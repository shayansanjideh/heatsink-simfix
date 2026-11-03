# Heat sink simulator-fix eval

Can a frontier model fix a broken physics simulator from a handful of measurements, and only the part that's broken?

Each model gets a plate-fin heat sink simulator with one missing mechanism (air leaking over the fins through the gap above them), a README, and 12 bench measurements of chip temperature and fan airflow. It has to write `predict.py`, which is scored on 30 held-out designs per setup, including fin counts and fan speeds outside the training data.

**Live:** [results](https://shayansanjideh.github.io/heatsink-simfix/) · [Heat Sink Playground](https://shayansanjideh.github.io/heatsink-simfix/playground/)

## Round 2 results

5 setups with different leak strengths × 2 attempts per model, the same setups for every model. The numbers are mean RMSE in °C on the held-out designs (lower is better).

| Model | Mean RMSE | Median |
|---|---|---|
| GPT-6.1 Sol | 0.75 | 0.77 |
| Sonnet | 1.48 | 1.69 |
| Opus | 5.14 | 3.92 |
| GPT-6.1 Terra | 5.77 | 2.15 |
| Haiku | 8.59 | 2.35 |
| GPT-6 Luna | 23.70 | 20.89 |
| *Baseline: fit the leak coefficient only* | 0.92 | 0.79 |
| *Baseline: textbook default leak (K = 1)* | 11.12 | 12.43 |
| *Baseline: curve fit on the gap* | 11.49 | 13.91 |
| *Baseline: unfixed simulator* | 25.25 | 19.52 |

Almost every model found the leak. The difference was what they did next. The best runs fit one leak coefficient from the measured airflow and left the rest alone. The worst runs also refit the fan curve or stacked correction factors onto physics that was already correct. Those extra knobs matched the 12 training points and then broke on dense fins (N > 30) the models never saw.

Full table, including errors by fan speed and fin count: [`results/report2.txt`](results/report2.txt). Per-run predictions: [`results/preds.json`](results/preds.json).

## Caveats

- **The reference is textbook correlations, not CFD:** Teertstra channel Nusselt number, Muzychka–Yovanovich friction, a linear fan curve, fin efficiency and Song–Lee–Au spreading resistance, plus a parallel bypass path at equal pressure drop.
- **Small sample:** 10 runs per model. Sol > Sonnet > the rest is solid. Opus, Terra and Haiku can't be separated.
- **Round leak values:** the hidden leak coefficients are round numbers (0.6, 2.5, 1.0, 3.5, 1.6), and one setup uses the textbook default of 1.0. Two of Haiku's perfect scores come from this. A round 3 should draw them from a continuous range.
- **Answers are public:** the held-out answers are in `eval/setups/*/hidden/`. Any new model run on these exact setups could have seen them. To run fresh models, change the seed in `make_v2.py` and regenerate.
- **No cheating found:** every transcript was scanned, and no run read the hidden files.

## Layout

- `eval/`
  - `sim_template.py`: the flawed simulator the agent receives.
  - `truth2.py`: the independent reference. Run `test_truth2.py` to check it.
  - `make_v2.py`: builds the 5 setups.
  - `run_agent2.py`: runs Claude Code (`claude -p`) or Codex (`codex exec`) in a fresh temp folder, then grades the result.
  - `grade2.py`, `report2.py`: grading and the results table.
  - `baselines/`: the four baselines.
- `model/`: the closed-form heat sink model in Python (`model.py`) and JS (`physics.js`, used by the playground).
- `docs/`: the GitHub Pages site (results page and playground).

```
cd eval
python3 test_truth2.py        # reference self-checks
python3 make_v2.py            # regenerate setups (change the seed first for a fresh eval)
python3 run_agent2.py claude --model sonnet --runs 2
python3 report2.py
```

Requires Python 3 with numpy and scipy. Running agents also requires the `claude` or `codex` CLI.
