from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v20 import HUMAN_WARRIOR_M01_HEAD_V20


HUMAN_WARRIOR_M01_HEAD_V21 = replace(
    HUMAN_WARRIOR_M01_HEAD_V20,
    revision="v21",
    proxy_revision="v24",
)


def load_head_profile_v21(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V21.character_id:
        raise KeyError(f"No head v21 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V21.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V21
