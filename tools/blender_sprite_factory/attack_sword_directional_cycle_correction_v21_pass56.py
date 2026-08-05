from __future__ import annotations


CORRECTION_PASS = "v21_pass56"
TWOHAND_UP_FRONT_DEPTH_CONTRACT_REVISION = (
    "twohand_up_front_depth_short_idproperty_v21_pass56"
)

SHORT_CLEARANCE_SCENE_KEY = "atk_sword_v21_p56_clearance_ok"
MAX_BLENDER_IDPROPERTY_NAME_LENGTH = 63

SOURCE_FAILED_RUN_ID = 30943701293
SOURCE_FAILED_ARTIFACT_ID = 8907059656
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "401faa170cbb113a86411ffc544c9433b815a40d0c1b9722b223ecce747b9047"
)
SOURCE_FAILED_COMMIT = "0dcf936fdf96eaa40b4aaa8065bf6f7890ca07ec"
SOURCE_FAILURE = (
    "pass55 rendered all 64 frames with twohand_up f04 and f05 on the front "
    "depth branch and zero edge alpha, then failed only because a diagnostic "
    "Blender scene IDProperty name exceeded the 63-character limit"
)

VISUAL_OUTPUT_CHANGED_FROM_PASS55 = False
FRONT_DEPTH_SELECTION_PRESERVED = True
BOUNDARY_FIX_PRESERVED = True
