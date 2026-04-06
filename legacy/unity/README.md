# Unity Module Skeleton

## 목적
Module 1의 최소 목표는 제공된 Unity 에셋을 import하여 도시 씬을 구성하고, 택시/장애물/차량을 배치해 배차 전후를 시각적으로 비교 가능한 상태를 만드는 것이다.

## 시작 순서
1. Unity Hub 설치
2. Unity 2022 LTS 프로젝트 생성
3. 아래 패키지 import
   - street_main.unitypackage
   - car_taxi.unitypackage
   - obs_car_1.unitypackage
   - obs_car_2.unitypackage
   - carwheel_move.unitypackage
4. 씬 저장
5. 택시 3대, 일반 차량, 장애물 배치
6. 캡처 또는 영상 저장

## 권장 산출물
- 씬 스크린샷
- 오브젝트 배치표
- 전/후 비교 영상

## 현재 실제 연결 방식
- Python 파이프라인이 `dispatch_recommendations.csv` 생성
- `src/module1/export_unity_scenario.py`가 상위 배차 결과를 `outputs/module1/unity_scenario.json`으로 변환
- Unity Editor 스크립트가 이 JSON을 읽어 택시 배치 장면을 자동 생성

## 현재 한계
- 셰이더 누락으로 인해 fallback material을 사용 중
- zone_id를 실제 GIS 좌표로 옮기는 단계는 아직 아님
- 현재는 데모 hotspot 슬롯 기반 배치

## 재실행
```bash
cd /Users/kenny31/Documents/Capstone
bash scripts/run_unity_module1_capture.sh
```

## 주요 결과물
- 최종 발표본: `outputs/module1/unity_module1_presentation.png`
- 시나리오 파일: `outputs/module1/unity_scenario.json`
- 스크래치 캡처: `outputs/module1/scratch/unity_module1_view.png`
- 스크래치 포커스 캡처: `outputs/module1/scratch/unity_module1_focus.png`
- 스크래치 오버레이: `outputs/module1/scratch/unity_module1_annotated.png`
