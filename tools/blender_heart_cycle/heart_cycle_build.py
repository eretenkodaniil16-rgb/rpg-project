from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy

import heart_cycle_model as model

_BASE_BUILD_MODEL = model.build_model


def _build_model_with_stable_parenting(resolution: int) -> model.HeartBuild:
    build = _BASE_BUILD_MODEL(resolution)

    # Objects are created in world coordinates and parented later to chamber
    # controls. Blender otherwise interprets those coordinates as local and
    # shifts them. A parent inverse restores the authored world-space pose and
    # still lets animated control scaling act around the chamber centre.
    for obj in bpy.data.objects:
        if obj.parent is not None:
            obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()

    cutters = build.collections.get("cutters")
    if cutters is not None:
        cutters.hide_viewport = True
        cutters.hide_render = True
    return build


model.build_model = _build_model_with_stable_parenting


if __name__ == "__main__":
    raise SystemExit(model.main())
