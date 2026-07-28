from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v12 import HUMAN_WARRIOR_M01_HEAD_V12


HUMAN_WARRIOR_M01_HEAD_V13 = replace(
    HUMAN_WARRIOR_M01_HEAD_V12,
    revision="v13",
    proxy_revision="v16",
)


def load_head_profile_v13(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V13.character_id:
        raise KeyError(f"No head v13 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V13.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V13
