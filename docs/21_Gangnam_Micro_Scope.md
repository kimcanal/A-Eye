# Gangnam Micro Scope

![Gangnam micro zone map](/Users/kenny31/Documents/Capstone/docs/assets/gangnam_micro_zone_map.svg)

## Purpose

This document defines a **project-scale 2D zone map** around Gangnam Station.
It is not a full Seoul digital twin.
It is a shared working map for:

- demand prediction
- dispatch prioritization
- Unity presentation scenes
- SUMO route grouping

## Scope Decision

We will treat the project as a **micro digital twin around Gangnam Station**.

- Real-world data source:
  - Gangnam Station area demand and nearby hotspot demand
- Simulation scope:
  - simplified 3x3 zone map
- Goal:
  - predict which zone gets busier
  - prioritize taxi dispatch across 9 simplified zones

This keeps the data story, model story, and Unity/SUMO story aligned.

## 3x3 Zone Layout

The map is centered on **Gangnam Station core / Gangnam-daero x Teheran-ro area**.

| Zone | Label | Suggested meaning |
|---|---|---|
| A1 | NW | North-west commercial / alley demand |
| A2 | N | Gangnam Station north exits / north curbside |
| A3 | NE | Teheran-ro west office frontage |
| B1 | W | Seocho-side west frontage / crossing inflow |
| B2 | C | Gangnam Station core hotspot |
| B3 | E | Teheran-ro east frontage / office pickup |
| C1 | SW | South-west commercial belt |
| C2 | S | Gangnam Station south exits / south curbside |
| C3 | SE | South-east office / connector belt |

## Recommended Project Rule

Use **B2** as the primary hotspot baseline.
Then expand to surrounding zones based on predicted demand.

Recommended dispatch interpretation:

- `B2`
  - core dispatch hotspot
- `A2`, `B3`, `C2`
  - secondary high-priority zones
- `A1`, `A3`, `B1`, `C1`, `C3`
  - surrounding support zones

## How To Use This

### For modeling

- treat each cell as one simplified service zone
- map detailed public-data points into one of these 9 zones

### For Unity

- place 3x3 city cells using this exact layout
- place the highest-priority taxi group in `B2`
- place secondary taxi groups in adjacent cells

### For SUMO

- create one route group per zone cluster
- start with `B2`, `A2`, `B3`, `C2`

## Practical Interpretation

This project should not claim:

- full Gangnam digital twin
- full Seoul traffic replication
- 1:1 road-level taxi simulation

This project **can** claim:

- demand prediction and dispatch validation in a constrained Gangnam Station micro-area
- simplified digital twin style verification in a 3x3 urban block model

## One-line Scope Statement

We define the capstone scope as a **Gangnam Station micro-area digital twin prototype** that predicts zone-level demand and validates dispatch strategies on a simplified 3x3 map.
