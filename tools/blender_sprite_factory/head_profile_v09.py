from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v08 import HUMAN_WARRIOR_M01_HEAD_V08


HUMAN_WARRIOR_M01_HEAD_V09 = replace(
    HUMAN_WARRIOR_M01_HEAD_V08,
    revision="v09",
    proxy_revision="v12",
)


def load_head_profile_v09(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V09.character_id:
        raise KeyError(f"No head v09 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V09.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V09
