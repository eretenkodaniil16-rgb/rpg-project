from __future__ import annotations

from pathlib import Path


PATH = Path("tests/test_human_warrior_runtime_animation_v02.gd")


def replace_once(content: str, old: str, new: str) -> str:
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"expected one match, found {count}: {old!r}")
    return content.replace(old, new, 1)


def main() -> int:
    content = PATH.read_text(encoding="utf-8")
    anchor = '''\tvar body: Polygon2D = player.get_node_or_null("Body") as Polygon2D
'''
    replacement = '''\tvar runtime_character: PlayerCharacter = game_state.get("player_character") as PlayerCharacter
\tif runtime_character == null:
\t\t_fail("Production scene has no runtime player character.")
\t\treturn
\tvar body: Polygon2D = player.get_node_or_null("Body") as Polygon2D
'''
    content = replace_once(content, anchor, replacement)
    content = content.replace('hero.equipped_weapon_id = ', 'runtime_character.equipped_weapon_id = ')
    content = replace_once(content, 'hero.race_id = "elf"', 'runtime_character.race_id = "elf"')
    PATH.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
