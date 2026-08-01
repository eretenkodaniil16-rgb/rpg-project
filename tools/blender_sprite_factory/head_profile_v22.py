from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v21 import HUMAN_WARRIOR_M01_HEAD_V21


HUMAN_WARRIOR_M01_HEAD_V22 = replace(
    HUMAN_WARRIOR_M01_HEAD_V21,
    revision="v22",
    proxy_revision="v25",
)


def load_head_profile_v22(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V22.character_id:
        raise KeyError(f"No head v22 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V22.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V22
