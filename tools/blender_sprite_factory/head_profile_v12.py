from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v11 import HUMAN_WARRIOR_M01_HEAD_V11


HUMAN_WARRIOR_M01_HEAD_V12 = replace(
    HUMAN_WARRIOR_M01_HEAD_V11,
    revision="v12",
    proxy_revision="v15",
)


def load_head_profile_v12(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V12.character_id:
        raise KeyError(f"No head v12 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V12.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V12
