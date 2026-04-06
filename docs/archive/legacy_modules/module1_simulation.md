# Module 1: Digital Twin Environment

## Purpose
Build a minimal digital twin simulation environment for the taxi-demand and dispatch pipeline.

## Minimum scenario
- City size: 3x3 blocks
- Passengers: 5
- Taxis: 3
- Regular vehicles: 4 types, 5 each
- Autonomous vehicle: 1
- Obstacles: 2

## Current status
- This repository does not yet contain a full 3D simulation engine implementation.
- The module currently defines the simulation concept, required assets, and a minimal scenario scaffold.

## Deliverables in this repository
- `module1_simulation/README.md`
- `module1_simulation/scenario.md`
- `module1_simulation/asset_requirements.md`
- `module1_simulation/minimal_stub.py`

## What is covered now
- Scenario definition
- Object counts and environment constraints
- Structure for future expansion into Unity / SUMO / Carla style simulation

## What remains
- Real-time movement logic
- Event logging
- Map/object/animation integration
- Actual simulation runtime
