from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v10 import HUMAN_WARRIOR_M01_HEAD_V10


HUMAN_WARRIOR_M01_HEAD_V11 = replace(
    HUMAN_WARRIOR_M01_HEAD_V10,
    revision="v11",
    proxy_revision="v14",
)


def load_head_profile_v11(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V11.character_id:
        raise KeyError(f"No head v11 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V11.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V11
