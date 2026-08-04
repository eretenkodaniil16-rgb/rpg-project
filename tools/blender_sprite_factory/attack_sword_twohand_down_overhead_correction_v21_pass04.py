from __future__ import annotations


CORRECTION_PASS = "v21_pass04"
OVERHEAD_WEAPON_ARC_REVISION = "centered_vertical_weapon_arc_f03_margin_v21_pass04"
TARGET_FRAME = 3
F03_SCREEN_PROJECTION = 0.76
REQUIRE_ZERO_EDGE_ALPHA = True
PRESERVE_F02 = True
PRESERVE_F04_F07_PROFILE = True
PRESERVE_BODY_ACTION = True
PRESERVE_WEAPON_GEOMETRY = True

SOURCE_FAILED_RUN_ID = 30956786634
SOURCE_FAILED_ARTIFACT_ID = 8911544251
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "18c870bf26de4a4bcc9ed4e6aeac77650abf47b875f76c6f7f0bf036f0b03184"
)
SOURCE_FAILURE = (
    "pass04 at projection 0.80 reduced normalized f03 top-edge contact from "
    "four alpha pixels to one; projection 0.76 reserves the final containment "
    "margin without changing the vertical screen axis"
)
