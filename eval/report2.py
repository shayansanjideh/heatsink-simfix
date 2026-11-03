"""Round-2 table: per arm, mean over setups x attempts. Also writes report2.json with per-run, per-point errors."""
import json, pathlib, statistics as st, subprocess, sys
from grade2 import grade
HERE = pathlib.Path(__file__).parent
subprocess.run([sys.executable, str(HERE / 'baselines' / 'make_baselines.py')], check=True)
rows, dump = {}, {}
for b in sorted(p for p in (HERE / 'baselines').iterdir() if p.is_dir()):
    for k in range(5):
        s = grade(str(b / f's{k}'), k); rows.setdefault('[base] ' + b.name, []).append(s); dump[f'base/{b.name}/s{k}'] = s
for d in sorted((HERE / 'results').glob('*')):
    for f in sorted(d.glob('s*_a*.json')):
        r = json.loads(f.read_text()); s = r['score']; rows.setdefault(d.name, []).append(s); dump[f'{d.name}/{f.stem}'] = dict(s, minutes=r['minutes'], cheat=r['cheat_flag'])
print(f"{'arm':24s}{'n':>3s}{'rmse mean':>10s}{'rmse med':>9s}{'within2C':>9s}{'errors/timeouts':>16s}")
for arm, ss in rows.items():
    ok = [s for s in ss if 'rmse' in s]
    if not ok: print(f'{arm:24s}{len(ss):3d}  all failed'); continue
    print(f"{arm:24s}{len(ss):3d}{st.mean(s['rmse'] for s in ok):10.2f}{st.median(s['rmse'] for s in ok):9.2f}{st.mean(s['within2C'] for s in ok):9.2f}{len(ss)-len(ok):16d}")
    print('   per run rmse:', ' '.join(f"{s['rmse']:.1f}" if 'rmse' in s else 'ERR' for s in ss))
json.dump(dump, open(HERE / 'report2.json', 'w'))
