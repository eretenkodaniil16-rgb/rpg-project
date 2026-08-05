from __future__ import annotations


CORRECTION_PASS = "v21_pass15"
TWOHAND_LEFT_TAIL_REVISION = "twohand_left_tail_action_projection_v21_pass15"
TARGET_ACTION_ID = "attack_sword_01_twohand_left_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "left"
TARGET_FRAMES = (5, 6, 7, 8)
SOURCE_FRAME_BY_TARGET = {
    5: 4,
    6: 5,
    7: 8,
    8: 1,
}
TARGET_BONES = (
    "upper_arm.L",
    "forearm.L",
    "hand.L",
    "upper_arm.R",
    "forearm.R",
    "hand.R",
)
SELECTED_ARM_BLEND_BY_FRAME = {
    5: 0.40,
    6: 0.0,
    7: 0.0,
    8: 0.0,
}
SELECTED_REQUESTED_SCREEN_PROJECTION_BY_FRAME = {
    5: 0.95,
    6: 0.95,
    7: 0.95,
    8: 0.95,
}
SELECTED_APPLIED_SCREEN_PROJECTION_BY_FRAME = {
    5: 0.95,
    6: 0.7912463508259105,
    7: 0.4668173488032021,
    8: 0.6569491343763803,
}
SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME = {
    5: -16.0,
    6: 0.0,
    7: 0.0,
    8: 8.0,
}
SELECTED_HEAD_CLEARANCE_PIXELS_BY_FRAME = {
    5: 1.314474105834961,
    6: 4.126619338989258,
    7: 5.058755195021977,
    8: 1.026265789105252,
}
SELECTED_CAMERA_MARGIN_PIXELS_BY_FRAME = {
    5: 16.339808464050293,
    6: 15.241540431976318,
    7: 28.960567474365234,
    8: 16.61630630493164,
}
SELECTED_ATTEMPT_BY_FRAME = {
    5: 741,
    6: 1,
    7: 1,
    8: 2,
}
MIN_HEAD_CLEARANCE_PIXELS = 1.0
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True

DIAGNOSTIC_RUN_ID = 30749917970
DIAGNOSTIC_ARTIFACT_ID = 8834141095
DIAGNOSTIC_ARTIFACT_SHA256 = (
    "745de5cef991cd5d575ac3c2c43a1b785903fd56d74803af1207fbdcc04c4f29"
)
DIAGNOSTIC_FRAME_SIZE = (96, 96)
DIAGNOSTIC_ALPHA_BBOX_BY_FRAME = {
    5: (14, 20, 88, 92),
    6: (8, 17, 73, 92),
    7: (25, 17, 68, 92),
    8: (30, 9, 65, 92),
}
DIAGNOSTIC_EDGE_ALPHA_COUNTS_BY_FRAME = {
    5: {"left": 0, "right": 0, "top": 0, "bottom": 0},
    6: {"left": 0, "right": 0, "top": 0, "bottom": 0},
    7: {"left": 0, "right": 0, "top": 0, "bottom": 0},
    8: {"left": 0, "right": 0, "top": 0, "bottom": 0},
}

SOURCE_FAILED_RUN_ID = 30748869155
SOURCE_FAILED_ARTIFACT_ID = 8833935925
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "e3abbf704854eb4c24c60a1d4b086646019495609311d2d16c59d941607a1c50"
)
SOURCE_FAILURE = (
    "pass13 validated twohand_left f02-f04 and then found no geometry-safe "
    "candidate for twohand_center_high/left/f05"
)
