# Module 1. Digital Twin 시뮬레이션

## 목적
이 모듈은 카카오모빌리티 캡스톤 명세서의 Module 1 요구사항을 반영한 디지털 트윈 시뮬레이션 최소 구현이다.

## 최소 시나리오
- 도시 크기: 3x3 블럭
- 탑승자: 5명
- 택시: 3대
- 일반 차량: 차종 4종, 각 5대
- 자율주행 차량: 1대
- 장애물: 2개

## 현재 구현 범위
- 실제 3D 시뮬레이터(Unity, Carla, SUMO)는 미구현
- 시뮬레이션에 필요한 개체와 제약조건을 명세에 맞춰 정의
- runnable한 최소 시뮬레이션 스켈레톤을 제공
- 실행 결과로 JSON 로그와 요약 파일을 생성

## 파일
- `scenario.md`: 최소 시나리오 정의
- `asset_requirements.md`: 필요한 자산 목록
- `minimal_stub.py`: 명세를 코드로 표현한 스텁
- `minimal_simulation.py`: 실행 가능한 최소 시뮬레이션

## 실행
```bash
python3 module1_simulation/minimal_simulation.py
```

## 출력
- `outputs/module1/module1_simulation_log.json`
- `outputs/module1/module1_summary.json`

## 향후 확장
- 3D 맵 배치
- 객체 이동 로직 정교화
- 이벤트 로그 출력 강화
- 배차 알고리즘 연동
