from __future__ import annotations


CORRECTION_PASS = "v21_pass43"
TWOHAND_UP_F03_DEPTH_CONTRACTION_REVIEW_REVISION = (
    "twohand_up_f03_upward_arc_depth_contraction_review_v21_pass43"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 3

DEPTH_CONTRACTION_PROJECTION_CANDIDATES = (0.40, 0.35)
DEPTH_CONTRACTION_ANGLE_CANDIDATES = (-8.0, -12.0, -16.0, -20.0)

TARGETED_DEPTH_SPECS = (
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -12.0,
        "screen_projection": 0.40,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -16.0,
        "screen_projection": 0.40,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -20.0,
        "screen_projection": 0.40,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -8.0,
        "screen_projection": 0.35,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -12.0,
        "screen_projection": 0.35,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -16.0,
        "screen_projection": 0.35,
    },
)

RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = True
REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = True

SOURCE_PASS42_RUN_ID = 30860213569
SOURCE_PASS42_ARTIFACT_ID = 8874162733
SOURCE_PASS42_ARTIFACT_SHA256 = (
    "f5fe19494387361100ea8e7867aa29f192cefc9662dfb8faa280a4366d81b49f"
)
SOURCE_PASS42_FINDING = (
    "pass42 confirmed that extending the clockwise screen-space offset from "
    "minus twelve through minus twenty-two degrees did not clear the top edge; "
    "the rigid blade remained too long in projection 0.45 while the right edge "
    "still had usable margin"
)
