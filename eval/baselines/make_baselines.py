"""Write baseline predict.py files into baselines/<name>/s{k}/ for each setup (each fits only on that setup's bench CSV)."""
import os, sys, textwrap
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
COMMON = textwrap.dedent('''
import csv, os, sys, numpy as np
from scipy.optimize import least_squares
WS = {ws!r}; ROOT = {root!r}
sys.path[:0] = [WS, ROOT]
import sim, truth2
DUCT = {duct}
rows = list(csv.DictReader(open(os.path.join(WS, 'bench_measurements.csv'))))
D = [(int(r['N_fins']), float(r['t_mm']), float(r['H_mm']), float(r['tb_mm']), float(r['fan_speed'])) for r in rows]
T = np.array([float(r['chip_temp_C']) for r in rows]); F = np.array([float(r['fan_flow_Ls']) for r in rows])
''')
BODIES = {
 'as_given': "def predict(N,t,H,tb,f=1.0): return sim.predict(N,t,H,tb,f)['chip_temp_C']\n",
 'curvefit_gap': textwrap.dedent('''
    def g(N,t,H,tb,f,p):
        fr = min(1.0, max(0.05, p[0] + p[1]*(DUCT - tb - H)))
        q = sim.predict(N,t,H,tb,f)['fan_flow_Ls']/1000
        return sim.chip_temp(int(N), t/1000, H/1000, tb/1000, fr*q)
    P = least_squares(lambda p: [g(*d,p)-y for d,y in zip(D,T)], [0.9,-0.02]).x
    def predict(N,t,H,tb,f=1.0): return g(N,t,H,tb,f,P)
 '''),
 'physics_K1': "def predict(N,t,H,tb,f=1.0): return truth2.bench(N,t,H,tb,f,DUCT,1.0)['chip_temp_C']\n",
 'physics_fitK': textwrap.dedent('''
    res = least_squares(lambda p: [truth2.bench(*d, DUCT, float(np.exp(p[0])))['fan_flow_Ls']/fl - 1 for d, fl in zip(D, F)], [0.0])
    K = float(np.exp(res.x[0]))
    def predict(N,t,H,tb,f=1.0): return truth2.bench(N,t,H,tb,f,DUCT,K)['chip_temp_C']
 '''),
}
import json
for k in range(5):
    duct = json.load(open(os.path.join(ROOT, 'setups', f's{k}', 'hidden', 'setup.json')))['duct_mm']
    for name, body in BODIES.items():
        d = os.path.join(HERE, name, f's{k}'); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'predict.py'), 'w').write(COMMON.format(ws=os.path.join(ROOT, 'setups', f's{k}', 'ws'), root=ROOT, duct=duct) + body)
