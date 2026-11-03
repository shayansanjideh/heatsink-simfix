"""Independent reference for the v2 bench (written separately from sim.py; no imports from it).
Physics: plate-fin channels + a parallel bypass gap above the fins inside a duct of height duct_mm,
sharing one pressure drop, on a quadratic-free linear fan curve scaled by fan laws.
Base conduction + spreading via Song-Lee-Au (psi includes the 1-D term; nothing added twice)."""
import numpy as np
from scipy.optimize import brentq

AIR = dict(rho=1.13, mu=1.9e-5, k=0.027, cp=1007.0)
SINK = dict(W=0.060, L=0.060, src=0.020, Q=60.0, T_in=35.0, R_jc=0.35, k_al=200.0)
FAN = dict(dp0=80.0, v0=0.012)

def _poiseuille(aspect):
    e = np.minimum(aspect, 1.0 / aspect)
    c = [1, -1.3553, 1.9467, -1.7012, 0.9564, -0.2537]
    return 24.0 * sum(ci * e**i for i, ci in enumerate(c))

def _dp_duct(q, width, height, k_minor):
    """Pressure drop for flow q (m3/s) through `count` identical rectangular ducts handled by caller."""
    if q <= 0: return 0.0
    A = width * height; Dh = 2 * A / (width + height); u = q / A
    Re = AIR['rho'] * u * Dh / AIR['mu']
    Lp = SINK['L'] / (Dh * Re)
    f = np.hypot(3.44 / np.sqrt(Lp), _poiseuille(height / width)) / Re
    return (4 * f * SINK['L'] / Dh + k_minor) * 0.5 * AIR['rho'] * u * u

def _paths(N, t, H, tb, duct, K_bp):
    W = SINK['W']; gap = (W - N * t) / (N - 1); sig = 1 - N * t / W
    kfin = 0.42 * (1 - sig**2) + (1 - sig**2)**2
    fins = lambda q: _dp_duct(q / (N - 1), gap, H, kfin)          # per-channel flow
    C = duct - tb - H
    byp = (lambda q: _dp_duct(q, W, C, K_bp)) if C > 1e-5 else None
    return gap, fins, byp

def _flow_at(dp_fn, dp):
    return 0.0 if dp <= 0 else brentq(lambda q: dp_fn(q) - dp, 0.0, 2.0)

def _thermal(N, t, H, tb, q_fins):
    W, L = SINK['W'], SINK['L']; gap = (W - N * t) / (N - 1)
    Pr = AIR['mu'] * AIR['cp'] / AIR['k']; nu = AIR['mu'] / AIR['rho']
    u = q_fins / ((N - 1) * gap * H); ReS = u * gap / nu * gap / L
    Nu = ((ReS * Pr / 2)**-3 + (0.664 * np.sqrt(ReS) * Pr**(1/3) * np.sqrt(1 + 3.65 / np.sqrt(ReS)))**-3)**(-1/3)
    h = Nu * AIR['k'] / gap
    m = np.sqrt(2 * h / (SINK['k_al'] * t)); eta = np.tanh(m * H) / (m * H)
    R_fins = 1 / (h * (2 * N * eta * H * L + (N - 1) * gap * L))
    R_airrise = 1 / (2 * AIR['rho'] * AIR['cp'] * q_fins)
    a = SINK['src'] / np.sqrt(np.pi); b = np.sqrt(W * L / np.pi); eps, tau = a / b, tb / b
    Bi = b / (SINK['k_al'] * R_fins * W * L); lam = np.pi + 1 / (np.sqrt(np.pi) * eps)
    phi = (np.tanh(lam * tau) + lam / Bi) / (1 + lam / Bi * np.tanh(lam * tau))
    psi = eps * tau / np.sqrt(np.pi) + (1 - eps) * phi / np.sqrt(np.pi)   # includes 1-D conduction
    R_plate = psi / (SINK['k_al'] * a * np.sqrt(np.pi))
    return SINK['T_in'] + SINK['Q'] * (SINK['R_jc'] + R_plate + R_fins + R_airrise)

def bench(N, t_mm, H_mm, tb_mm, fan_speed, duct_mm, K_bp):
    N = int(round(N)); t, H, tb, duct = t_mm / 1e3, H_mm / 1e3, tb_mm / 1e3, duct_mm / 1e3
    gap, fins, byp = _paths(N, t, H, tb, duct, K_bp)
    dp0, v0 = FAN['dp0'] * fan_speed**2, FAN['v0'] * fan_speed
    total = lambda dp: _flow_at(fins, dp) + (_flow_at(byp, dp) if byp else 0.0)
    dp = brentq(lambda p: dp0 * (1 - total(p) / v0) - p, 1e-7, dp0 * (1 - 1e-9))
    qf = _flow_at(fins, dp)
    return dict(chip_temp_C=float(_thermal(N, t, H, tb, qf)), fan_flow_Ls=total(dp) * 1e3, fin_fraction=qf / total(dp))
