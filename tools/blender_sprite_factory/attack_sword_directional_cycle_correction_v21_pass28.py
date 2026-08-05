from __future__ import annotations

CORRECTION_PASS = "v21_pass28"
TWOHAND_UP_FALLBACK_REVISION = (
    "twohand_up_on_demand_depth_search_v21_pass28"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAMES = tuple(range(1, 9))

FALLBACK_ERROR_PREFIXES = (
    "attack sword directional v21 pass02 found no geometry-safe candidate",
    "attack sword directional v21 pass02 found no export-contained candidate",
)
FULLY_OCCLUDED_CANDIDATES_ARE_REJECTED = True
USE_MINIMUM_VISIBLE_BLADE_SAMPLE_GUARD = True

SOURCE_FAILED_RUN_ID = 30847584866
SOURCE_FAILED_ARTIFACT_ID = 8870099701
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "71927d198e4d665a8c484e49fdd08b6c983193d5eff461fa9369f5a912547173"
)
SOURCE_FAILURE = (
    "raw depth-aware clearance raised when a candidate had no visible blade "
    "samples for twohand_center_high/up/f01"
)
