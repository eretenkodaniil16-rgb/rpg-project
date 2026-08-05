from __future__ import annotations


CORRECTION_PASS = "v21_pass21"
ONEHAND_UP_VISIBLE_BLADE_DIAGNOSTIC_REVISION = (
    "onehand_up_f05_f08_visible_blade_clearance_v21_pass21"
)
DIAGNOSTIC_SCENE_KEY = "attack_sword_onehand_up_visible_blade_diagnostic_v21"
CONTACT_SHEET_NAME = "attack_sword_01_onehand_up_visible_blade_diagnostic_v21.png"
BLADE_CLEARANCE_PART_IDS = (
    "blade",
    "highlight",
    "tip",
)
HILT_OCCLUSION_PART_IDS = (
    "guard",
    "grip",
    "pommel",
)
MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = 1.0
ALLOW_HILT_OCCLUSION_BEHIND_HEAD = True
REQUIRE_ZERO_EDGE_ALPHA = True

SOURCE_FAILED_RUN_ID = 30753294334
SOURCE_FAILED_ARTIFACT_ID = 8835191378
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "97a04736c2b482477dee21a70af99d51362c767f45a71ea6f27446a8ab197636"
)
SOURCE_FAILURE = (
    "pass20 exhausted 6820 candidates for onehand_up f05 because the legacy "
    "clearance check included the hand-attached guard, grip and pommel; all "
    "candidates reported exactly zero clearance before any PNG was rendered"
)
TECHNICAL_FAILED_RUN_ID = 30754498101
TECHNICAL_FAILED_ARTIFACT_ID = 8835541839
TECHNICAL_FAILED_ARTIFACT_SHA256 = (
    "5b19f1ece9ee8e74aa6708026e8f4f9b6c425819d11f5008d497c8a79fde02c7"
)
TECHNICAL_FAILURE = (
    "the first pass21 adapter matched legacy v06 object names while the active "
    "up-direction weapon uses v12 objects; filtering now uses stable weapon_part IDs"
)
