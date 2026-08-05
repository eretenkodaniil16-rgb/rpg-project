from __future__ import annotations


CORRECTION_PASS = "v21_pass25"
ONEHAND_UP_F05_ARM_DIAGNOSTIC_REVISION = (
    "onehand_up_f05_right_arm_lateral_clearance_v21_pass25"
)
DIAGNOSTIC_SCENE_KEY = "attack_sword_onehand_up_f05_arm_diagnostic_v21"
CONTACT_SHEET_NAME = "attack_sword_01_onehand_up_f05_arm_diagnostic_v21.png"
TARGET_FRAMES = (5,)
SEARCH_PROJECTIONS = (0.95, 0.78, 0.62, 0.46, 0.30, 0.18)
SEARCH_ANGLE_OFFSETS = (
    0.0,
    -12.0,
    12.0,
    -24.0,
    24.0,
    -36.0,
    36.0,
    -48.0,
    48.0,
    -60.0,
    60.0,
    -72.0,
    72.0,
    -84.0,
    84.0,
    -90.0,
    90.0,
)
ARM_PROFILE_CANDIDATES = (
    {"source_blend": 0.0, "scale": 0.0, "sweep_sign": 1.0, "lift_sign": -1.0},
    {"source_blend": 0.0, "scale": 0.5, "sweep_sign": 1.0, "lift_sign": -1.0},
    {"source_blend": 0.0, "scale": 0.5, "sweep_sign": -1.0, "lift_sign": -1.0},
    {"source_blend": 0.0, "scale": 1.0, "sweep_sign": 1.0, "lift_sign": -1.0},
    {"source_blend": 0.0, "scale": 1.0, "sweep_sign": -1.0, "lift_sign": -1.0},
    {"source_blend": 0.0, "scale": 1.5, "sweep_sign": 1.0, "lift_sign": -1.0},
    {"source_blend": 0.0, "scale": 1.5, "sweep_sign": -1.0, "lift_sign": -1.0},
    {"source_blend": 0.5, "scale": 0.5, "sweep_sign": 1.0, "lift_sign": -1.0},
    {"source_blend": 0.5, "scale": 0.5, "sweep_sign": -1.0, "lift_sign": -1.0},
    {"source_blend": 0.5, "scale": 1.0, "sweep_sign": 1.0, "lift_sign": -1.0},
    {"source_blend": 0.5, "scale": 1.0, "sweep_sign": -1.0, "lift_sign": -1.0},
    {"source_blend": 0.0, "scale": 1.0, "sweep_sign": 1.0, "lift_sign": 1.0},
    {"source_blend": 0.0, "scale": 1.0, "sweep_sign": -1.0, "lift_sign": 1.0},
)
BASE_BONE_DELTAS_DEGREES = {
    "upper_arm.R": (-26.0, 14.0, 0.0),
    "forearm.R": (-40.0, 20.0, 0.0),
    "hand.R": (-14.0, 8.0, 0.0),
}
REQUIRE_ZERO_EDGE_ALPHA = True

SOURCE_FAILED_RUN_ID = 30758959479
SOURCE_FAILED_ARTIFACT_ID = 8836881277
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "c42c8107d1213c7f2ebc0251f3b0f6bdb4d2f4f3da0e0e3891e11b3fadd96284"
)
SOURCE_FAILURE = (
    "pass24 moved the blade onto the front camera-depth branch but all 6820 "
    "candidates still crossed the head silhouette because the f05 grip pivot "
    "remained too close to the head; a local right-arm correction is required"
)
