from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v15 import HUMAN_WARRIOR_M01_HEAD_V15


HUMAN_WARRIOR_M01_HEAD_V16 = replace(
    HUMAN_WARRIOR_M01_HEAD_V15,
    revision="v16",
    proxy_revision="v19",
)


def load_head_profile_v16(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V16.character_id:
        raise KeyError(f"No head v16 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V16.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V16
