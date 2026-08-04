from __future__ import annotations


CORRECTION_PASS = "v21_pass03"
OVERHEAD_WEAPON_ARC_REVISION = "centered_vertical_weapon_arc_f03_contained_v21_pass03"
TARGET_FRAME = 3
F03_SCREEN_PROJECTION = 0.88
REQUIRE_ZERO_EDGE_ALPHA = True
PRESERVE_F02 = True
PRESERVE_F04_F07_PROFILE = True
PRESERVE_BODY_ACTION = True
PRESERVE_WEAPON_GEOMETRY = True

SOURCE_FAILED_RUN_ID = 30954695867
SOURCE_FAILED_ARTIFACT_ID = 8910883651
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "7219fbef898ad1f389cd9689f1afe5baafcecb14ada49b3b973e571666fc03d2"
)
SOURCE_FAILURE = (
    "pass02 established the correct centered vertical overhead wind-up, but "
    "f03 touched the top canvas edge at four alpha pixels with projection 0.96"
)
