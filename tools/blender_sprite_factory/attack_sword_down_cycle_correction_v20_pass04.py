from __future__ import annotations


CORRECTION_PASS = "v20_pass04"
ONEHAND_CONTAINMENT_REVISION = "export_space_positive_extension_v20_pass04"
TARGET_ANIMATION_ID = "attack_sword_01_onehand_down_v20"
TARGET_FRAME = 6
ANGLE_CANDIDATES_DEGREES = (
    42.0,
    44.0,
    46.0,
    48.0,
    50.0,
    52.0,
    54.0,
    56.0,
    58.0,
    60.0,
)
MIN_HEAD_CLEARANCE_PIXELS = 4.0
REQUIRE_ZERO_EDGE_ALPHA = True
KNOWN_FAILED_RUN_ID = 30720688002
KNOWN_FAILED_ARTIFACT_ID = 8824976123
KNOWN_FAILED_ARTIFACT_SHA256 = (
    "6cfffc93c33e13db8e3bcc66991de918790e5e06458fc8024c6d72367da0dbf1"
)
KNOWN_FAILED_OFFSET_MIN_DEGREES = -40.0
KNOWN_FAILED_OFFSET_MAX_DEGREES = 40.0


def validate_attack_sword_down_cycle_v20_pass04() -> None:
    if TARGET_FRAME != 6:
        raise ValueError("v20 pass04 must correct only the rebound frame")
    if not ANGLE_CANDIDATES_DEGREES:
        raise ValueError("v20 pass04 requires positive extension candidates")
    if tuple(sorted(set(ANGLE_CANDIDATES_DEGREES))) != ANGLE_CANDIDATES_DEGREES:
        raise ValueError("v20 pass04 candidates must be unique and increasing")
    if ANGLE_CANDIDATES_DEGREES[0] <= KNOWN_FAILED_OFFSET_MAX_DEGREES:
        raise ValueError("v20 pass04 must not repeat pass03 failed candidates")
    if ANGLE_CANDIDATES_DEGREES[-1] > 60.0:
        raise ValueError("v20 pass04 exceeds the bounded artistic search range")
    if MIN_HEAD_CLEARANCE_PIXELS < 4.0:
        raise ValueError("v20 pass04 head clearance is weaker than the locked contract")
    if not REQUIRE_ZERO_EDGE_ALPHA:
        raise ValueError("v20 pass04 must preserve the zero-edge-alpha contract")


validate_attack_sword_down_cycle_v20_pass04()
