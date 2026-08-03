from __future__ import annotations


CORRECTION_PASS = "v21_pass42"
TWOHAND_UP_F03_EXTENDED_OFFSET_REVIEW_REVISION = (
    "twohand_up_f03_upward_arc_extended_offset_review_v21_pass42"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 3

EXTENDED_SCREEN_PROJECTION_CANDIDATES = (0.45,)
EXTENDED_ANGLE_OFFSET_CANDIDATES = (
    -12.0,
    -14.0,
    -16.0,
    -18.0,
    -20.0,
    -22.0,
)

TARGETED_OFFSET_SPECS = tuple(
    {
        "source_pose_code": 5,
        "arm_blend": 0.60,
        "depth_branch": "source",
        "weapon_offset_degrees": offset,
        "screen_projection": 0.45,
    }
    for offset in EXTENDED_ANGLE_OFFSET_CANDIDATES
)

RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = True
REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = True

SOURCE_PASS41_RUN_ID = 30859624987
SOURCE_PASS41_ARTIFACT_ID = 8873961062
SOURCE_PASS41_ARTIFACT_SHA256 = (
    "aeaeea5a32f9a7d1e0376f23b6868e47ec7a73df7a9bb3dd7007c7f828f136cf"
)
SOURCE_PASS41_FINDING = (
    "pass41 showed that offsets from minus four to minus ten degrees preserve "
    "the intended original_f05 blend 0.60 upward arc and keep the right edge "
    "clear, but every candidate still touched the top edge with seven or eight "
    "alpha pixels"
)
