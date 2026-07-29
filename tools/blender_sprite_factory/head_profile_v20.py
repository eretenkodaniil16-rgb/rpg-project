from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v18 import HUMAN_WARRIOR_M01_HEAD_V18


HUMAN_WARRIOR_M01_HEAD_V20 = replace(
    HUMAN_WARRIOR_M01_HEAD_V18,
    revision="v20",
    proxy_revision="v23",
)


def load_head_profile_v20(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V20.character_id:
        raise KeyError(f"No head v20 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V20.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V20
