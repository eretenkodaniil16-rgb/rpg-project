from __future__ import annotations


CORRECTION_PASS = "v21_pass35"
TWOHAND_UP_F02_OCCLUSION_REVIEW_REVISION = (
    "twohand_up_f02_rear_view_occlusion_continuity_review_v21_pass35"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAMES = (1, 2, 3)

MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = 0.0
MIN_VISIBLE_BLADE_SAMPLES = 8
ALLOW_ZERO_SCREEN_GAP_WHEN_BLADE_IS_VISIBLE = True
PREFER_SOURCE_DEPTH_BRANCH = True
MAX_REFERENCE_RIGHT_EDGE_PIXELS = 4
REQUIRE_ZERO_EDGE_ALPHA_FOR_CANDIDATES = True

SOURCE_FAILED_RUN_ID = 30854585534
SOURCE_FAILED_ARTIFACT_ID = 8872057458
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "297f60abd7313f5ad54d31a50b10615b079a8b5c2e8cebce0bac0691bb572e65"
)
SOURCE_FAILURE = (
    "pass34 found six offset-zero f02 candidates but required positive side "
    "clearance and aborted on the unchanged f03 reference touching four right "
    "edge pixels; rear-view guard and windup must allow visible blade overlap "
    "with the head while preserving source depth and continuity"
)
