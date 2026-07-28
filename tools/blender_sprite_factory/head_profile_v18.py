from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v17 import HUMAN_WARRIOR_M01_HEAD_V17


HUMAN_WARRIOR_M01_HEAD_V18 = replace(
    HUMAN_WARRIOR_M01_HEAD_V17,
    revision="v18",
    proxy_revision="v21",
)


def load_head_profile_v18(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V18.character_id:
        raise KeyError(f"No head v18 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V18.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V18
