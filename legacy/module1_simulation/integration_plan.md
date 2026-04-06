# Module 1 Digital Twin Integration Plan

## Goal
Connect the Module 1 scaffold to a real digital twin asset pipeline.

## What the assignment expects
- Use provided 3D Map / Object / Animation assets
- Build a city traffic simulation environment
- Place taxis, passengers, vehicles, and obstacles
- Reproduce movement and call events in the environment

## Current repository status
- Scenario definition: done
- Minimum executable scaffold: done
- Asset integration: not done yet

## Integration steps
1. Add the provided 3D assets into `module1_simulation/assets/`
2. Replace the simplified state-log simulation with a runtime that reads asset positions or scene definitions
3. Map taxi/passenger/vehicle entities to scene objects
4. Emit movement and call events from the scene runtime
5. Save outputs as logs for later modules

## Practical interpretation
Until the real assets are available, the repo keeps a lightweight runnable skeleton that documents the intended digital twin structure.
