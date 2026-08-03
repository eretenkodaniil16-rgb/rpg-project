from __future__ import annotations

CORRECTION_PASS = "v21_pass27"
TWOHAND_UP_F01_SOLVER_REVISION = (
    "twohand_up_f01_depth_aware_rigid_weapon_solver_v21_pass27"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAMES = (1,)

SEARCH_SCREEN_PROJECTIONS = (
    0.95,
    0.90,
    0.85,
    0.80,
    0.75,
    0.70,
    0.65,
    0.60,
    0.55,
    0.50,
    0.45,
    0.40,
    0.35,
    0.30,
)
SEARCH_OFFSET_LIMIT_DEGREES = 90
SEARCH_OFFSET_STEP_DEGREES = 6
SEARCH_DEPTH_BRANCHES = ("source", "flipped")
MAX_RENDER_ATTEMPTS = 16

MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = 1.0
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True
ALLOW_BLADE_OCCLUSION_BEHIND_HEAD = True
PREFER_HIGH_SCREEN_PROJECTION = True

SOURCE_FAILED_RUN_ID = 30774895237
SOURCE_FAILED_ARTIFACT_ID = 8841935284
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "7f2c95d6011e985d114939d7c8fc84eba7068ed2c692ca2adcebb4190db3f599"
)
SOURCE_FAILURE = (
    "pass02 found no geometry-safe candidate for "
    "twohand_center_high/up/f01"
)
