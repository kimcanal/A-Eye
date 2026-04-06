# SUMO Traffic Simulation Guide

This repository now uses **SUMO as the active Digital Twin path**.

The current focus is a **Yeoksam 3x3 baseline**:
- 5-minute synthetic demand
- rule-based dispatch
- `before` vs `after` taxi reallocation
- SUMO route/config generation

## Main Entry Point

```bash
bash scripts/run_yeoksam_sumo_pipeline.sh
```

This generates:
- `module1_sumo/yeoksam_before.rou.xml`
- `module1_sumo/yeoksam_after.rou.xml`
- `module1_sumo/yeoksam_before.sumocfg`
- `module1_sumo/yeoksam_after.sumocfg`
- `outputs/yeoksam_sumo/yeoksam_sumo_board.png`
- `outputs/yeoksam_sumo/yeoksam_sumo_motion.gif`

## Active SUMO Files

The active SUMO files live in `module1_sumo/`:

- `generated_grid3x3.net.xml`
- `yeoksam_before.rou.xml`
- `yeoksam_after.rou.xml`
- `yeoksam_before.sumocfg`
- `yeoksam_after.sumocfg`

Older public-data SUMO artifacts were moved into `legacy/`.

## Running SUMO

CLI validation:

```bash
sumo -c module1_sumo/yeoksam_before.sumocfg
sumo -c module1_sumo/yeoksam_after.sumocfg
```

Local GUI helper:

```bash
bash scripts/run_local_sumo_gui.sh module1_sumo/yeoksam_before.sumocfg
bash scripts/run_local_sumo_gui.sh module1_sumo/yeoksam_after.sumocfg
```

Note:
- macOS + XQuartz may still block `sumo-gui` because of GLX/OpenGL issues.
- When GUI does not open, use the generated board/GIF outputs instead.

## Current Limitation

- The network is a simplified Yeoksam 3x3 abstraction, not the full real road graph.
- The dispatch path is currently rule-based, not ML-driven.
- The GUI path may be unstable on macOS, even when CLI execution is valid.
