// Closed-form plate-fin heat sink model (same as model.py). Textbook correlations, not CFD.
const HS = (() => {
  const W = 0.060, L = 0.060, SRC = 0.020, Q = 60.0, T_AMB = 35.0, R_JC_TIM = 0.35, T_LIMIT = 85.0;
  const H_MAX_TOTAL = 0.040, K_AL = 200.0, RHO_AL = 2700.0, RHO = 1.13, CP = 1007.0, MASS_CAP = 150;
  const ENVS = {
    normal:  { label: 'Air, standard fan', mu: 1.9e-5, k: 0.027, dp0: 80.0,  v0: 0.012 },
    thick:   { label: 'Thick fluid (10× viscosity)', mu: 1.9e-4, k: 0.027, dp0: 80.0, v0: 0.012 },
    weakfan: { label: 'Weak high-flow fan', mu: 1.9e-5, k: 0.027, dp0: 8.0, v0: 0.025 },
    blower:  { label: 'High-pressure blower', mu: 1.9e-5, k: 0.027, dp0: 600.0, v0: 0.004 },
  };
  function fRe(lam) {
    lam = Math.min(lam, 1 / lam);
    return 24 * (1 - 1.3553 * lam + 1.9467 * lam ** 2 - 1.7012 * lam ** 3 + 0.9564 * lam ** 4 - 0.2537 * lam ** 5);
  }
  function system(N, t, H, env) {
    const E = ENVS[env], nu = E.mu / RHO;
    const s = (W - N * t) / (N - 1), Ach = (N - 1) * s * H, Dh = 2 * s * H / (s + H);
    const sigma = 1 - N * t / W, Kc = 0.42 * (1 - sigma ** 2), Ke = (1 - sigma ** 2) ** 2, lam = s / H;
    const dp = Vd => {
      const V = Vd / Ach, Re = V * Dh / nu, Ls = L / (Dh * Re);
      const fapp = Math.sqrt((3.44 / Math.sqrt(Ls)) ** 2 + fRe(lam) ** 2) / Re;
      return (fapp * 4 * L / Dh + Kc + Ke) * 0.5 * RHO * V ** 2;
    };
    const fan = Vd => E.dp0 * (1 - Vd / E.v0);
    return { s, Ach, dp, fan };
  }
  function evaluate(N, t, H, tb, env = 'normal') {
    N = Math.round(N);
    const E = ENVS[env], mu = E.mu, nu = mu / RHO, k = E.k, PR = mu * CP / k;
    const s = N > 1 ? (W - N * t) / (N - 1) : W;
    const out = { N, t, H, tb, s, env };
    if (N < 2 || s <= 5e-5 || H + tb > H_MAX_TOTAL + 1e-12) return Object.assign(out, { Tj: Infinity, ok: false });
    const sys = system(N, t, H, env);
    let lo = 1e-9, hi = E.v0;                       // bisection for fan = system
    for (let i = 0; i < 80; i++) { const m = 0.5 * (lo + hi); (sys.fan(m) - sys.dp(m) > 0) ? lo = m : hi = m; }
    const Vdot = 0.5 * (lo + hi), dP = sys.fan(Vdot), V = Vdot / sys.Ach;
    const Res = V * s / nu * s / L;
    const Nu = ((Res * PR / 2) ** -3 + (0.664 * Math.sqrt(Res) * PR ** (1 / 3) * Math.sqrt(1 + 3.65 / Math.sqrt(Res))) ** -3) ** (-1 / 3);
    const h = Nu * k / s, m = Math.sqrt(2 * h / (K_AL * t)), eta = Math.tanh(m * H) / (m * H);
    const R_conv = 1 / (h * (N * eta * 2 * H * L + (N - 1) * s * L));
    const R_air = 1 / (2 * RHO * Vdot * CP), R_base = tb / (K_AL * W * L);
    const a = Math.sqrt(SRC ** 2 / Math.PI), b = Math.sqrt(W * L / Math.PI), eps = a / b, tau = tb / b;
    const Bi = (1 / (R_conv * W * L)) * b / K_AL, lc = Math.PI + 1 / (Math.sqrt(Math.PI) * eps);
    const phi = (Math.tanh(lc * tau) + lc / Bi) / (1 + lc / Bi * Math.tanh(lc * tau));
    // Song-Lee-Au total already includes 1-D base conduction (tb/kWL); split it out so the bars don't count it twice
    const R_sp = (eps * tau / Math.sqrt(Math.PI) + (1 - eps) * phi / Math.sqrt(Math.PI)) / (K_AL * a * Math.sqrt(Math.PI)) - R_base;
    const R_tot = R_JC_TIM + R_sp + R_base + R_conv + R_air, Tj = T_AMB + Q * R_tot;
    const mass = RHO_AL * (W * L * tb + N * t * H * L) * 1000;
    const T_air = T_AMB + Q * R_air, T_finbase = T_air + Q * R_conv, T_plate = T_finbase + Q * R_base;
    return Object.assign(out, { Tj, ok: true, mass, dP, Vdot, V, h, eta, m, R_conv, R_sp, R_air, R_base, R_tot,
      T_air, T_finbase, T_plate, T_spot: T_plate + Q * R_sp });
  }
  return { W, L, SRC, Q, T_AMB, T_LIMIT, H_MAX_TOTAL, MASS_CAP, ENVS, evaluate, system };
})();
if (typeof module !== 'undefined') module.exports = HS;
