# Heat sink simulator-fix eval

Can a frontier model fix a broken physics simulator from a handful of measurements, and only the part that's broken?

Each model gets a plate-fin heat sink simulator with one missing mechanism (air leaking over the fins through the gap above them), a README, and 12 simulated bench measurements of chip temperature and fan airflow. There is no physical rig: the measurements come from the reference model (`eval/truth2.py`) plus noise. It has to write `predict.py`, which is scored on 30 held-out designs per setup, including fin counts and fan speeds outside the training data.

**Live:** [results](https://shayansanjideh.github.io/heatsink-simfix/) · [Heat Sink Playground](https://shayansanjideh.github.io/heatsink-simfix/playground/)

## Round 2 results

5 setups with different leak strengths × 2 attempts per model, the same setups for every model. The numbers are mean RMSE in °C on the held-out designs (lower is better).

Models: Claude Sonnet 5.5, Opus 5.5 and Haiku 5.5 through Claude Code (`claude -p`, which ran at medium effort), and GPT-6.1 Sol, GPT-6.1 Terra and GPT-6 Luna through Codex (`codex exec`, effort setting not recorded). The two CLIs have different built-in tools, so this compares model plus harness, not models alone.

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

Almost every model found the leak. A code check finds a real bypass path in 10 of 10 runs for every model except Luna, which has one in 4 of 10. What separated them was leaving the rest alone. We compared each run's predictions with the true physics, changing only the leak value. Sol and Sonnet matched it to within 0.25 °C in 19 of 20 runs (also 19 of 20 at a looser 1 °C, against 8 of 20 for Opus and Terra). Haiku matched in 5 of 10, Opus and Luna in 2 of 10 each, and Terra in 0 of 10. The other runs changed parts that weren't broken, such as loss formulas, the fan curve in 3 Opus runs, or stacked correction factors. Some of those edits still matched the 12 training points; Opus's and Terra's mostly did, while Haiku's and Luna's worst runs already missed their own training data. Errors grow on dense fins (N > 30) for every model, including correct ones, because a small leak error gets amplified there.

Sol's worst run scored 1.7 °C and Sonnet's 3.0. Every other model had at least 3 runs above 5 °C.

Full table, including errors by fan speed and fin count: [`results/report2.txt`](results/report2.txt). Per-run predictions: [`results/preds.json`](results/preds.json).

## Caveats

- **Leaving the rest alone was right by design:** the reference is written independently but uses the same correlations as the simulator, plus the leak. Everything except the leak was correct by construction, and the models weren't told that. On real hardware, refitting a fan curve to measured airflow can be sensible engineering, so this tests one narrow skill, not engineering judgment in general.
- **The reference is textbook correlations, not CFD:** Teertstra channel Nusselt number, Muzychka–Yovanovich friction, a linear fan curve, fin efficiency and Song–Lee–Au spreading resistance, plus a parallel bypass path at equal pressure drop.
- **Small sample:** 10 runs per model. Sol and Sonnet lead on means and on worst-case runs, but medians don't clearly separate them from the rest. Opus, Terra and Haiku can't be separated.
- **Crashes:** one Terra run (s4_a1) and one Luna run (s3_a0) crashed on 13 and 12 of their 30 designs, and each crash is scored as a 50 °C miss. Without crashed points, Terra's mean would be 2.65 instead of 5.77, so that one run drives most of its score. Excluding crashed points also moves Luna from 2 to 3 of 10 runs that match the true physics apart from the leak value; Terra stays at 0.
- **Round leak values:** the hidden leak coefficients are round numbers (0.6, 2.5, 1.0, 3.5, 1.6), and one setup uses the textbook default of 1.0. All six perfect 0.00 scores come from this: five are on the K = 1.0 setup, where the default is exactly right, and one is a coarse search that landed on 3.5. A round 3 should draw them from a continuous range.
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
