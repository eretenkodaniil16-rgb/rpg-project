from __future__ import annotations


CORRECTION_PASS = "v21_pass49"
TWOHAND_UP_F01_TO_F06_SELECTED_CYCLE_REVISION = (
    "twohand_up_f01_to_f06_selected_local_overscan_full_cycle_"
    "diagnostic_v21_pass49"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 6
FRAME_ORDER = (1, 2, 3, 4, 5, 6, 7, 8)

F06_FIXED_WEAPON_OFFSET_DEGREES = 30.0
F06_CAMERA_SHIFT_X_CANDIDATES = (
    -0.010,
    -0.020,
    -0.030,
    -0.040,
    -0.050,
    -0.060,
)
REQUIRE_ZERO_EDGE_ALPHA = True

SOURCE_FAILED_RUN_ID = 30905181774
SOURCE_FAILED_ARTIFACT_ID = 8890922018
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "43061271a13ee21d160914c98ca223d4bb50fe09d2470dde8ba930071cf5d927"
)
SOURCE_FAILURE = (
    "pass48 selected f04 at offset 32 degrees with temporary shift_x -0.06 "
    "and zero edge alpha, then f05 passed at offset 0 degrees; f06 stopped "
    "the cycle with its best candidate at offset 30 degrees touching only "
    "two left-edge pixels while right, top and bottom remained clear"
)
