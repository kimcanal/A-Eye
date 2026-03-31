# Unity Module 1 Actual Run Notes

## What was verified

- Unity Editor launch succeeded with the provided asset project.
- Required assets for Module 1 were imported into the Unity project.
- A real Unity scene was generated in batch mode.
- A screenshot was rendered from Unity and saved into the Capstone project outputs folder.

## Unity project used

- Unity project: `/Users/kenny31/Downloads/PBL_AssetPackge/Modeling/New Unity Project`
- Unity version: `6000.0.68f1`

## Generated outputs

- Screenshot: `/Users/kenny31/Documents/Capstone/outputs/module1/unity_module1_view.png`
- Scene file: `/Users/kenny31/Downloads/PBL_AssetPackge/Modeling/New Unity Project/Assets/Scenes/CapstoneModule1.unity`
- Scenario JSON: `/Users/kenny31/Documents/Capstone/outputs/module1/unity_scenario.json`

## Important implementation note

The imported map initially rendered as magenta because the provided materials reference custom shaders that are not fully present in the package set.  
To make the scene visible and reviewable, the Unity scene builder applies fallback Standard materials at runtime for the generated Module 1 scene.

This means:

- geometry is real Unity asset geometry
- placement is real Unity scene placement
- colors are fallback materials for visibility, not final art-direction materials

## How to rerun

```bash
cd /Users/kenny31/Documents/Capstone
bash scripts/run_unity_module1_capture.sh
```

## Data bridge

The current Module 1 path is now:

1. dispatch results are generated from the Python pipeline
2. `src/module1/export_unity_scenario.py` converts the top dispatch priorities into `unity_scenario.json`
3. Unity reads that scenario file and places taxis into fixed demo slots in the city scene

This is a real code bridge between the prediction/dispatch pipeline and the Unity scene, even though the zone-to-world mapping is still a demo-slot mapping rather than full GIS placement.

## Current Module 1 scene contents

- street map prefab
- 3 taxi objects
- 4 obstacle objects
  - cones
  - bollard
  - road fence

## Next logical steps

1. Adjust camera framing to focus more tightly on one main intersection.
2. Replace fallback materials with the correct shaders or compatible URP/Built-in conversions.
3. Add animated movement or multiple screenshots for before/after dispatch storytelling.
