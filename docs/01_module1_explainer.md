# Module 1 설명서

## 이 모듈이 하는 일
Module 1은 A-Eye 프로젝트의 바탕이 되는 디지털 트윈 시뮬레이션 환경을 정의합니다. 이 프로젝트는 택시 수요를 예측하고, 수요와 공급의 불균형을 바탕으로 배차 전략을 고민하는 것이 목표입니다. Module 1은 그 모든 작업이 일어나는 "가상의 도시 무대"를 먼저 만드는 단계입니다.

비전공자 관점에서 보면, 이 모듈은 "도시 한 구역을 작은 가상 세계로 만들어서, 그 안에 승객과 택시와 다른 차량들을 배치하고, 시간에 따라 조금씩 움직이게 해보는 것"입니다.

## 왜 필요한가
수요 예측이나 배차 전략은 단순한 숫자만으로는 설명하기 어렵습니다. 실제 도시처럼 보이는 환경이 있으면 다음을 더 쉽게 이해할 수 있습니다.
- 언제 사람이 많이 몰리는지
- 택시가 어느 지역에 부족한지
- 차량이 어떤 식으로 움직이는지
- 이후 예측 결과를 어디에 적용해야 하는지

즉, Module 1은 나머지 모듈이 의미를 가지도록 해주는 "배경 화면"입니다.

## 현재 구성
이 저장소의 Module 1은 실제 3D 게임 엔진(Unity, Carla, SUMO)을 직접 띄우는 수준은 아니고, 명세를 만족시키기 위한 최소 실행 골격입니다.

구성 요소는 다음과 같습니다.
- 도시 크기: 3x3 블럭
- 승객: 5명
- 택시: 3대
- 일반 차량: 4종 × 5대
- 자율주행 차량: 1대
- 장애물: 2개

각 객체는 좌표를 가지며, 간단한 시간 step 동안 움직임을 기록할 수 있습니다.

## 실행 방법
터미널에서 다음 명령을 실행하면 됩니다.

```bash
python3 module1_simulation/minimal_simulation.py
```

실행하면 다음 파일이 생성됩니다.
- `outputs/module1/module1_simulation_log.json`
- `outputs/module1/module1_summary.json`

## 실행 결과를 어떻게 해석하나
### `module1_simulation_log.json`
시간 step마다 어떤 객체가 어디에 있었는지와 어떤 움직임이 있었는지를 저장합니다.
예를 들면:
- 0번째 step: 초기 상태
- 1번째 step: 택시나 차량이 조금 이동한 상태
- 2번째 step: 다시 이동한 상태

이 파일은 "시뮬레이션이 실제로 돌아갔다"는 증거이자, 이후 분석을 위한 기록입니다.

### `module1_summary.json`
모든 객체 수와 출력 위치 같은 핵심 요약이 들어 있습니다.
- 도시 크기
- 승객 수
- 택시 수
- 차량 종류와 개수
- 장애물 수
- step 수

즉, 이 파일만 봐도 Module 1이 어떤 조건으로 구성되었는지 빠르게 확인할 수 있습니다.

## 현재 한계
이 Module 1은 아직 다음 기능은 포함하지 않습니다.
- 실제 3D 맵 렌더링
- 차량 간 충돌 처리
- 승객 탑승/하차 이벤트
- 경로 탐색
- 택시 배차 알고리즘 연동

즉, 지금은 "작동하는 최소 뼈대"이고, 실제 3D 시뮬레이터는 다음 단계 확장 과제입니다.

## 전체 구조에서 Module 1의 역할
A-Eye는 크게 다음 순서로 구성됩니다.
- Module 1: 도시 무대 만들기
- Module 2: 데이터를 정리해 모델이 읽을 수 있게 만들기
- Module 3: 수요를 예측하기
- Module 4: 예측 결과를 바탕으로 배차 전략을 정하기

Module 1은 이 전체 흐름의 출발점입니다. 무대가 있어야 데이터도 의미가 있고, 예측도 의미가 있고, 배차도 의미가 생깁니다.

## Asset compatibility check
The downloaded asset pack contains Kakaomobility Unity packages that match the assignment's Module 1 theme: a road/map package, taxi and obstacle objects, movement animations, and a map-setting package. This means the current Module 1 scaffold is directionally aligned with the real asset set, and can be upgraded into a Unity scene by importing those packages.

## Results analysis
The minimal simulation runs successfully, produces 31 entities, and logs movement events for taxi entities across 5 steps after the initial snapshot. This shows that the scenario is not only described on paper but also executable in a simplified form.
