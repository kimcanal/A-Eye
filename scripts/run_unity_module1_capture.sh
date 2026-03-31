#!/usr/bin/env bash

set -euo pipefail

CAPSTONE_ROOT="/Users/kenny31/Documents/Capstone"
UNITY_APP="/Applications/Unity/Unity.app/Contents/MacOS/Unity"
UNITY_PROJECT="/Users/kenny31/Downloads/PBL_AssetPackge/Modeling/New Unity Project"
UNITY_LOG="/tmp/unity_build_scene_manual.log"

if [[ ! -x "$UNITY_APP" ]]; then
  echo "Unity executable not found: $UNITY_APP" >&2
  exit 1
fi

if [[ ! -d "$UNITY_PROJECT" ]]; then
  echo "Unity project not found: $UNITY_PROJECT" >&2
  exit 1
fi

"$CAPSTONE_ROOT/.venv/bin/python" "$CAPSTONE_ROOT/src/module1/export_unity_scenario.py"

"$UNITY_APP" \
  -batchmode \
  -projectPath "$UNITY_PROJECT" \
  -executeMethod CapstoneSceneBuilder.BuildModule1Scene \
  -quit \
  -logFile "$UNITY_LOG"

"$CAPSTONE_ROOT/.venv/bin/python" "$CAPSTONE_ROOT/src/module1/render_unity_overlay.py"
"$CAPSTONE_ROOT/.venv/bin/python" "$CAPSTONE_ROOT/src/module1/build_unity_presentation.py"

echo "Unity scene build complete."
echo "Log: $UNITY_LOG"
echo "Screenshot: /Users/kenny31/Documents/Capstone/outputs/module1/unity_module1_view.png"
echo "Focus screenshot: /Users/kenny31/Documents/Capstone/outputs/module1/unity_module1_focus.png"
echo "Annotated screenshot: /Users/kenny31/Documents/Capstone/outputs/module1/unity_module1_annotated.png"
echo "Presentation board: /Users/kenny31/Documents/Capstone/outputs/module1/unity_module1_presentation.png"
echo "Scene: /Users/kenny31/Downloads/PBL_AssetPackge/Modeling/New Unity Project/Assets/Scenes/CapstoneModule1.unity"
echo "Scenario: /Users/kenny31/Documents/Capstone/outputs/module1/unity_scenario.json"
