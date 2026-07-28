from __future__ import annotations

from dataclasses import replace

from head_profile import HeadProfile
from head_profile_v09 import HUMAN_WARRIOR_M01_HEAD_V09


HUMAN_WARRIOR_M01_HEAD_V10 = replace(
    HUMAN_WARRIOR_M01_HEAD_V09,
    revision="v10",
    proxy_revision="v13",
)


def load_head_profile_v10(character_id: str) -> HeadProfile:
    if character_id != HUMAN_WARRIOR_M01_HEAD_V10.character_id:
        raise KeyError(f"No head v10 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_HEAD_V10.assert_valid()
    return HUMAN_WARRIOR_M01_HEAD_V10
