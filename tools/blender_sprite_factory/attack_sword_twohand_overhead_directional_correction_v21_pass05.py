from __future__ import annotations


CORRECTION_PASS = "v21_pass05"
DIRECTIONAL_FRAMING_REVISION = (
    "twohand_overhead_directional_measured_rear_framing_v21_pass05"
)
UP_SCALE_MULTIPLIER = 0.88
REQUIRE_ZERO_EDGE_ALPHA = True
PRESERVE_ACTION_CURVES = True
PRESERVE_CHARACTER_LOCAL_WEAPON_ARC = True
PRESERVE_DOWN_PASS04_PIXELS = True
PRESERVE_SIDE_PASS03_FRAMING = True
PRESERVE_DIRECTIONAL_ASYMMETRY = True

SOURCE_FAILED_RUN_ID = 30961703713
SOURCE_FAILED_ARTIFACT_ID = 8913474638
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "b900a438adc8f9e5783d97a397804c44a42a92b766f9e4e550ba0b5e32b55a4e"
)
SOURCE_RAW_F03_ALPHA_HEIGHT = 154
SOURCE_FIXED_SCALE = 0.644628
TARGET_NORMALIZED_ALPHA_HEIGHT = 88
SOURCE_FAILURE = (
    "pass04 preserved all down, left, and right frames but rear f03 still "
    "occupied the full 92-pixel baseline span at scale 0.93; the measured raw "
    "alpha height is 154 pixels, so a 0.88 directional multiplier reserves a "
    "stable four-pixel upper margin without modifying action curves"
)
