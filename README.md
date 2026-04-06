# A-Eye
# [카카오모빌리티 - AI 기반 택시 수요 예측 및 동적 배차 시스템 (캡스톤디자인)](https://nimble-ceder-40b.notion.site/28_DT_-32317efd202c8158b35ac245c2b4dc73)

Kakao Mobility capstone repository for a **Yeoksam-dong 3x3 taxi dispatch Digital Twin**.

This branch keeps **one active path only**:
- `Yeoksam 3x3 SUMO baseline`
- `5-minute synthetic demand`
- `heuristic dispatch`
- `before / after comparison`

Everything else has been moved into `legacy/` or `docs/archive/`.

## Start Here

Run the current baseline:

```bash
bash scripts/run_yeoksam_sumo_pipeline.sh
```

Main outputs:
- `outputs/yeoksam_sumo/dispatch_recommendations.csv`
- `outputs/yeoksam_sumo/dispatch_comparison.csv`
- `outputs/yeoksam_sumo/dispatch_evaluation.json`
- `outputs/yeoksam_sumo/yeoksam_sumo_board.png`
- `outputs/yeoksam_sumo/yeoksam_sumo_motion.gif`
- `module1_sumo/yeoksam_before.sumocfg`
- `module1_sumo/yeoksam_after.sumocfg`

## Active Folders

- `configs/`
  - active config only
- `src/`
  - active pipeline code
- `scripts/`
  - active entry script only
- `module1_sumo/`
  - active SUMO files only
- `docs/`
  - active docs only
- `data/`
  - active generated input data
- `outputs/`
  - active generated outputs

## Archived
- `legacy/`
- `docs/archive/`

## What To Read First

- [docs/README.md](docs/README.md)
- [docs/01_Project_Status.md](docs/01_Project_Status.md)
- [docs/03_SUMO_Simulation.md](docs/03_SUMO_Simulation.md)
- [docs/22_Yeoksam_SUMO_Baseline.md](docs/22_Yeoksam_SUMO_Baseline.md)

## Cleanup

If generated files get noisy:

```bash
bash scripts/clean_generated_outputs.sh safe
bash scripts/clean_generated_outputs.sh intermediate
bash scripts/clean_generated_outputs.sh all
```

## 참고 링크
- Notion: https://nimble-ceder-40b.notion.site/28_DT_-32317efd202c8158b35ac245c2b4dc73
