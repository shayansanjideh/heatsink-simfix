"""Grade a folder containing predict.py against setup k's hidden held-out points."""
import json, math, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CODE = ("import json,sys\nsys.path.insert(0,'.')\nfrom predict import predict\nout=[]\n"
        "for h in json.load(sys.stdin):\n  try:\n    v=predict(h['N'],h['t_mm'],h['H_mm'],h['tb_mm'],h['fan_speed'])\n"
        "    v=v['chip_temp_C'] if isinstance(v,dict) else float(v)\n  except Exception: v=None\n  out.append(v)\nprint(json.dumps(out))")
def grade(folder, k):
    held = json.load(open(os.path.join(HERE, 'setups', f's{k}', 'hidden', 'setup.json')))['heldout']
    r = subprocess.run([sys.executable, '-c', CODE], input=json.dumps(held), capture_output=True, text=True, cwd=folder, timeout=900,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    if r.returncode: return dict(error=r.stderr[-600:])
    preds = json.loads(r.stdout.strip().splitlines()[-1])
    errs = [abs(p - h['chip_temp_C']) if isinstance(p, (int, float)) and math.isfinite(p) else 50.0 for p, h in zip(preds, held)]
    return dict(rmse=round(math.sqrt(sum(e*e for e in errs) / len(errs)), 2), max=round(max(errs), 2),
                within2C=round(sum(e <= 2 for e in errs) / len(errs), 3), failed=sum(not isinstance(p, (int, float)) for p in preds),
                errors=[round(e, 3) for e in errs], preds=preds)
if __name__ == '__main__':
    s = grade(sys.argv[1], int(sys.argv[2])); s.pop('errors'); s.pop('preds'); print(json.dumps(s))
