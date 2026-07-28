from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v14 import HUMAN_WARRIOR_M01_HEAD_V14


HUMAN_WARRIOR_M01_HEAD_V15 = replace(
    HUMAN_WARRIOR_M01_HEAD_V14,
    revision="v15",
    proxy_revision="v18",
)


def load_head_profile_v15(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V15.character_id:
        raise KeyError(f"No head v15 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V15.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V15
