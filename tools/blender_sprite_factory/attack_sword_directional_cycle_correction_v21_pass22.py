from __future__ import annotations


CORRECTION_PASS = "v21_pass22"
ONEHAND_UP_DEPTH_AWARE_DIAGNOSTIC_REVISION = (
    "onehand_up_f05_f08_depth_aware_clearance_v21_pass22"
)
DIAGNOSTIC_SCENE_KEY = "attack_sword_onehand_up_depth_aware_diagnostic_v21"
CONTACT_SHEET_NAME = "attack_sword_01_onehand_up_depth_aware_diagnostic_v21.png"
HEAD_MODULE_IDS = (
    "head",
    "hair",
)
BLADE_CLEARANCE_PART_IDS = (
    "blade",
    "highlight",
    "tip",
)
MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = 1.0
DEPTH_MAP_SUPERSAMPLE = 4
WEAPON_EDGE_SAMPLE_STEP_PIXELS = 0.25
DEPTH_EPSILON_WORLD = 0.01
ALLOW_BLADE_OCCLUSION_BEHIND_HEAD = True
REQUIRE_ZERO_EDGE_ALPHA = True

SOURCE_FAILED_RUN_ID = 30754861863
SOURCE_FAILED_ARTIFACT_ID = 8835658875
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "9b3eb11787e42287d80f71846d0adb403f25614c39722f5067d97969f3a3dec1"
)
SOURCE_FAILURE = (
    "pass21 exhausted 6820 candidates for onehand_up f05 because its visible-"
    "blade check still used a flat 2D head rectangle; projected blade geometry "
    "behind the head therefore reported zero clearance even when the depth "
    "buffer would correctly hide it"
)
