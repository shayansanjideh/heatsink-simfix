"""Thermal simulator for the plate-fin heat sink test bench.

predict(N, t_mm, H_mm, tb_mm, fan_speed=1.0) -> dict with chip temperature (C) and fan flow (L/s).
Correlations: Teertstra et al. channel Nusselt number, Muzychka-Yovanovich apparent friction with
entrance/exit losses, fin efficiency, Song-Lee-Au spreading resistance.
"""
import math
from scipy.optimize import brentq

W, L = 0.060, 0.060            # heat sink footprint (m); L is along the flow
SRC = 0.020                    # square chip side (m)
Q = 60.0                       # chip power (W)
T_IN = 35.0                    # inlet air temperature (C)
R_JC_TIM = 0.35                # junction-to-case + thermal paste (K/W)
K_AL = 200.0                   # aluminum conductivity (W/m K)
RHO, MU, K_AIR, CP = 1.13, 1.9e-5, 0.027, 1007.0
PR = MU * CP / K_AIR
NU = MU / RHO
FAN_DP0, FAN_V0 = 80.0, 0.012  # nominal fan: shutoff pressure (Pa), free-delivery flow (m3/s)

def fRe_rect(aspect):
    a = min(aspect, 1 / aspect)
    return 24 * (1 - 1.3553 * a + 1.9467 * a**2 - 1.7012 * a**3 + 0.9564 * a**4 - 0.2537 * a**5)

def channel_dp(Vdot, area, Dh, aspect, k_loss):
    """Pressure drop (Pa) for flow Vdot (m3/s) through a rectangular passage of length L."""
    V = Vdot / area
    Re = V * Dh / NU
    Lstar = L / (Dh * Re)
    f_app = math.sqrt((3.44 / math.sqrt(Lstar))**2 + fRe_rect(aspect)**2) / Re
    return (f_app * 4 * L / Dh + k_loss) * 0.5 * RHO * V**2

def chip_temp(N, t, H, tb, Vdot):
    """Chip temperature (C) when Vdot (m3/s) of air flows through the fin channels."""
    s = (W - N * t) / (N - 1)
    V = Vdot / ((N - 1) * s * H)
    Re_s = V * s / NU * s / L
    Nu = ((Re_s * PR / 2)**-3 + (0.664 * math.sqrt(Re_s) * PR**(1/3) * math.sqrt(1 + 3.65 / math.sqrt(Re_s)))**-3)**(-1/3)
    h = Nu * K_AIR / s
    m = math.sqrt(2 * h / (K_AL * t))
    eta = math.tanh(m * H) / (m * H)
    R_conv = 1 / (h * (N * eta * 2 * H * L + (N - 1) * s * L))
    R_air = 1 / (2 * RHO * Vdot * CP)
    a, b = math.sqrt(SRC**2 / math.pi), math.sqrt(W * L / math.pi)
    eps, tau = a / b, tb / b
    Bi = (1 / (R_conv * W * L)) * b / K_AL
    lc = math.pi + 1 / (math.sqrt(math.pi) * eps)
    phi = (math.tanh(lc * tau) + lc / Bi) / (1 + lc / Bi * math.tanh(lc * tau))
    R_sp = (eps * tau / math.sqrt(math.pi) + (1 - eps) * phi / math.sqrt(math.pi)) / (K_AL * a * math.sqrt(math.pi))
    return T_IN + Q * (R_JC_TIM + R_sp + R_conv + R_air)   

def predict(N, t_mm, H_mm, tb_mm, fan_speed=1.0):
    N = int(round(N)); t, H, tb = t_mm / 1000, H_mm / 1000, tb_mm / 1000
    s = (W - N * t) / (N - 1)
    sigma = 1 - N * t / W
    k_loss = 0.42 * (1 - sigma**2) + (1 - sigma**2)**2
    sink_dp = lambda v: channel_dp(v, (N - 1) * s * H, 2 * s * H / (s + H), s / H, k_loss)
    dp0, v0 = FAN_DP0 * fan_speed**2, FAN_V0 * fan_speed          # fan laws
    fan = lambda v: dp0 * (1 - v / v0)
    Vdot = brentq(lambda v: fan(v) - sink_dp(v), 1e-9, v0)
    return {"chip_temp_C": chip_temp(N, t, H, tb, Vdot), "fan_flow_Ls": Vdot * 1000}
