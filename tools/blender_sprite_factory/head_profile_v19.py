from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v18 import HUMAN_WARRIOR_M01_HEAD_V18


HUMAN_WARRIOR_M01_HEAD_V19 = replace(
    HUMAN_WARRIOR_M01_HEAD_V18,
    revision="v19",
    proxy_revision="v22",
)


def load_head_profile_v19(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V19.character_id:
        raise KeyError(f"No head v19 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V19.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V19
