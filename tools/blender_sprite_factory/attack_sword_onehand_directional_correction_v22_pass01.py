from __future__ import annotations


CORRECTION_PASS = "v22_pass01"
ONEHAND_DIRECTIONAL_REVISION = (
    "onehand_directional_local_readability_v22_pass01"
)
SOURCE_MASTER_ACTION_ID = "attack_sword_01_onehand_down_v20"
TARGET_DIRECTIONS = ("left", "right", "up")
TARGET_ACTION_ID_BY_DIRECTION = {
    "left": "attack_sword_01_onehand_left_v21",
    "right": "attack_sword_01_onehand_right_v21",
    "up": "attack_sword_01_onehand_up_v21",
}
TARGET_FRAMES = (4, 5, 6)
FRAME_WEIGHTS = {
    4: 0.45,
    5: 1.00,
    6: 0.55,
}

# Extremely small action-local rotations only. Direction comes from the real
# rig rotation; these deltas only preserve weapon-arm readability and remove
# local projection collisions without changing the attack character.
BONE_DELTAS_DEGREES_BY_DIRECTION = {
    "left": {
        "upper_arm.R": (0.0, 1.5, -0.75),
        "forearm.R": (0.0, 2.0, -1.0),
        "hand.R": (0.0, 0.75, -1.25),
    },
    "right": {
        "upper_arm.R": (0.25, -1.5, 0.75),
        "forearm.R": (0.25, -2.0, 1.0),
        "hand.R": (0.0, -0.75, 1.25),
    },
    "up": {
        "upper_arm.R": (1.5, 0.25, -0.75),
        "forearm.R": (2.0, 0.25, -1.0),
        "hand.R": (1.0, 0.0, -1.25),
    },
}

APPROVED_TWOHAND_BASELINE_COMMIT = (
    "3131225654ed018a0b4e632ba663d7ad60480fb6"
)
APPROVED_TWOHAND_WORKFLOW_RUN_ID = 30962732089
APPROVED_TWOHAND_ARTIFACT_ID = 8913799114
APPROVED_TWOHAND_ARTIFACT_SHA256 = (
    "5c3f5ede5f50c72952b7f52d67b1e7d2e51d52aba83d6cd074a55c07e5262f38"
)

PRESERVE_SOURCE_FCURVE_TIMING = True
PRESERVE_DOWN_PIXELS = True
PRESERVE_TWOHAND_BASELINE = True
ROOT_TRANSLATION_USED = False
MIRRORING_USED = False
NEGATIVE_SCALE_USED = False
WEAPON_GEOMETRY_CHANGED = False
MATERIALS_CHANGED = False
