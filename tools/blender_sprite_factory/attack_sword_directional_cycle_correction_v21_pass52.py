from __future__ import annotations


CORRECTION_PASS = "v21_pass52"
TWOHAND_UP_F08_SETTLE_REVIEW_REVISION = (
    "twohand_up_f08_guard_settle_continuity_review_v21_pass52"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 8
PREVIOUS_REFERENCE_FRAME = 7
GUARD_REFERENCE_FRAME = 1
TARGET_BONES = (
    "upper_arm.L",
    "forearm.L",
    "hand.L",
    "upper_arm.R",
    "forearm.R",
    "hand.R",
)

SOURCE_POSE_CODES = (7, 1, 6, 5)
SOURCE_POSE_LABELS = {
    7: "selected_f07_arm_pose",
    1: "guard_f01_arm_pose",
    6: "selected_f06_arm_pose",
    5: "original_f05_arm_pose",
}
ARM_BLEND_CANDIDATES = (0.0, 0.20, 0.40, 0.60, 0.80, 1.00)
SCREEN_PROJECTION_CANDIDATES = (0.90, 0.75, 0.60, 0.45, 0.30, 0.20)
ANGLE_OFFSET_CANDIDATES = (
    0.0,
    -12.0,
    12.0,
    -24.0,
    24.0,
    -36.0,
    36.0,
    -48.0,
    48.0,
    -60.0,
    60.0,
    -72.0,
    72.0,
    -84.0,
    84.0,
)
DEPTH_BRANCH_CANDIDATES = ("source", "flipped")

SELECTED_F07_SOURCE_FRAME = 6
SELECTED_F07_ARM_BLEND = 0.20
SELECTED_F07_CAMERA_SHIFT_X = -0.070
SELECTED_F07_WEAPON_OFFSET_DEGREES = 60.0
SELECTED_F07_SCREEN_PROJECTION = 0.90

MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = 1.0
MIN_VISIBLE_BLADE_SAMPLES = 4
MIN_CAMERA_MARGIN_PIXELS = 1.0
MAX_ABS_WEAPON_OFFSET_DEGREES = 84.0
REVIEW_VARIANT_COUNT = 6
REQUIRE_ZERO_EDGE_ALPHA_FOR_FINAL_ACCEPTANCE = True
RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = True

SOURCE_FAILED_RUN_ID = 30907489747
SOURCE_FAILED_ARTIFACT_ID = 8891849751
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "2869f19e3bfa3f6b70dd300ab633a2f2302b8630678cc64f2fbeb6b2293946d7"
)
SOURCE_FAILURE = (
    "pass51 selected f07 review variant 1 with temporary shift_x -0.07 and "
    "zero edge alpha, then the original settle frame f08 produced no "
    "geometry-safe rigid-weapon candidate before rendering"
)
