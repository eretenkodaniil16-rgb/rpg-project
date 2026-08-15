from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def _extract_option(name: str, default: str | None = None) -> str | None:
    if "--" not in sys.argv:
        return default
    try:
        index = sys.argv.index(name)
    except ValueError:
        return default
    if index + 1 >= len(sys.argv):
        raise ValueError(f"{name} requires a value")
    value = sys.argv[index + 1]
    del sys.argv[index:index + 2]
    return value


HRA_GLB = _extract_option("--hra-glb")
HRA_YAW = float(_extract_option("--hra-yaw", "0") or 0.0)
if not HRA_GLB:
    raise RuntimeError("--hra-glb is required")

# v2 base runner keeps the proven 105 s mechanics but also runs the chamber
# assembly/vessel-offset repair. The procedural chambers are subsequently
# hidden by the HRA integration; its improved great-vessel tree remains.
import heart_starling_anrep_v02_runner_v2 as base  # noqa: E402
import heart_hra_reference_v01 as hra  # noqa: E402

app = base.runner.app
_original_app_build_model = app.build_model


def build_model_with_hra(resolution: int):
    build = _original_app_build_model(resolution)
    hra.integrate(build, HRA_GLB, HRA_YAW)
    return build


app.build_model = build_model_with_hra
app.MODEL_REVISION = "hra_heart_male_v1_2_starling_anrep"
app.BLEND_NAME = "hra_heart_male_v1_2_starling_anrep.blend"


if __name__ == "__main__":
    raise SystemExit(app.main())
