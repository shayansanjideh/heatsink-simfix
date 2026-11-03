"""Plate-fin heat sink, ducted fan, closed-form model (~0.1 ms/eval).
Correlations: Teertstra et al. (1999) channel Nu; Muzychka/Yovanovich apparent friction
(as used by Culham & Muzychka 2001); Kays-London style Kc/Ke; Song-Lee-Au spreading resistance.
Textbook correlations, not CFD."""
import math
from scipy.optimize import brentq

# fixed problem
W, L = 0.060, 0.060          # footprint (m), L along flow
SRC = 0.020                  # square heat source side (m)
Q = 60.0                     # W
T_AMB = 35.0                 # C
R_JC_TIM = 0.35              # K/W junction-to-case + TIM
T_LIMIT = 85.0
H_MAX_TOTAL = 0.040          # fin height + base <= 40 mm
K_AL, RHO_AL = 200.0, 2700.0
RHO, MU, K_AIR, CP = 1.13, 1.9e-5, 0.027, 1007.0
NU = MU / RHO
FAN_DP0, FAN_V0 = 80.0, 0.012  # linear fan curve: shutoff 80 Pa, free flow 12 L/s (~25 CFM)

def fRe_rect(lam):
    lam = min(lam, 1/lam)
    return 24*(1 - 1.3553*lam + 1.9467*lam**2 - 1.7012*lam**3 + 0.9564*lam**4 - 0.2537*lam**5)

ENVS = {
  'normal':  dict(mu=1.9e-5, k_air=0.027, dp0=80.0,  v0=0.012),
  'thick':   dict(mu=1.9e-4, k_air=0.027, dp0=80.0,  v0=0.012),   # 10x viscosity
  'weakfan': dict(mu=1.9e-5, k_air=0.027, dp0=8.0,   v0=0.025),   # high-flow, low-pressure fan
  'blower':  dict(mu=1.9e-5, k_air=0.027, dp0=600.0, v0=0.004),   # high-pressure, low-flow blower
}

def evaluate(N, t, H, tb, env='normal'):
    E = ENVS[env]; MU = E['mu']; NU = MU/RHO; K_AIR = E['k_air']; FAN_DP0 = E['dp0']; FAN_V0 = E['v0']; PR = MU*CP/K_AIR
    """N fins, t fin thickness, H fin height, tb base thickness (m). Returns dict."""
    N = int(round(N))
    s = (W - N*t) / (N - 1) if N > 1 else W
    out = dict(N=N, t=t, H=H, tb=tb, s=s)
    if N < 2 or s <= 5e-5 or H + tb > H_MAX_TOTAL + 1e-12:
        out.update(Tj=float('inf'), feasible=False, reason='geometry'); return out
    Ach = (N-1)*s*H
    Dh = 2*s*H/(s+H)
    sigma = 1 - N*t/W
    Kc, Ke = 0.42*(1-sigma**2), (1-sigma**2)**2
    lam = s/H
    def dp_sys(Vdot):
        V = Vdot/Ach
        Re = V*Dh/NU
        Ls = L/(Dh*Re)
        fapp = math.sqrt((3.44/math.sqrt(Ls))**2 + fRe_rect(lam)**2)/Re
        return (fapp*4*L/Dh + Kc + Ke)*0.5*RHO*V**2
    fan = lambda Vd: FAN_DP0*(1 - Vd/FAN_V0)
    Vdot = brentq(lambda Vd: fan(Vd) - dp_sys(Vd), 1e-9, FAN_V0)
    dP = fan(Vdot)
    V = Vdot/Ach
    Res = V*s/NU * s/L
    Nu = ((Res*PR/2)**-3 + (0.664*math.sqrt(Res)*PR**(1/3)*math.sqrt(1+3.65/math.sqrt(Res)))**-3)**(-1/3)
    h = Nu*K_AIR/s
    m = math.sqrt(2*h/(K_AL*t))
    eta = math.tanh(m*H)/(m*H)
    A_eff = N*eta*2*H*L + (N-1)*s*L
    R_conv = 1/(h*A_eff)
    R_air = 1/(2*RHO*Vdot*CP)          # mean air temperature rise
    R_base = tb/(K_AL*W*L)
    # Song-Lee-Au spreading (circle-equivalent)
    a, b = math.sqrt(SRC**2/math.pi), math.sqrt(W*L/math.pi)
    eps, tau = a/b, tb/b
    Bi = (1/(R_conv*W*L))*b/K_AL
    lc = math.pi + 1/(math.sqrt(math.pi)*eps)
    phi = (math.tanh(lc*tau) + lc/Bi)/(1 + lc/Bi*math.tanh(lc*tau))
    R_sp = (eps*tau/math.sqrt(math.pi) + (1-eps)*phi/math.sqrt(math.pi))/(K_AL*a*math.sqrt(math.pi))
    R_tot = R_JC_TIM + R_sp + R_conv + R_air   # R_sp already includes 1-D base conduction (tb/kWL)
    Tj = T_AMB + Q*R_tot
    mass = RHO_AL*(W*L*tb + N*t*H*L)*1000
    out.update(Tj=Tj, feasible=Tj <= T_LIMIT, mass_g=mass, dP=dP, Vdot_Ls=Vdot*1000,
               V=V, h=h, eta=eta, R_conv=R_conv, R_sp=R_sp, R_air=R_air, R_tot=R_tot, m=m)
    return out
