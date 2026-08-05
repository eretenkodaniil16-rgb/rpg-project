from __future__ import annotations

from pathlib import Path


PATH = Path("scripts/game/player.gd")
OLD = '''func _on_character_sprite_animation_finished() -> void:
\tif not _action_animation_locked or not is_instance_valid(_character_sprite):
\t\treturn
\tif _character_sprite.animation != _active_attack_animation:
\t\treturn
\t_finish_melee_attack(_active_attack_sequence_id)
'''
NEW = '''func _on_character_sprite_animation_finished() -> void:
\tif not _action_animation_locked or not is_instance_valid(_character_sprite):
\t\treturn
\tif _character_sprite.animation != _active_attack_animation:
\t\treturn
\t# AnimatedSprite2D completes its internal non-loop transition after emitting
\t# animation_finished. Finalizing synchronously can restore the finished attack
\t# over the combat idle selected by _refresh_visual_animation(). Keep the local
\t# action lock until the deferred call establishes the post-attack state.
\tcall_deferred("_finish_melee_attack", _active_attack_sequence_id)
'''


def main() -> int:
    content = PATH.read_text(encoding="utf-8")
    count = content.count(OLD)
    if count != 1:
        raise RuntimeError(f"expected one animation_finished handler, found {count}")
    PATH.write_text(content.replace(OLD, NEW, 1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
