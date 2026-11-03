# Heat sink bench: fix the simulator

`sim.py` is our thermal simulator for a plate-fin heat sink test bench. Its predictions don't match the
bench measurements in `bench_measurements.csv` well, and we need a simulator we can trust for design work.

## The bench
- Aluminum plate-fin heat sink, 60 x 60 mm footprint, straight fins running along the airflow.
- 20 x 20 mm chip, 60 W, centered under the base. Inlet air 35 C.
- The sink sits on the floor of a rectangular test duct, 60 mm wide and {DUCT} mm tall (inside dimensions),
  with the fan at the duct inlet. `fan_speed` scales the fan (1.0 = nominal).
- Measurements (at a few fan speeds): chip temperature (thermocouple, about +/-0.5 C) and total fan flow (flow meter, about +/-2%).

## Your task
Write `predict.py` in this folder exposing

    predict(N, t_mm, H_mm, tb_mm, fan_speed) -> chip temperature in C

(N = number of fins, t = fin thickness, H = fin height, tb = base thickness).
It will be graded on held-out bench measurements you cannot see, covering
N 3-50, t 0.4-1.5 mm, H 12-38 mm, tb 3-9 mm, H + tb <= 40 mm, fan_speed 0.5-1.5.
Many of those are well outside the measured range, so a model that only fits these 12 points will do badly.

Also write `NOTES.md` (a few paragraphs): what was wrong, what you changed, and how confident you are.
You may run Python (numpy and scipy are installed). Work only inside this folder; no internet.
