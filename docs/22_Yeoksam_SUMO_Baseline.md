# Yeoksam 3x3 SUMO Baseline

This is the simplified Module 1 baseline that does **not require machine learning**.

## Goal
- Treat Yeoksam-dong as a 3x3 micro area.
- Use 5-minute synthetic taxi demand.
- Compare `before` (market-cruise patrol allocation) vs `after` (kakao-like heuristic reallocation).
- Export both cases into SUMO route/config files.

## Zone layout
- `A1`: Yeoksam NW Office
- `A2`: Teheran West
- `A3`: Teheran East
- `B1`: Yeoksam West
- `B2`: Gangnam Station Core
- `B3`: Yeoksam East Commercial
- `C1`: Yeoksam SW
- `C2`: Gangnam-daero South
- `C3`: Yeoksam SE

The intended hotspot is `B2`, with secondary demand in `B3` and `C2`.

## Run
```bash
cd /Users/kenny31/Documents/Capstone
bash scripts/run_yeoksam_sumo_pipeline.sh
```

## Main outputs
- synthetic data: `/Users/kenny31/Documents/Capstone/data/yeoksam_synthetic_5min.csv`
- dispatch result: `/Users/kenny31/Documents/Capstone/outputs/yeoksam_sumo/dispatch_recommendations.csv`
- before/after comparison: `/Users/kenny31/Documents/Capstone/outputs/yeoksam_sumo/dispatch_comparison.csv`
- evaluation summary: `/Users/kenny31/Documents/Capstone/outputs/yeoksam_sumo/dispatch_evaluation.json`
- visual summary board: `/Users/kenny31/Documents/Capstone/outputs/yeoksam_sumo/yeoksam_sumo_board.png`
- motion playback: `/Users/kenny31/Documents/Capstone/outputs/yeoksam_sumo/yeoksam_sumo_motion.gif`
- before SUMO route: `/Users/kenny31/Documents/Capstone/module1_sumo/yeoksam_before.rou.xml`
- after SUMO route: `/Users/kenny31/Documents/Capstone/module1_sumo/yeoksam_after.rou.xml`
- before SUMO config: `/Users/kenny31/Documents/Capstone/module1_sumo/yeoksam_before.sumocfg`
- after SUMO config: `/Users/kenny31/Documents/Capstone/module1_sumo/yeoksam_after.sumocfg`

## Why this exists
The assignment requires a Digital Twin environment, but the team does not need to start with a full city-scale simulator. This baseline gives us:
- a small, understandable Yeoksam scope
- 5-minute demand structure that matches the assignment better than the hourly Seoul API
- immediate before/after SUMO inputs

It is the right first milestone before we add ML models.
