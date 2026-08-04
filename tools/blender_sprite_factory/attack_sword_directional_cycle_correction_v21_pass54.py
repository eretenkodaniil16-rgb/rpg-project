from __future__ import annotations


CORRECTION_PASS = "v21_pass54"
TWOHAND_UP_INTEGRATED_ACTION_REVISION = (
    "twohand_up_selected_action_and_export_profile_v21_pass54"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAMES = (1, 2, 3, 4, 5, 6, 7, 8)
ACTION_CHANGED_FRAMES = (1, 2, 3, 7, 8)
TARGET_BONES = (
    "upper_arm.L",
    "forearm.L",
    "hand.L",
    "upper_arm.R",
    "forearm.R",
    "hand.R",
)

# Exact local Euler deltas measured from the pass53 selected render manifest.
ACTION_BONE_DELTAS_DEGREES_BY_FRAME = {
    1: {
        "upper_arm.L": (28.799999776904638, 0.0, 9.59999992563488),
        "forearm.L": (27.600000426530514, 0.0, -8.399999550732378),
        "hand.L": (21.599999192348243, 0.0, -4.79999996281744),
        "upper_arm.R": (28.799999776904638, 0.0, -4.800000475081627),
        "forearm.R": (27.600000426530514, 0.0, 13.199999641615864),
        "hand.R": (21.599999960744523, 0.0, 9.600000181766973),
    },
    2: {
        "upper_arm.L": (16.048000054978772, 0.0, 4.176000198170057),
        "forearm.L": (17.183999849810963, 0.0, -7.8719997170394524),
        "hand.L": (12.720000285664357, 0.0, -4.544000139824107),
        "upper_arm.R": (16.048000054978772, 0.0, -4.543999862347673),
        "forearm.R": (17.183999849810963, 0.0, 7.503999284465556),
        "hand.R": (12.720000114909627, 0.0, 4.176000027415328),
    },
    3: {
        "upper_arm.L": (37.199999327637016, 0.0, 20.40000022617226),
        "forearm.L": (34.80000062688876, 0.0, -5.9999998254557525),
        "hand.L": (27.599999402002133, 0.0, 0.0),
        "upper_arm.R": (37.199999327637016, 0.0, 0.0),
        "forearm.R": (34.80000062688876, 0.0, 26.400000691958244),
        "hand.R": (27.599999914266323, 0.0, 20.40000022617226),
    },
    7: {
        "upper_arm.L": (3.951999875471258, 0.0, 1.3520000130056875),
        "forearm.L": (3.5359999469956382, 0.0, -0.9360000738578973),
        "hand.L": (2.9119999262161613, 0.0, -0.5199999959718893),
        "upper_arm.R": (3.951999875471258, 0.0, -0.5200000600049128),
        "forearm.R": (3.5359999469956382, 0.0, 1.768000101563866),
        "hand.R": (2.9119999262161613, 0.0, 1.352000023677858),
    },
    8: {
        "upper_arm.L": (13.951999669941543, 0.0, 4.351999744306664),
        "forearm.L": (15.535999832694896, 0.0, -5.935998733121253),
        "hand.L": (10.912000077688639, 0.0, -3.5199999940771303),
        "upper_arm.R": (13.951999669941543, 0.0, -3.520000314242248),
        "forearm.R": (15.535999832694896, 0.0, 6.767999443846139),
        "hand.R": (10.911999650801816, 0.0, 4.3520000111109285),
    },
}

# Frames with explicit depth/projection selected by the diagnostic reviews.
PROJECTED_WEAPON_PROFILE_BY_FRAME = {
    1: {"depth_branch": "source", "offset_degrees": 0.0, "projection": 0.30},
    2: {"depth_branch": "flipped", "offset_degrees": 0.0, "projection": 0.40},
    3: {"depth_branch": "source", "offset_degrees": 0.0, "projection": 0.25},
    7: {"depth_branch": "source", "offset_degrees": 60.0, "projection": 0.90},
    8: {"depth_branch": "source", "offset_degrees": 48.0, "projection": 0.90},
}
EXPECTED_SOURCE_PROJECTION_BY_FRAME = {
    1: 0.9441554552150095,
    2: 0.8788323960048797,
    3: 0.9991638994289267,
    7: 0.931707515535577,
    8: 0.9581097719792748,
}

# These frames retain the source depth/projection and rotate only in screen space.
ANGLE_ONLY_WEAPON_OFFSET_DEGREES_BY_FRAME = {
    4: 32.0,
    5: 0.0,
    6: 30.0,
}

CAMERA_SHIFT_X_BY_FRAME = {
    1: 0.0,
    2: 0.0,
    3: 0.0,
    4: -0.06,
    5: 0.0,
    6: -0.01,
    7: -0.07,
    8: 0.0,
}
CAMERA_SHIFT_Y_BY_FRAME = {
    1: 0.0,
    2: 0.0,
    3: 0.02,
    4: 0.0,
    5: 0.0,
    6: 0.0,
    7: 0.0,
    8: 0.0,
}

REQUIRE_ZERO_EDGE_ALPHA = True
SOURCE_SELECTED_RUN_ID = 30909429195
SOURCE_SELECTED_ARTIFACT_ID = 8892651912
SOURCE_SELECTED_ARTIFACT_SHA256 = (
    "e14b8aeaf35b3b4a713e6c2d4c54140257f62a2958fb1cd28b20803f0df2c15c"
)
SOURCE_SELECTED_COMMIT = "154db73428f25b343ae0e35fc0f48a1db52584f9"
SOURCE_SELECTED_FINDING = (
    "pass53 rendered the complete twohand_up f01-f08 cycle at 96x96 RGBA with "
    "a common baseline and zero alpha pixels on every canvas edge; pass54 "
    "moves the measured arm poses into Action data and retains only rigid "
    "weapon transforms plus temporary per-frame camera overscan in export"
)
