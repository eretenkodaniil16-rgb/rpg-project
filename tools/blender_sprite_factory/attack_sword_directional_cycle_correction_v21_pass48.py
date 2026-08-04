from __future__ import annotations


CORRECTION_PASS = "v21_pass48"
TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION = (
    "twohand_up_f01_f02_f03_selected_f04_targeted_extended_overscan_"
    "full_cycle_diagnostic_v21_pass48"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 4
FRAME_ORDER = (1, 2, 3, 4, 5, 6, 7, 8)

# Pass47 proved that negative shift_x moves the rear-view blade away from the
# left canvas edge. Pass48 keeps the best geometry-safe 32 degree weapon
# offset and extends only the temporary camera overscan range.
F04_FIXED_WEAPON_OFFSET_DEGREES = 32.0
F04_CAMERA_SHIFT_X_CANDIDATES = (
    -0.050,
    -0.060,
    -0.070,
    -0.080,
    -0.090,
    -0.100,
    -0.120,
)
F04_FIXED_CENTER_COMPENSATION_USED = False
REQUIRE_ZERO_EDGE_ALPHA = True

SOURCE_FAILED_RUN_ID = 30904054095
SOURCE_FAILED_ARTIFACT_ID = 8890620536
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "7405a89af03ed48f2f8f884fc8ae823cddbee378171a3d4e9d76236bb0edecfa"
)
SOURCE_FAILURE = (
    "pass47 preserved f01 through f03 and tested shift_x -0.01 through -0.04; "
    "the best geometry-safe f04 offset remained 32 degrees and left-edge "
    "alpha fell from six or seven pixels to four at shift_x -0.04 while all "
    "other edges stayed clear; pass48 fixes that offset and extends only the "
    "temporary horizontal camera overscan"
)
