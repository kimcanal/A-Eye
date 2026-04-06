# A-Eye
# [카카오모빌리티 - AI 기반 택시 수요 예측 및 동적 배차 시스템 (캡스톤디자인)](https://nimble-ceder-40b.notion.site/28_DT_-32317efd202c8158b35ac245c2b4dc73)

Kakao Mobility capstone repository for a **Yeoksam-dong 3x3 taxi dispatch Digital Twin**.

The repository now has **one active path only**:
- `SUMO baseline`
- `5-minute synthetic Yeoksam demand`
- `rule-based dispatch`
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

## Folder Guide

### Active
- `configs/`
  - active YAML config for the Yeoksam SUMO path
- `src/`
  - active Python pipeline code
- `scripts/`
  - active runnable scripts only
- `module1_sumo/`
  - active SUMO network, routes, and configs for Yeoksam
- `docs/`
  - active docs for the current path
- `data/`
  - active generated input data for the current path
- `outputs/`
  - active generated outputs for the current path

### Archived / Legacy
- `legacy/`
  - old Unity work, public-data experiments, previous outputs, and older helper scripts
- `docs/archive/`
  - previous planning, meetings, and older pipeline notes

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

이 단계는 선택적인 고도화 단계이며, 기본 파이프라인에는 포함되지 않습니다.

## Module 1 / Unity 문서
- `docs/01_module1_compendium.md`
- `docs/06_team_guide_module1.md`
- `docs/07_unity_workflow_checklist.md`
- `docs/08_module1_code_map.md`
- `docs/18_module1_visualization_guide.md`

Module 1 최소 시각화 실행:

```bash
bash scripts/run_module1.sh
```

생성 결과:
- `outputs/module1/module1_overview.png`
- `outputs/module1/module1_simulation.gif`

Unity 실제 브리지 실행:

```bash
bash scripts/run_unity_module1_capture.sh


.
```

생성 결과:
- `outputs/module1/unity_module1_view.png`
- `outputs/module1/unity_module1_annotated.png`
- `outputs/module1/unity_module1_presentation.png`
- `outputs/module1/unity_scenario.json`

## 참고 링크
- Notion: https://nimble-ceder-40b.notion.site/28_DT_-32317efd202c8158b35ac245c2b4dc73
