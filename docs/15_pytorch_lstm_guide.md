# PyTorch LSTM 가이드

## 왜 추가했는가

과제 명세서에는 수요 예측 모델 예시로 `CNN-LSTM`, `ConvLSTM` 같은 딥러닝 구조가 나온다.
그래서 현재 저장소에는 baseline(RandomForest) 외에 딥러닝 확장용으로 `LSTM` 예제를 추가했다.

## 현재 위치

- 코드: `src/prediction/train_lstm.py`
- 설정: `configs/base.yaml`의 `lstm` 섹션

## 현재 구조

입력은 과거 `seq_len`개 시점의 feature sequence다.

사용 feature:
- `available_taxis`
- `hour`
- `day_of_week`
- `lag_1`
- `rolling_mean_3`

타깃:
- 현재 시점의 `call_count`

즉, “이전 몇 개 시점의 흐름을 보고 다음 수요를 맞추는” 기본 LSTM 구조다.

## 실행

PyTorch 설치 후 아래처럼 실행하면 된다.

```bash
.venv/bin/python -m src.prediction.train_lstm
```

## 산출물

- `outputs/lstm_metrics.json`
- `outputs/lstm_predictions.csv`

## 해석

이 LSTM은 최종 모델이라기보다 다음 목적을 가진다.

- PyTorch 기반 딥러닝 실험 시작점
- 이후 CNN-LSTM으로 가기 전 구조 이해
- baseline과 비교할 수 있는 딥러닝 기준선 확보

## 다음 단계

- grid 기반 입력으로 바꾸기
- 지역 간 공간 관계를 반영하기
- 이후 `CNN-LSTM` 또는 `ConvLSTM`으로 확장하기
