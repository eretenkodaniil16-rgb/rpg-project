from __future__ import annotations


CORRECTION_PASS = "v21_pass40"
TWOHAND_UP_F03_TARGETED_PROJECTION_REVIEW_REVISION = (
    "twohand_up_f03_upward_arc_projection_review_v21_pass40"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 3

TARGETED_PROJECTION_SPECS = (
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": 0.0,
        "screen_projection": 0.55,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": 0.0,
        "screen_projection": 0.50,
    },
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": 0.0,
        "screen_projection": 0.45,
    },
    {
        "source_pose_code": 4,
        "arm_blend": 0.80,
        "depth_branch": "source",
        "weapon_offset_degrees": 0.0,
        "screen_projection": 0.55,
    },
    {
        "source_pose_code": 4,
        "arm_blend": 0.80,
        "depth_branch": "source",
        "weapon_offset_degrees": 0.0,
        "screen_projection": 0.50,
    },
    {
        "source_pose_code": 4,
        "arm_blend": 0.80,
        "depth_branch": "source",
        "weapon_offset_degrees": 0.0,
        "screen_projection": 0.45,
    },
)

RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = True
REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = True

SOURCE_COMPLETE_RUN_ID = 30857617930
SOURCE_COMPLETE_ARTIFACT_ID = 8873199189
SOURCE_COMPLETE_ARTIFACT_SHA256 = (
    "31fa4cd7817e8ad858eca26b2bce4e78a222ecab4ed3063c1f02ed8e12d956df"
)
SOURCE_COMPLETE_FINDING = (
    "pass39 confirmed that the upward-arc families are original_f05 blend 0.60 "
    "and original_f04 blend 0.80; projection 0.575 preserved the intended arc "
    "but touched the top or right canvas edge"
)
