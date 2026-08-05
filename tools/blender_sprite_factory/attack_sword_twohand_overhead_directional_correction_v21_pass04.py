from __future__ import annotations


CORRECTION_PASS = "v21_pass04"
DIRECTIONAL_FRAMING_REVISION = (
    "twohand_overhead_directional_rear_framing_v21_pass04"
)
UP_SCALE_MULTIPLIER = 0.93
REQUIRE_ZERO_EDGE_ALPHA = True
PRESERVE_ACTION_CURVES = True
PRESERVE_CHARACTER_LOCAL_WEAPON_ARC = True
PRESERVE_DOWN_PASS04_PIXELS = True
PRESERVE_SIDE_PASS03_FRAMING = True
PRESERVE_DIRECTIONAL_ASYMMETRY = True

SOURCE_FAILED_RUN_ID = 30960602143
SOURCE_FAILED_ARTIFACT_ID = 8913121051
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "2200d227484a90f7a47b992575a48f9d55afa331f8c5d5be018c40e27ac18b8f"
)
SOURCE_FAILURE = (
    "pass03 completed all down, left, and right frames with zero edge alpha; "
    "the unchanged rear-view raised silhouette touched the top edge at up f03 "
    "for every projection candidate, matching the previously solved side-view "
    "framing condition"
)
