from __future__ import annotations


CORRECTION_PASS = "v21_pass41"
TWOHAND_UP_F03_FINE_OFFSET_REVIEW_REVISION = (
    "twohand_up_f03_upward_arc_fine_offset_review_v21_pass41"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 3

FINE_SCREEN_PROJECTION_CANDIDATES = (0.50, 0.45)
FINE_ANGLE_OFFSET_CANDIDATES = (-4.0, -6.0, -8.0, -10.0)

TARGETED_OFFSET_SPECS = (
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -6.0,
        "screen_projection": 0.50,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -8.0,
        "screen_projection": 0.50,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -10.0,
        "screen_projection": 0.50,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -4.0,
        "screen_projection": 0.45,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -6.0,
        "screen_projection": 0.45,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -8.0,
        "screen_projection": 0.45,
    },
)

RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = True
REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = True

SOURCE_PASS40_RUN_ID = 30858909679
SOURCE_PASS40_ARTIFACT_ID = 8873680973
SOURCE_PASS40_ARTIFACT_SHA256 = (
    "c04054f09d7908abf3350c643e46d8e52885acc15558aff0b9b0064b73081dd5"
)
SOURCE_PASS40_FINDING = (
    "pass40 preserved the correct original_f05 blend 0.60 upward arc, but all "
    "zero-offset projection candidates still touched the top edge: projection "
    "0.55 had eight pixels, 0.50 had seven pixels, and 0.45 had six pixels"
)
