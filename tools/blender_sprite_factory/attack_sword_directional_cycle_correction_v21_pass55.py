from __future__ import annotations


CORRECTION_PASS = "v21_pass55"
TWOHAND_UP_FRONT_DEPTH_REVISION = (
    "twohand_up_f04_f05_front_depth_and_f08_boundary_v21_pass55"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
FRONT_DEPTH_FRAMES = (4, 5)
BOUNDARY_FIX_FRAME = 8

# Keep the pass54 screen-space trajectory exactly, but invert camera depth so
# the rigid sword module is rendered in front of the rear-view torso.
PROJECTED_WEAPON_PROFILE_OVERRIDES_BY_FRAME = {
    4: {
        "depth_branch": "flipped",
        "offset_degrees": 32.0,
        "projection": 0.960023,
    },
    5: {
        "depth_branch": "flipped",
        "offset_degrees": 0.0,
        "projection": 0.482838,
    },
}
EXPECTED_SOURCE_PROJECTION_OVERRIDES_BY_FRAME = {
    4: 0.960023,
    5: 0.482838,
}
CAMERA_SHIFT_X_OVERRIDES_BY_FRAME = {
    8: -0.05,
}

REQUIRE_FRONT_DEPTH_BRANCH = True
REQUIRE_ZERO_EDGE_ALPHA = True
PRESERVE_SCREEN_SPACE_TRAJECTORY = True
PRESERVE_ACTION_DATA = True

SOURCE_FAILED_RUN_ID = 30910793795
SOURCE_FAILED_ARTIFACT_ID = 8893911601
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "9a2ef81b4c8ff1a6e18bf7aac019c8bb1f170f69e6b625a4768653bbc0d2690a"
)
SOURCE_FAILED_COMMIT = "2fff7833ef0fc674d31800bfe926ae32cada1578"
SOURCE_FAILURE = (
    "pass54 rendered all directional frames, but twohand_up f04 and f05 placed "
    "the sword behind the rear-view torso during manual review; integrated "
    "twohand_up f08 also touched the left canvas edge at four alpha pixels"
)
