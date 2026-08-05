from __future__ import annotations


CORRECTION_PASS = "v21_pass02"
DIRECTIONAL_CONTAINMENT_REVISION = (
    "twohand_overhead_directional_projection_containment_v21_pass02"
)
PROJECTION_SEARCH_STEP = 0.04
MINIMUM_SCREEN_PROJECTION = 0.44
REQUIRE_ZERO_EDGE_ALPHA = True
PRESERVE_ACTION_CURVES = True
PRESERVE_CHARACTER_LOCAL_ARC_ANGLE = True
PRESERVE_DOWN_PASS04_PIXELS = True

SOURCE_FAILED_RUN_ID = 30959167282
SOURCE_FAILED_ARTIFACT_ID = 8912382876
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "753eabbdf752674ab6b7c683d5cbc78305216a668267c1cd58c5c31deded8a18"
)
SOURCE_FAILURE = (
    "the first four-direction render preserved all approved down pass04 pixels "
    "and rendered left f01-f02, but the unchanged local overhead anticipation "
    "projected five alpha pixels onto the top edge at left f03"
)
