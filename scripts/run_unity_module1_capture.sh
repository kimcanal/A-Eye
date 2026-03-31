#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAPSTONE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_UNITY_APP="/Applications/Unity/Unity.app/Contents/MacOS/Unity"
DEFAULT_UNITY_PROJECT="$HOME/Downloads/PBL_AssetPackge/Modeling/New Unity Project"
UNITY_APP="${UNITY_APP:-$DEFAULT_UNITY_APP}"
UNITY_PROJECT="${UNITY_PROJECT:-$DEFAULT_UNITY_PROJECT}"
UNITY_LOG="${UNITY_LOG:-/tmp/unity_build_scene_manual.log}"
PYTHON_BIN="${PYTHON_BIN:-$CAPSTONE_ROOT/.venv/bin/python}"
UNITY_EDITOR_SCRIPT_SOURCE="$CAPSTONE_ROOT/unity/CapstoneSceneBuilder.cs"
UNITY_EDITOR_SCRIPT_DEST="$UNITY_PROJECT/Assets/Editor/CapstoneSceneBuilder.cs"
README_ASSET_DEST="$CAPSTONE_ROOT/docs/assets/unity_module1_presentation.png"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  echo "Create the virtualenv first or set PYTHON_BIN to a valid interpreter." >&2
  exit 1
fi

if [[ ! -x "$UNITY_APP" ]]; then
  echo "Unity executable not found: $UNITY_APP" >&2
  echo "Set UNITY_APP=/path/to/Unity.app/Contents/MacOS/Unity and retry." >&2
  exit 1
fi

if [[ ! -d "$UNITY_PROJECT" ]]; then
  echo "Unity project not found: $UNITY_PROJECT" >&2
  echo "Set UNITY_PROJECT=/path/to/your/UnityProject and retry." >&2
  exit 1
fi

mkdir -p "$(dirname "$UNITY_EDITOR_SCRIPT_DEST")"
cp "$UNITY_EDITOR_SCRIPT_SOURCE" "$UNITY_EDITOR_SCRIPT_DEST"

export CAPSTONE_ROOT

"$PYTHON_BIN" "$CAPSTONE_ROOT/src/module1/export_unity_scenario.py"

"$UNITY_APP" \
  -batchmode \
  -projectPath "$UNITY_PROJECT" \
  -executeMethod CapstoneSceneBuilder.BuildModule1Scene \
  -quit \
  -logFile "$UNITY_LOG"

"$PYTHON_BIN" "$CAPSTONE_ROOT/src/module1/render_unity_overlay.py"
"$PYTHON_BIN" "$CAPSTONE_ROOT/src/module1/build_unity_presentation.py"

if [[ -d "$(dirname "$README_ASSET_DEST")" ]]; then
  cp "$CAPSTONE_ROOT/outputs/module1/unity_module1_presentation.png" "$README_ASSET_DEST"
fi

echo "Unity scene build complete."
echo "Log: $UNITY_LOG"
echo "Screenshot: $CAPSTONE_ROOT/outputs/module1/unity_module1_view.png"
echo "Focus screenshot: $CAPSTONE_ROOT/outputs/module1/unity_module1_focus.png"
echo "Annotated screenshot: $CAPSTONE_ROOT/outputs/module1/unity_module1_annotated.png"
echo "Presentation board: $CAPSTONE_ROOT/outputs/module1/unity_module1_presentation.png"
echo "README asset copy: $README_ASSET_DEST"
echo "Scene: $UNITY_PROJECT/Assets/Scenes/CapstoneModule1.unity"
echo "Scenario: $CAPSTONE_ROOT/outputs/module1/unity_scenario.json"
