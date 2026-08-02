from __future__ import annotations


CORRECTION_PASS = "v21_pass07"
TWOHAND_LEFT_ARM_REVISION = (
    "twohand_left_windup_to_guard_arm_blend_v21_pass07"
)
TARGET_ACTION_ID = "attack_sword_01_twohand_left_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "left"
TARGET_FRAME = 2
GUARD_FRAME = 1
TARGET_BONES = (
    "upper_arm.L",
    "forearm.L",
    "hand.L",
    "upper_arm.R",
    "forearm.R",
    "hand.R",
)
BLEND_CANDIDATES = (
    0.10,
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.90,
    1.00,
)
WEAPON_OFFSET_DEGREES = 46.0
MIN_HEAD_CLEARANCE_PIXELS = 4.0
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True
SOURCE_FAILED_RUN_ID = 30743767105
SOURCE_FAILED_ARTIFACT_ID = 8832298907
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "1d8bc31cc934b1c0cae0e1d7fdca1887e25a8bb78873243b2ec68fee44631ba7"
)
SOURCE_FAILURE = (
    "twohand_left/f02 rigid +46 degrees clears head but touches top edge"
)
SOURCE_OFFSET_HEAD_CLEARANCE_PIXELS = 5.578
SOURCE_OFFSET_CAMERA_MARGIN_PIXELS = 1.418
SOURCE_OFFSET_EDGE_ALPHA_COUNTS = {
    "left": 0,
    "right": 0,
    "top": 7,
    "bottom": 0,
}
