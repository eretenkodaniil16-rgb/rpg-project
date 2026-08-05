from __future__ import annotations


CORRECTION_PASS = "v21_pass03"
DIRECTIONAL_FRAMING_REVISION = (
    "twohand_overhead_directional_side_framing_v21_pass03"
)

# The action and character-local weapon arc remain identical. Side views need
# slightly more orthographic margin because the raised paired arms produce a
# taller projected silhouette than the approved down view.
DIRECTION_SCALE_MULTIPLIER = {
    "down": 1.0,
    "left": 0.93,
    "right": 0.93,
    "up": 1.0,
}
SIDE_DIRECTIONS = ("left", "right")
REQUIRE_ZERO_EDGE_ALPHA = True
PRESERVE_ACTION_CURVES = True
PRESERVE_CHARACTER_LOCAL_WEAPON_ARC = True
PRESERVE_DOWN_PASS04_PIXELS = True
PRESERVE_DIRECTIONAL_ASYMMETRY = True

SOURCE_FAILED_RUN_ID = 30959826679
SOURCE_FAILED_ARTIFACT_ID = 8912702932
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "d96bea7751ffec1bd4d015d806d2eb77898a6fb44045b8830bdc245c3ab3a1df"
)
SOURCE_FAILURE = (
    "projection-only containment could not clear left f03 because the raised "
    "paired arms and sword form a taller complete silhouette; all projection "
    "candidates from 0.76 through 0.44 still touched the top edge by 4-5 pixels"
)
