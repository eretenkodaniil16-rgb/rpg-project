from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v13 import HUMAN_WARRIOR_M01_HEAD_V13


HUMAN_WARRIOR_M01_HEAD_V14 = replace(
    HUMAN_WARRIOR_M01_HEAD_V13,
    revision="v14",
    proxy_revision="v17",
)


def load_head_profile_v14(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V14.character_id:
        raise KeyError(f"No head v14 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V14.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V14
