from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v16 import HUMAN_WARRIOR_M01_HEAD_V16


HUMAN_WARRIOR_M01_HEAD_V17 = replace(
    HUMAN_WARRIOR_M01_HEAD_V16,
    revision="v17",
    proxy_revision="v20",
)


def load_head_profile_v17(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V17.character_id:
        raise KeyError(f"No head v17 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V17.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V17
