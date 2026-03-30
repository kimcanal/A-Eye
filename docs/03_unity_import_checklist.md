# Unity Import Checklist for Module 1

## Objective
Bring the provided Kakaomobility 3D assets into a Unity project and connect them to the Module 1 scaffold.

## Recommended import order
1. Import `MapSetting_2.unitypackage`
2. Import `street_main.unitypackage`
3. Import vehicle and obstacle objects:
   - `car_taxi.unitypackage`
   - `obs_car_1.unitypackage`
   - `obs_car_2.unitypackage`
   - `obs_kickboard.unitypackage`
4. Import movement animations:
   - `carwheel_move.unitypackage`
   - `kickboard_fall.unitypackage`
5. Validate scene composition
6. Hook movement/call events into the simulation scaffold

## Scene mapping
- Taxi entity -> taxi object prefab
- Regular vehicles -> obstacle or placeholder vehicle prefabs if needed
- Passengers -> simple marker/object representation
- Obstacles -> obstacle prefabs
- Movement steps -> animation clips or timeline events

## Validation checklist
- [ ] Map asset imports without errors
- [ ] Taxi object appears in the scene
- [ ] Obstacle objects appear in the scene
- [ ] Movement animation plays correctly
- [ ] Scene matches the 3x3 block scenario
- [ ] Logs can be emitted from the scene runtime

## Notes
The repository's current runnable Python scaffold is a simplified state-log version. Once the Unity assets are imported, the same scenario definition can be mapped to actual scene objects and animation events.
