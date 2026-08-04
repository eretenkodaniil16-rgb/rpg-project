from __future__ import annotations


CORRECTION_PASS = "v21_pass04"
OVERHEAD_WEAPON_ARC_REVISION = "centered_vertical_weapon_arc_f03_margin_v21_pass04"
TARGET_FRAME = 3
F03_SCREEN_PROJECTION = 0.80
REQUIRE_ZERO_EDGE_ALPHA = True
PRESERVE_F02 = True
PRESERVE_F04_F07_PROFILE = True
PRESERVE_BODY_ACTION = True
PRESERVE_WEAPON_GEOMETRY = True

SOURCE_FAILED_RUN_ID = 30955975264
SOURCE_FAILED_ARTIFACT_ID = 8911224047
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "8e791d9ef7f70bcc488499f12232d8dcdffa68cbe2409884c02d0b4bdbf748db"
)
SOURCE_FAILURE = (
    "pass03 moved the raw f03 alpha bbox from y=0 to y=8, but the normalized "
    "96x96 frame still touched the top edge at four alpha pixels after fixed "
    "scale and baseline anchoring"
)
