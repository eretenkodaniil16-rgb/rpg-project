from __future__ import annotations


CORRECTION_PASS = "v21_pass02"
OVERHEAD_WEAPON_ARC_REVISION = "centered_vertical_weapon_arc_v21_pass02"
TARGET_ACTION_ID = "attack_sword_01_twohand_down_overhead_v21"
TARGET_DIRECTION = "down"
TARGET_FRAMES = (2, 3, 4, 5, 6, 7)

# Screen-space offsets are measured from the approved f01 guard sword axis.
# f02-f03 keep the blade vertical above the hands; f04-f05 reverse the
# blade axis for the downward contact and follow-through.
SCREEN_OFFSET_DEGREES_BY_FRAME = {
    2: 0.0,
    3: 0.0,
    4: 180.0,
    5: 180.0,
    6: 170.0,
    7: 20.0,
}
SCREEN_PROJECTION_BY_FRAME = {
    2: 0.96,
    3: 0.96,
    4: 0.96,
    5: 0.96,
    6: 0.92,
    7: 0.88,
}

TWOHAND_OBJECT_NAMES = (
    "combat_twohand_high_v06_blade",
    "combat_twohand_high_v06_highlight",
    "combat_twohand_high_v06_tip",
    "combat_twohand_high_v06_guard",
    "combat_twohand_high_v06_grip",
    "combat_twohand_high_v06_pommel",
)
BLADE_OBJECT_NAME = "combat_twohand_high_v06_blade"
GRIP_OBJECT_NAME = "combat_twohand_high_v06_grip"

USE_REFERENCE_DEPTH_SIGN = True
REQUIRE_ZERO_EDGE_ALPHA = True
PRESERVE_F01_F08 = True
PRESERVE_BODY_ACTION = True
PRESERVE_WEAPON_GEOMETRY = True
