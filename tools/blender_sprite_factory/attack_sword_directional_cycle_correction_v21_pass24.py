from __future__ import annotations


CORRECTION_PASS = "v21_pass24"
ONEHAND_UP_FRONT_DEPTH_DIAGNOSTIC_REVISION = (
    "onehand_up_f05_f08_front_depth_branch_v21_pass24"
)
DIAGNOSTIC_SCENE_KEY = "attack_sword_onehand_up_front_depth_diagnostic_v21"
CONTACT_SHEET_NAME = "attack_sword_01_onehand_up_front_depth_diagnostic_v21.png"
FLIP_CAMERA_DEPTH_BRANCH = True
REQUIRE_ZERO_EDGE_ALPHA = True

SOURCE_FAILED_RUN_ID = 30758735419
SOURCE_FAILED_ARTIFACT_ID = 8836789913
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "30e4b4a8ed0e76440605bd490954ff185a6ba441783cf9a43d183d8dbf9e3e91"
)
SOURCE_FAILURE = (
    "pass23 exhausted all 6820 bounded arm, screen-projection and angle "
    "candidates for onehand_up f05 because the trajectory planner preserved "
    "the source camera-depth branch and kept the blade behind the head"
)
