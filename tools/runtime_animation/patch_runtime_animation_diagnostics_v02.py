from __future__ import annotations

from pathlib import Path


PATH = Path("tests/test_human_warrior_runtime_animation_v02.gd")
OLD_ONEHAND = '''\tif sprite.animation != &"combat_idle_onehand_left":
\t\t_fail("One-handed attack did not return to the matching combat idle.")
\t\treturn
'''
NEW_ONEHAND = '''\tif sprite.animation != &"combat_idle_onehand_left":
\t\t_fail(
\t\t\t"One-handed post-attack mismatch: animation=%s playing=%s frame=%d weapon=%s debug=%s"
\t\t\t% [
\t\t\t\tstr(sprite.animation),
\t\t\t\tstr(sprite.is_playing()),
\t\t\t\tsprite.frame,
\t\t\t\truntime_character.equipped_weapon_id,
\t\t\t\tstr(player.call("get_visual_debug_state"))
\t\t\t]
\t\t)
\t\treturn
'''
OLD_TWOHAND = '''\tif sprite.animation != &"combat_idle_twohand_up":
\t\t_fail("Two-handed attack did not return to the matching combat idle.")
\t\treturn
'''
NEW_TWOHAND = '''\tif sprite.animation != &"combat_idle_twohand_up":
\t\t_fail(
\t\t\t"Two-handed post-attack mismatch: animation=%s playing=%s frame=%d weapon=%s debug=%s"
\t\t\t% [
\t\t\t\tstr(sprite.animation),
\t\t\t\tstr(sprite.is_playing()),
\t\t\t\tsprite.frame,
\t\t\t\truntime_character.equipped_weapon_id,
\t\t\t\tstr(player.call("get_visual_debug_state"))
\t\t\t]
\t\t)
\t\treturn
'''


def replace_once(content: str, old: str, new: str) -> str:
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"expected one match, found {count}")
    return content.replace(old, new, 1)


def main() -> int:
    content = PATH.read_text(encoding="utf-8")
    content = replace_once(content, OLD_ONEHAND, NEW_ONEHAND)
    content = replace_once(content, OLD_TWOHAND, NEW_TWOHAND)
    PATH.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
