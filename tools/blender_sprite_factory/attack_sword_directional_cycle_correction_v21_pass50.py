from __future__ import annotations


CORRECTION_PASS = "v21_pass50"
TWOHAND_UP_F07_CONTINUITY_REVIEW_REVISION = (
    "twohand_up_f07_arm_projection_continuity_review_v21_pass50"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 7
PREVIOUS_REFERENCE_FRAME = 6
NEXT_REFERENCE_FRAME = 8
TARGET_BONES = (
    "upper_arm.L",
    "forearm.L",
    "hand.L",
    "upper_arm.R",
    "forearm.R",
    "hand.R",
)

SOURCE_FRAME_CANDIDATES = (8, 6, 5, 1)
SOURCE_FRAME_LABELS = {
    8: "original_f08",
    6: "selected_f06_arm_pose",
    5: "original_f05",
    1: "selected_f01_arm_pose",
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

MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = 1.0
MIN_VISIBLE_BLADE_SAMPLES = 4
MIN_CAMERA_MARGIN_PIXELS = 1.0
MAX_ABS_WEAPON_OFFSET_DEGREES = 84.0
REVIEW_VARIANT_COUNT = 6
REQUIRE_ZERO_EDGE_ALPHA_FOR_FINAL_ACCEPTANCE = True
RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = True

SOURCE_FAILED_RUN_ID = 30905969414
SOURCE_FAILED_ARTIFACT_ID = 8891183018
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "bc24480f7f03c0baefbf9fab317111f2bef9e5aa67206381052c019fda20452d"
)
SOURCE_FAILURE = (
    "pass49 selected f06 at weapon offset 30 degrees and temporary shift_x "
    "-0.01 with zero edge alpha, then the unchanged f07 arm pose produced no "
    "geometry-safe rigid-weapon candidate even under the non-key one-pixel "
    "head-clearance and camera-margin contract"
)
