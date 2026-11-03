"""Build 5 randomized setups: setups/s{k}/ws (agent-visible) and setups/s{k}/hidden (params + held-out)."""
import csv, json, os, shutil, numpy as np, truth2
rng = np.random.default_rng(2026)
README = open('README_template.md').read()
DUCTS = [42.0, 44.5, 47.0, 49.5, 52.0]; KS = [0.6, 2.5, 1.0, 3.5, 1.6]   # shuffled, not monotone together
def feasible(N, t, H, tb, duct):
    return (60 - N * t) / (N - 1) >= 0.5 and H + tb <= min(40, duct - 2)
for k in range(5):
    duct, K = DUCTS[k], KS[k]
    base = f'setups/s{k}'; os.makedirs(base + '/ws', exist_ok=True); os.makedirs(base + '/hidden', exist_ok=True)
    shutil.copy('sim_template.py', base + '/ws/sim.py')
    open(base + '/ws/README.md', 'w').write(README.replace('{DUCT}', f'{duct:g}'))
    train = []
    while len(train) < 12:
        N = int(rng.integers(6, 27)); t = float(np.round(rng.uniform(0.5, 1.5), 1)); tb = float(np.round(rng.uniform(4, 8), 1))
        H = float(np.round(rng.uniform(24, min(34, 40 - tb)), 0))
        if feasible(N, t, H, tb, duct): train.append((N, t, H, tb))
    with open(base + '/ws/bench_measurements.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['N_fins', 't_mm', 'H_mm', 'tb_mm', 'fan_speed', 'chip_temp_C', 'fan_flow_Ls'])
        for i, d in enumerate(train):
            fs = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.75, 0.75, 0.75, 1.25, 1.25, 1.25][i]
            r = truth2.bench(*d, fs, duct, K)
            w.writerow([*d, fs, round(r['chip_temp_C'] + rng.normal(0, 0.5), 2), round(r['fan_flow_Ls'] * (1 + rng.normal(0, 0.02)), 3)])
    held = []
    while len(held) < 30:
        N = int(rng.integers(3, 51)); t = float(np.round(rng.uniform(0.4, 1.5), 2)); tb = float(np.round(rng.uniform(3, 9), 1))
        H = float(np.round(rng.uniform(12, min(38, 40 - tb)), 1)); fs = float(np.round(rng.uniform(0.5, 1.5), 2))
        if not feasible(N, t, H, tb, duct): continue
        r = truth2.bench(N, t, H, tb, fs, duct, K)
        if r['chip_temp_C'] > 250: continue
        held.append(dict(N=N, t_mm=t, H_mm=H, tb_mm=tb, fan_speed=fs, chip_temp_C=r['chip_temp_C']))
    json.dump(dict(duct_mm=duct, K_bp=K, heldout=held), open(base + '/hidden/setup.json', 'w'), indent=1)
    print(k, duct, K, 'held-out range', round(min(h['chip_temp_C'] for h in held), 1), round(max(h['chip_temp_C'] for h in held), 1))
