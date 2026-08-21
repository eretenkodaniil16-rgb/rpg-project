# CI bootstrap for Blender action-potential integration v04.
#
# Blender resolves paths beginning with // relative to the currently loaded
# .blend file. In headless CI the startup file has no project path, so the
# standalone v03 builder could resolve //action_potential_models_v03.blend to
# the filesystem root. Save a tiny bootstrap .blend next to the scripts first;
# then run the normal v04 generator unchanged.

from pathlib import Path
import runpy

import bpy

HERE = Path(__file__).resolve().parent
BOOTSTRAP_BLEND = HERE / "_ci_bootstrap_action_potential.blend"
V04_SCRIPT = HERE / "action_potential_video_v04.py"

bpy.ops.wm.save_as_mainfile(filepath=str(BOOTSTRAP_BLEND))
print("ACTION_POTENTIAL_CI_BOOTSTRAP", BOOTSTRAP_BLEND)
runpy.run_path(str(V04_SCRIPT), run_name="__main__")
