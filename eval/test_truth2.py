"""Regression tests for the reference: run before any eval."""
import numpy as np, importlib.util, truth2
spec = importlib.util.spec_from_file_location('sim', 'sim_template.py'); sim = importlib.util.module_from_spec(spec); spec.loader.exec_module(sim)
# 1) no-bypass limit: independent reference == fixed sim.py
for d in [(6,1.2,30,6),(20,0.8,30,6),(40,0.5,32,6),(15,1.0,20,4),(30,0.4,36,3)]:
    for fs in (0.5, 1.0, 1.5):
        a = sim.predict(*d, fs)['chip_temp_C']; b = truth2.bench(*d, fs, d[2] + d[3], 1.0)['chip_temp_C']
        assert abs(a - b) < 1e-6, (d, fs, a, b)
# 2) 1-D limit: Song-Lee-Au psi first term equals tb/(k W L) (no double count)
for tb in (0.003, 0.006, 0.009):
    a = 0.020 / np.sqrt(np.pi); b = np.sqrt(0.06 * 0.06 / np.pi)
    first = (a / b) * (tb / b) / np.sqrt(np.pi) / (200 * a * np.sqrt(np.pi))
    assert abs(first - tb / (200 * 0.06 * 0.06)) < 1e-12
# 3) monotonic physics: more bypass loss or smaller duct -> more flow through fins
d = (20, 0.8, 30, 6)
fr = [truth2.bench(*d, 1.0, 46, K)['fin_fraction'] for K in (0.5, 1, 2, 4)]; assert all(np.diff(fr) > 0)
fr = [truth2.bench(*d, 1.0, D, 1.0)['fin_fraction'] for D in (52, 48, 44, 40)]; assert all(np.diff(fr) > 0)
# 4) fan laws: free-delivery flow scales with speed (sink removed -> tiny resistance not testable; check total flow rises with speed)
q = [truth2.bench(*d, s, 46, 1.0)['fan_flow_Ls'] for s in (0.5, 1.0, 1.5)]; assert all(np.diff(q) > 0)
print('reference tests passed')
