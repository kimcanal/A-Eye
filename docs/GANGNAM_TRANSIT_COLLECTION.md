# Gangnam Transit Collection

Month: `202603`

## Decision

Use Gangnam/Yeoksam-area Seoul public-transport data first. The NYC TLC
dataset remains useful for real 5-minute taxi-label structure, but the
Gangnam transit profile is the stronger local demand proxy for presentation.

## Target Dongs

- 신사동
- 논현1동
- 논현2동
- 삼성1동
- 삼성2동
- 대치4동
- 역삼1동
- 역삼2동
- 압구정동
- 청담동

`압구정동` is present in `gangnam_ultimate_dataset.csv`, while the current
`__yeoksam_taxi` 3D map uses the other 9 dongs.

## Generated Artifacts

- `data/processed/transit/gangnam_transit_od_hourly_202603.csv`
- `data/processed/transit/gangnam_transit_od_hourly_summary_202603.csv`
- `data/processed/transit/gangnam_transit_peak_by_dong_202603.csv`
- `data/processed/transit/gangnam_transit_peak_hours_202603.csv`
- `data/processed/transit/gangnam_subway_station_hourly_202603.csv`
- `data/processed/transit/gangnam_subway_dong_hourly_summary_202603.csv`

## Top Micro-Area Transit Hours

| Rank | Hour | Avg micro-area pressure |
|---:|---:|---:|
| 1 | 18 | 97634.355 |
| 2 | 8 | 91500.613 |
| 3 | 17 | 78570.546 |
| 4 | 7 | 70675.936 |
| 5 | 9 | 60624.033 |

## Top Dong Peak Pressures

| Dong | Peak hour | Avg pressure | Inbound | Outbound |
|---|---:|---:|---:|---:|
| 역삼1동 | 18 | 25797.677 | 7711.226 | 19785.194 |
| 논현1동 | 18 | 17439.419 | 4167.387 | 13948.677 |
| 대치4동 | 18 | 13554.742 | 2772.645 | 11336.419 |
| 논현2동 | 8 | 11176.742 | 10157.097 | 1334.0 |
| 압구정동 | 18 | 9756.0 | 2941.194 | 7412.323 |

## Top Subway Stations

| Station | Dong | Daily avg station pressure |
|---|---|---:|
| 강남 | 역삼1동 | 314219.93 |
| 선릉 | 삼성2동 | 257316.13 |
| 역삼 | 역삼1동 | 194682.192 |
| 신논현 | 논현1동 | 127596.064 |
| 압구정 | 압구정동 | 125541.36 |
| 신사 | 신사동 | 106829.874 |
| 강남구청 | 논현2동 | 105435.998 |
| 봉은사 | 삼성1동 | 95156.708 |

## Interpretation

This is not taxi demand ground truth. It is a local movement-pressure proxy:

- high inbound/outbound public-transport flow indicates people movement
- taxi demand often rises around high movement pressure, bad weather, and low road speed
- combine this with `gangnam_ultimate_dataset.csv` for relative demand scoring
