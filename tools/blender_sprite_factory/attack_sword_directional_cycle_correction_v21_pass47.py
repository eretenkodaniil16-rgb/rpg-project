from __future__ import annotations


CORRECTION_PASS = "v21_pass47"
TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION = (
    "twohand_up_f01_f02_f03_selected_f04_horizontal_overscan_"
    "full_cycle_diagnostic_v21_pass47"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 4
FRAME_ORDER = (1, 2, 3, 4, 5, 6, 7, 8)

# Blender camera shift_x moves the orthographic view horizontally without
# changing model transforms, weapon geometry, perspective or render scale.
# Negative values move the captured view toward the clipped left-hand blade.
F04_CAMERA_SHIFT_X_CANDIDATES = (
    -0.010,
    -0.015,
    -0.020,
    -0.025,
    -0.030,
    -0.040,
)
F04_FIXED_CENTER_COMPENSATION_USED = False
REQUIRE_ZERO_EDGE_ALPHA = True

SOURCE_FAILED_RUN_ID = 30862305118
SOURCE_FAILED_ARTIFACT_ID = 8874892768
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "31233b839935fe708e625b1b71dfd7b1e68829d3c7b912481ac5dbc18be209be"
)
SOURCE_FAILURE = (
    "pass46 validated f01, f02 and the selected f03 with zero edge alpha, "
    "then f04 failed all planner offsets 32 through 40 degrees with six to "
    "seven alpha pixels on the left edge while top, right and bottom stayed "
    "clear; pass47 tests only temporary horizontal camera overscan"
)
