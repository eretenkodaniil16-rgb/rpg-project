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
    '''var _pending_area_aim_cell: Vector2i = Vector2i.ZERO
var _spell_area_confirm_button: Button
var _spell_area_cancel_button: Button
''',
    '''var _pending_area_aim_cell: Vector2i = Vector2i.ZERO
var _pending_area_direction: Vector2 = Vector2.RIGHT
var _spell_area_confirmation_in_progress: bool = false
var _spell_area_confirm_button: Button
var _spell_area_cancel_button: Button
''',
    "review state fields",
)
text = replace_once(
    text,
    '''\t_pending_area_spell = ability.duplicate(true)
\t_spell_area_targeting_active = true
\t_spell_area_confirm_button.show()
\t_spell_area_cancel_button.show()
''',
    '''\t_pending_area_spell = ability.duplicate(true)
\t_spell_area_targeting_active = true
\t_spell_area_confirmation_in_progress = false
\t_spell_area_confirm_button.disabled = false
\t_spell_area_cancel_button.disabled = false
\t_spell_area_confirm_button.show()
\t_spell_area_cancel_button.show()
''',
    "begin review state",
)
text = replace_once(
    text,
    '''\tvar area: Dictionary = _pending_area_spell.get("area", {}) as Dictionary
\tvar caster_cell: Vector2i = grid.world_to_cell(player.global_position)
\tvar aim_cell: Vector2i = grid.world_to_cell(world_position)
\tif not grid.is_cell_valid(aim_cell):
\t\treturn
\tif str(area.get("origin", "point")) != "self":
''',
    '''\tvar area: Dictionary = _pending_area_spell.get("area", {}) as Dictionary
\tvar origin_mode: String = str(area.get("origin", "point"))
\tvar caster_cell: Vector2i = grid.world_to_cell(player.global_position)
\tvar aim_cell: Vector2i = grid.world_to_cell(world_position)
\tif not grid.is_cell_valid(aim_cell):
\t\treturn
\tif origin_mode != "self":
''',
    "origin mode",
)
text = replace_once(
    text,
    '''\tif aim_cell == caster_cell:
\t\tvar fallback_world: Vector2 = player.global_position + _get_player_facing_direction() * grid.get_cell_size()
\t\taim_cell = grid.world_to_cell(fallback_world)
\t_pending_area_aim_cell = aim_cell
''',
    '''\tif aim_cell == caster_cell and origin_mode == "self":
\t\tvar fallback_world: Vector2 = player.global_position + _get_player_facing_direction() * grid.get_cell_size()
\t\taim_cell = grid.world_to_cell(fallback_world)
\tvar direction_world: Vector2 = grid.cell_to_world_center(aim_cell) - player.global_position
\t_pending_area_direction = direction_world.normalized() if direction_world.length_squared() > 0.0001 else _get_player_facing_direction()
\t_pending_area_aim_cell = aim_cell
''',
    "point origin fallback",
)
text = replace_once(
    text,
    '''\tvar cells: Array[Vector2i] = _spell_area_system.get_area_cells(grid, caster_cell, aim_cell, area)
''',
    '''\tvar cells: Array[Vector2i] = _spell_area_system.get_area_cells(
\t\tgrid,
\t\tcaster_cell,
\t\taim_cell,
\t\tarea,
\t\t_pending_area_direction
\t)
''',
    "direction hint call",
)
text = replace_once(
    text,
    '''func _confirm_spell_area() -> void:
\tif not _spell_area_targeting_active or _pending_area_spell.is_empty():
\t\treturn
''',
    '''func _confirm_spell_area() -> void:
\tif not _spell_area_targeting_active or _pending_area_spell.is_empty() or _spell_area_confirmation_in_progress:
\t\treturn
''',
    "confirmation guard",
)
text = replace_once(
    text,
    '''\tvar spell_name: String = str(_pending_area_spell.get("name", "Заклинание"))
\tvar cast_result: Dictionary = _ability_system.perform_area_spell(
''',
    '''\tvar spell_name: String = str(_pending_area_spell.get("name", "Заклинание"))
\t_spell_area_confirmation_in_progress = true
\t_spell_area_confirm_button.disabled = true
\t_spell_area_cancel_button.disabled = true
\tvar cast_result: Dictionary = _ability_system.perform_area_spell(
''',
    "atomic confirmation start",
)
text = replace_once(
    text,
    '''\tif not bool(cast_result.get("success", false)):
\t\t_ability_panel.set_message(str(cast_result.get("message", "Заклинание не сработало.")), false)
\t\treturn
\t_set_combat_busy(true)
''',
    '''\tif not bool(cast_result.get("success", false)):
\t\t_spell_area_confirmation_in_progress = false
\t\t_spell_area_confirm_button.disabled = false
\t\t_spell_area_cancel_button.disabled = false
\t\t_ability_panel.set_message(str(cast_result.get("message", "Заклинание не сработало.")), false)
\t\treturn
\t_spell_area_targeting_active = false
\t_set_combat_busy(true)
''',
    "atomic confirmation success",
)
text = replace_once(
    text,
    '''func _cancel_spell_area_targeting() -> void:
\t_spell_area_targeting_active = false
\t_pending_area_spell.clear()
\t_pending_area_cells.clear()
\tif _spell_area_confirm_button != null:
\t\t_spell_area_confirm_button.hide()
\tif _spell_area_cancel_button != null:
\t\t_spell_area_cancel_button.hide()
''',
    '''func _cancel_spell_area_targeting() -> void:
\t_spell_area_targeting_active = false
\t_spell_area_confirmation_in_progress = false
\t_pending_area_spell.clear()
\t_pending_area_cells.clear()
\tif _spell_area_confirm_button != null:
\t\t_spell_area_confirm_button.disabled = false
\t\t_spell_area_confirm_button.hide()
\tif _spell_area_cancel_button != null:
\t\t_spell_area_cancel_button.disabled = false
\t\t_spell_area_cancel_button.hide()
''',
    "confirmation cleanup",
)
PATH.write_text(text, encoding="utf-8")
print("Spell area review fixes applied.")
