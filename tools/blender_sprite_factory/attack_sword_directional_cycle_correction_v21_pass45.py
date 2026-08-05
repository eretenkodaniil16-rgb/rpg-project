from __future__ import annotations


CORRECTION_PASS = "v21_pass45"
TWOHAND_UP_F03_CAMERA_OVERSCAN_REVIEW_REVISION = (
    "twohand_up_f03_camera_overscan_review_v21_pass45"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 3

SELECTED_SOURCE_POSE_CODE = 5
SELECTED_ARM_BLEND = 0.60
SELECTED_DEPTH_BRANCH = "source"
SELECTED_WEAPON_OFFSET_DEGREES = 0.0
SELECTED_SCREEN_PROJECTION = 0.25

CAMERA_SHIFT_Y_CANDIDATES = (0.02, 0.04, 0.06, 0.08, 0.10, 0.12)

TARGETED_OVERSCAN_SPECS = tuple(
    {
        "source_pose_code": SELECTED_SOURCE_POSE_CODE,
        "arm_blend": SELECTED_ARM_BLEND,
        "depth_branch": SELECTED_DEPTH_BRANCH,
        "weapon_offset_degrees": SELECTED_WEAPON_OFFSET_DEGREES,
        "screen_projection": SELECTED_SCREEN_PROJECTION,
        "camera_shift_y": shift_y,
    }
    for shift_y in CAMERA_SHIFT_Y_CANDIDATES
)

RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = True
REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = True

SOURCE_PASS44_RUN_ID = 30861229962
SOURCE_PASS44_ARTIFACT_ID = 8874507849
SOURCE_PASS44_ARTIFACT_SHA256 = (
    "3eef25f623359d02376c30a4d58b9108d167d2e630163d1c28c1e5d1426c4da2"
)
SOURCE_PASS44_FINDING = (
    "pass44 proved that the 192x192 raw render clips the sword before output "
    "normalization: projections from 0.30 through 0.20 still had five to seven "
    "top-edge pixels, while the projection 0.25 zero-offset pose retained 557 "
    "visible blade samples and the intended original_f05 blend 0.60 upward arc"
)
