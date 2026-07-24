from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "scripts/game/game_srd_combat.gd"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


text = PATH.read_text(encoding="utf-8")
text = replace_once(
    text,
    '''func _process(delta: float) -> void:
\tsuper._process(delta)
\t_sync_player_damage_traits()
\t_refresh_srd_interface()
''',
    '''func _process(delta: float) -> void:
\tsuper._process(delta)
\tif _spell_area_targeting_active and (GameState.input_locked or _any_overlay_visible()):
\t\t_cancel_spell_area_targeting()
\t_sync_player_damage_traits()
\t_refresh_srd_interface()
''',
    "overlay cleanup",
)
text = replace_once(
    text,
    '''\t\t\ttarget.call("receive_player_attack", result, false)
\t_set_combat_busy(false)
''',
    '''\t\t\ttarget.call("receive_player_attack", result, false)
\t\t\tif target.has_method("get_current_health") and int(target.call("get_current_health")) <= 0:
\t\t\t\t_release_grapples_for(target)
\t_set_combat_busy(false)
''',
    "area death cleanup",
)
text = replace_once(
    text,
    '''\tvar combat_trigger: Node = targets[0] if not targets.is_empty() else null
\t_cancel_spell_area_targeting()
\tif not _turn_system.active and is_instance_valid(combat_trigger):
\t\t_start_turn_based_combat(combat_trigger)
''',
    '''\tvar combat_trigger: Node = null
\tfor target: Node in targets:
\t\tif _target_is_valid(target):
\t\t\tcombat_trigger = target
\t\t\tbreak
\t_cancel_spell_area_targeting()
\tif not _turn_system.active and is_instance_valid(combat_trigger):
\t\t_start_turn_based_combat(combat_trigger)
''',
    "living combat trigger",
)
text = replace_once(
    text,
    '''func _advance_combat_turn() -> void:
\tif _turn_system.active:
''',
    '''func _advance_combat_turn() -> void:
\tif _spell_area_targeting_active:
\t\t_cancel_spell_area_targeting()
\tif _turn_system.active:
''',
    "turn cleanup",
)
PATH.write_text(text, encoding="utf-8")
print("Spell area runtime cleanup applied.")
