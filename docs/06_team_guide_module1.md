# Module 1 Team Guide

## What we are building
We are building the first stage of the A-Eye project: the digital twin simulation environment.

The goal is not just to have a prediction model. The goal is to create a city-like simulation where taxi-demand behavior can be observed, logged, and later connected to the prediction and dispatch modules.

## What the assignment assets provide
The downloaded asset pack includes Unity packages for:
- a road/map scene
- taxi and obstacle objects
- motion/animation assets
- map-setting assets

These assets are the actual 3D pieces that can be imported into Unity.

## What we already have in the repo
- A minimal runnable Module 1 scaffold in Python
- Scenario documentation
- Asset analysis documentation
- Unity import checklist
- Execution results and summary documents
- A consolidated Module 1 compendium

## What each team member should do next
### 1. Unity / scene builder
- Create a Unity project
- Import the provided `.unitypackage` files
- Build the 3x3 city-block scene
- Place taxis, obstacles, and other objects
- Make sure movement animations play correctly

### 2. Simulation / logic builder
- Map the Unity scene objects to the scenario definition
- Decide how entities move through time
- Emit scene events or logs
- Keep the simulation output machine-readable

### 3. Documentation / coordination
- Keep the Module 1 docs updated
- Record which asset goes where
- Write down what was imported and what still needs work
- Keep the team aligned on what counts as "done"

## Suggested implementation workflow
1. Import `MapSetting_2.unitypackage`
2. Import `street_main.unitypackage`
3. Import taxi and obstacle objects
4. Import movement animations
5. Verify the scene visually in Unity
6. Connect scene behavior to the scenario model
7. Export or log the scene events

## How this connects to later modules
- Module 1 creates the environment
- Module 2 turns data into usable features
- Module 3 predicts demand
- Module 4 turns demand imbalance into dispatch decisions

Without Module 1, the later modules do not have a real stage to work on.
