from __future__ import annotations

from pathlib import Path


PLAYER_PATH = Path("scripts/game/player.gd")
PLAYER_COMBAT_PATH = Path("scripts/game/player_combat.gd")
TEST_PATH = Path("tests/test_human_warrior_runtime_animation_v02.gd")


def replace_once(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"expected one match in {path}, found {count}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    replace_once(
        PLAYER_PATH,
        '''\t_visual_facing_direction = direction.normalized()
\t_visual_motion_state = VISUAL_STATE_IDLE
''',
        '''\tvar normalized_attack_direction: Vector2 = direction.normalized()
\t# Synchronize both the authored visual and the production combat-facing state
\t# before enabling the lock. Subsequent external facing requests are ignored
\t# until the attack has completed.
\tif has_method("set_facing_direction"):
\t\tcall("set_facing_direction", normalized_attack_direction)
\telse:
\t\tset_visual_facing(normalized_attack_direction)
\t_visual_motion_state = VISUAL_STATE_IDLE
''',
    )
    replace_once(
        PLAYER_COMBAT_PATH,
        '''func set_facing_direction(direction: Vector2) -> void:
\tif direction.length_squared() <= 0.0001:
\t\treturn
''',
        '''func set_facing_direction(direction: Vector2) -> void:
\tif is_action_animation_locked():
\t\treturn
\tif direction.length_squared() <= 0.0001:
\t\treturn
''',
    )
    replace_once(
        TEST_PATH,
        '''\tif int(player.call(
\t\t"start_melee_attack_animation",
\t\tplayer.global_position + Vector2.LEFT * 64.0,
\t\tonehand_weapon,
\t\tCallable()
\t)) != -1:
\t\t_fail("A repeated attack was accepted while the first animation was active.")
\t\treturn
''',
        '''\tif int(player.call(
\t\t"start_melee_attack_animation",
\t\tplayer.global_position + Vector2.LEFT * 64.0,
\t\tonehand_weapon,
\t\tCallable()
\t)) != -1:
\t\t_fail("A repeated attack was accepted while the first animation was active.")
\t\treturn
\tplayer.call("set_facing_direction", Vector2.RIGHT)
\tif Vector2(player.call("get_facing_direction")).dot(Vector2.LEFT) < 0.99:
\t\t_fail("Facing changed while the one-handed attack lock was active.")
\t\treturn
''',
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
