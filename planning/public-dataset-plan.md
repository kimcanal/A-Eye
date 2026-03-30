# Public Dataset Plan

## Goal

This document maps the assignment spec to realistic public datasets that the team can actually use.

The assignment asks for:

- time + location based demand modeling
- external feature engineering
- short-term demand forecasting
- dispatch optimization using predicted demand and current supply

## Key conclusion

There is no clearly usable official Seoul public dataset in this repo workflow that exposes full taxi call logs at the required granularity.

The best practical strategy is:

1. use a strong public **proxy demand dataset** as the main training data
2. use **weather / holiday / traffic** as external features
3. use the available taxi OD sample only as a **supporting EDA reference**

## Recommended priority

### Priority 1: Main training dataset

#### 서울시 행정동별 대중교통 총 승차 승객수 정보
- Link: https://data.seoul.go.kr/dataList/OA-21223/S/1/datasetView.do
- Why it fits:
  - 1 day, 1 hour granularity
  - administrative-dong level
  - daily updates
  - almost exactly matches the team's current target schema: `date`, `hour`, `zone`, `pickup_count`
- Best use:
  - Phase 1 baseline forecasting
  - phase 1 dispatch scoring

### Priority 2: Mode-specific alternatives

#### 서울시 행정동별 버스 총 승차 승객수 정보
- Link: https://data.seoul.go.kr/dataList/OA-21225/S/1/datasetView.do
- Why it fits:
  - same 1 day, 1 hour, dong-based granularity
  - bus-only demand signal
- Best use:
  - if the team wants a more commute-heavy demand proxy

#### 서울시 행정동별 지하철 총 승차 승객수 정보
- Link: https://data.seoul.go.kr/dataList/OA-21224/S/1/datasetView.do
- Why it fits:
  - same 1 day, 1 hour, dong-based granularity
  - subway-only demand signal
- Best use:
  - if the team wants to emphasize station-area surges

### Priority 3: OD support dataset

#### 서울시 행정동 단위 대중교통 출발지/도착지 승객수 정보
- Link: https://data.seoul.go.kr/dataList/OA-21226/F/1/datasetView.do
- Why it fits:
  - 1 day, 1 hour granularity
  - origin/destination passenger flow by dong
  - downloadable daily/monthly zip files
- Best use:
  - explain movement direction
  - later dispatch redistribution logic
  - support analysis for Module 4

### Priority 4: Finer spatial alternative

#### 서울시 버스노선별 정류장별 시간대별 승하차 인원 정보
- Link: https://data.seoul.go.kr/dataList/OA-12913/S/1/datasetView.do
- Why it fits:
  - route-stop-hour demand
  - closer to "pickup point" thinking
  - richer than dong-level aggregates
- Tradeoff:
  - data is larger and more complex
  - route/stop cleanup work is heavier
- Best use:
  - if the team wants more detailed pickup hotspots later

#### 서울시 지하철 호선별 역별 시간대별 승하차 인원 현황
- Link: https://data.seoul.go.kr/bsp/wgs/dataView/data300View/514.do
- Why it fits:
  - station-hour demand
  - clear time-series structure
- Tradeoff:
  - not taxi-specific
  - station-based, not dong-based

## External feature datasets

### Weather

#### 기상청 단기예보 조회서비스
- Link: https://www.data.go.kr/data/15084084/openapi.do
- Why it fits:
  - real-time updates
  - short-term weather features
  - supports grid-based local weather
- Best feature columns:
  - precipitation
  - temperature
  - humidity
  - sky status
  - wind speed

### Holiday / special day

#### 한국천문연구원 특일 정보
- Link: https://www.data.go.kr/data/15012690/openapi.do
- Why it fits:
  - public holiday / anniversary / special-day flags
- Best feature columns:
  - holiday flag
  - special day type

### Traffic speed

#### 서울도시고속도로 일별 시간대별 교통소통(속도) 정보
- Link: https://data.seoul.go.kr/dataList/OA-15247/F/1/datasetView.do
- Why it fits:
  - date + hour + road segment + speed
  - useful as an external congestion signal
- Best use:
  - congestion feature for forecasting
  - traffic context for dispatch explanation

### Real-time extension

#### 서울시 실시간 인구데이터
- Link: https://data.seoul.go.kr/bsp/wgs/dataView/data300View/6225.do
- Why it fits:
  - real-time population by major places
  - good for Phase 3 real-time extension
- Tradeoff:
  - 122 named places, not full dong coverage

#### 서울시 실시간 도시데이터
- Link: https://data.seoul.go.kr/dataList/OA-21285/A/1/datasetView.do
- Why it fits:
  - combines population, traffic, weather, subway arrival, events, etc.
- Tradeoff:
  - location coverage is limited to major places

## Taxi-specific data found

#### 서울특별시 일자별 택시 OD 유형별 상위 10개소
- Link: https://www.data.go.kr/data/15135325/fileData.do
- Why it is not the main dataset:
  - only top 10 places
  - sample-sized public release
  - not full demand distribution
  - not ideal for training a forecasting model
- Best use:
  - supporting EDA
  - hotspot explanation
  - presentation background

## Recommended team path

### Option A: easiest stable route
1. Main: `서울시 행정동별 대중교통 총 승차 승객수 정보`
2. Extra features: weather + holiday
3. Later: traffic speed
4. Optional support: taxi OD sample as EDA only

### Option B: more detailed route
1. Main: `서울시 버스노선별 정류장별 시간대별 승하차 인원 정보`
2. Map stops to zones
3. Add weather + holiday + traffic
4. Add OD support later

## Final recommendation

For this team, the best first public-data choice is:

1. `서울시 행정동별 대중교통 총 승차 승객수 정보`
2. `기상청 단기예보 조회서비스`
3. `한국천문연구원 특일 정보`
4. `서울도시고속도로 일별 시간대별 교통소통(속도) 정보`

This is the most practical combination for:

- matching the assignment structure
- minimizing preprocessing complexity
- keeping the project explainable for the team
