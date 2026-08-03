from __future__ import annotations


CORRECTION_PASS = "v21_pass44"
TWOHAND_UP_F03_COMPACT_PROJECTION_REVIEW_REVISION = (
    "twohand_up_f03_upward_arc_compact_projection_review_v21_pass44"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 3

COMPACT_PROJECTION_CANDIDATES = (0.30, 0.25, 0.20)
COMPACT_ANGLE_OFFSET_CANDIDATES = (0.0, -4.0, -8.0, -12.0)

TARGETED_COMPACT_SPECS = (
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -8.0,
        "screen_projection": 0.30,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -12.0,
        "screen_projection": 0.30,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": 0.0,
        "screen_projection": 0.25,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -4.0,
        "screen_projection": 0.25,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": -8.0,
        "screen_projection": 0.25,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": 0.0,
        "screen_projection": 0.20,
    },
)

RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = True
REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = True

SOURCE_PASS43_RUN_ID = 30860714915
SOURCE_PASS43_ARTIFACT_ID = 8874331270
SOURCE_PASS43_ARTIFACT_SHA256 = (
    "b7d0474f51e523546645f283d119995116f2cc9273f85afe0da6439a720cc4f8"
)
SOURCE_PASS43_FINDING = (
    "pass43 reduced the screen projection to 0.40 and 0.35 while preserving "
    "the original_f05 blend 0.60 arm pose, but every candidate still touched "
    "the top edge with six or seven alpha pixels; all other edges stayed clear"
)
