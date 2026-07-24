from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def replace_function(text: str, name: str, replacement: str) -> str:
    pattern = re.compile(rf"(?ms)^func {re.escape(name)}\(.*?(?=^func |\Z)")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"{name}: expected one function, found {len(matches)}")
    match = matches[0]
    return text[:match.start()] + replacement.rstrip() + "\n\n\n" + text[match.end():]


# Tighten cone width to the SRD rule: width at a distance equals that distance.
area_path = ROOT / "scripts/systems/spell_area_system.gd"
area_text = area_path.read_text(encoding="utf-8")
area_text = replace_once(
    area_text,
    "lateral_distance <= forward_distance * 0.5 + 0.5",
    "lateral_distance <= forward_distance * 0.5",
    "cone width",
)
area_path.write_text(area_text, encoding="utf-8")

# Add the first executable area spell and expose it to Wizard/Sorcerer starter data.
abilities_path = ROOT / "data/abilities/abilities.json"
abilities = json.loads(abilities_path.read_text(encoding="utf-8"))
abilities["burning_hands"] = {
    "id": "burning_hands",
    "name": "Горящие руки",
    "kind": "active",
    "is_spell": True,
    "spell_level": 1,
    "school": "Воплощение",
    "target": "area",
    "effect": "area_saving_throw_spell",
    "ability": "intelligence",
    "save_ability": "dexterity",
    "damage_dice": [3, 6],
    "damage_type": "fire",
    "save_for_half": True,
    "range_ft": 0,
    "casting_time_text": "1 действие",
    "components": ["v", "s"],
    "area": {
        "shape": "cone",
        "origin": "self",
        "length_ft": 15,
        "include_origin": False,
        "target_filter": "creatures"
    },
    "upcast": {"damage_dice_per_level": [1, 6]},
    "description": "Тонкий веер пламени охватывает 15-футовый конус. Каждая цель совершает спасбросок Ловкости; при успехе получает половину урона.",
    "button": "ГОРЯЩИЕ РУКИ"
}
abilities_path.write_text(json.dumps(abilities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

classes_path = ROOT / "data/classes/classes.json"
classes_root = json.loads(classes_path.read_text(encoding="utf-8"))
for class_data in classes_root.get("classes", []):
    if class_data.get("id") not in ("wizard", "sorcerer"):
        continue
    profile = class_data.setdefault("spellcasting", {})
    starting = profile.setdefault("starting_spells", [])
    prepared = profile.setdefault("starting_prepared", [])
    if "burning_hands" not in starting:
        starting.append("burning_hands")
    if "burning_hands" not in prepared:
        prepared.append("burning_hands")
classes_path.write_text(json.dumps(classes_root, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Battle-grid preview state and rendering.
grid_path = ROOT / "scripts/game/battle_grid.gd"
grid = grid_path.read_text(encoding="utf-8")
grid = replace_once(
    grid,
    "const MEASURE_COLOR: Color = Color(1.0, 0.72, 0.28, 0.92)\n",
    "const MEASURE_COLOR: Color = Color(1.0, 0.72, 0.28, 0.92)\nconst SPELL_AREA_COLOR: Color = Color(1.0, 0.32, 0.12, 0.28)\nconst SPELL_ORIGIN_COLOR: Color = Color(1.0, 0.82, 0.22, 0.48)\nconst INVALID_SPELL_CELL: Vector2i = Vector2i(-99999, -99999)\n",
    "grid colors",
)
grid = replace_once(
    grid,
    "var _last_active_position: Vector2 = Vector2.INF\n",
    "var _last_active_position: Vector2 = Vector2.INF\nvar _spell_area_cells: Array[Vector2i] = []\nvar _spell_area_origin_cell: Vector2i = INVALID_SPELL_CELL\nvar _spell_area_preview_active: bool = false\n",
    "grid preview fields",
)
marker = "func world_to_cell(world_position: Vector2) -> Vector2i:\n"
preview_methods = '''func set_spell_area_preview(cells: Array[Vector2i], origin_cell: Vector2i) -> void:
\t_spell_area_cells = cells.duplicate()
\t_spell_area_origin_cell = origin_cell
\t_spell_area_preview_active = true
\tqueue_redraw()


func clear_spell_area_preview() -> void:
\t_spell_area_cells.clear()
\t_spell_area_origin_cell = INVALID_SPELL_CELL
\t_spell_area_preview_active = false
\tqueue_redraw()


func is_spell_area_preview_active() -> bool:
\treturn _spell_area_preview_active


func get_spell_area_preview_cells() -> Array[Vector2i]:
\treturn _spell_area_cells.duplicate()


'''
if marker not in grid:
    raise RuntimeError("grid preview insertion marker missing")
grid = grid.replace(marker, preview_methods + marker, 1)
grid = replace_once(
    grid,
    '''\tdraw_rect(field_rect, BORDER_COLOR, false, 2.0)
\tif is_instance_valid(_active_actor):
''',
    '''\tdraw_rect(field_rect, BORDER_COLOR, false, 2.0)
\tif _spell_area_preview_active:
\t\tfor spell_cell: Vector2i in _spell_area_cells:
\t\t\t_draw_cell_highlight(cell_to_world_center(spell_cell), SPELL_AREA_COLOR)
\t\tif is_cell_valid(_spell_area_origin_cell):
\t\t\t_draw_cell_highlight(cell_to_world_center(_spell_area_origin_cell), SPELL_ORIGIN_COLOR)
\tif is_instance_valid(_active_actor):
''',
    "grid preview draw",
)
grid_path.write_text(grid, encoding="utf-8")

# One payment, one shared damage roll, one save per unique target.
ability_path = ROOT / "scripts/systems/class_ability_system.gd"
ability = ability_path.read_text(encoding="utf-8")
marker = "func consume_bardic_inspiration(character: PlayerCharacter) -> int:\n"
area_executor = '''func perform_area_spell(
\tcharacter: PlayerCharacter,
\tability: Dictionary,
\ttarget_contexts: Array,
\tcasting_context: Dictionary = {},
\tdamage_rolls_override: Array[int] = []
) -> Dictionary:
\tif character == null or str(ability.get("effect", "")) != "area_saving_throw_spell":
\t\treturn _failure("Для этой способности не создан исполнитель области.")
\tvar payment: Dictionary = _spellcasting.consume_spell_cost_detailed(
\t\tcharacter,
\t\tability,
\t\tint(casting_context.get("slot_level", 0)),
\t\tcasting_context
\t)
\tif not bool(payment.get("success", false)):
\t\treturn _failure(str(payment.get("message", "Заклинание недоступно.")))
\tvar slot_level: int = int(payment.get("slot_level", int(ability.get("spell_level", 0))))
\tvar damage_dice: Array[int] = _damage_dice_for_level(ability, character.level)
\tdamage_dice = _spellcasting.scale_dice_for_slot(ability, damage_dice, slot_level, "damage")
\tvar shared_damage: int = _roll_damage(damage_dice[0], damage_dice[1], damage_rolls_override)
\tshared_damage += _spellcasting.damage_bonus_for_slot(ability, slot_level)
\tvar ability_id: String = _spellcasting.get_spellcasting_ability(character, ability)
\tif ability_id.is_empty():
\t\tability_id = str(ability.get("ability", "intelligence"))
\tvar save_ability: String = str(ability.get("save_ability", "dexterity"))
\tvar spell_dc: int = int(ability.get("save_dc", 8 + CombatSystem.proficiency_bonus_for_level(character.level) + character.get_ability_modifier(ability_id)))
\tvar save_for_half: bool = bool(ability.get("save_for_half", false))
\tvar resolutions: Array[Dictionary] = []
\tvar seen_targets: Dictionary = {}
\tfor value: Variant in target_contexts:
\t\tif not value is Dictionary:
\t\t\tcontinue
\t\tvar target_context: Dictionary = value as Dictionary
\t\tif bool(target_context.get("total_cover", false)):
\t\t\tcontinue
\t\tvar target: Node = target_context.get("target") as Node
\t\tif not is_instance_valid(target):
\t\t\tcontinue
\t\tvar target_id: int = target.get_instance_id()
\t\tif seen_targets.has(target_id):
\t\t\tcontinue
\t\tseen_targets[target_id] = true
\t\tvar save_overrides: Array[int] = []
\t\tvar overrides_value: Variant = target_context.get("save_rolls_override", [])
\t\tif overrides_value is Array:
\t\t\tfor override_value: Variant in overrides_value:
\t\t\t\tsave_overrides.append(int(override_value))
\t\tvar defender_state: CombatantState = target_context.get("defender_state") as CombatantState
\t\tvar save_result: Dictionary = _srd_rules.resolve_saving_throw(
\t\t\tsave_ability,
\t\t\tint(target_context.get("target_save_modifier", 0)),
\t\t\tspell_dc,
\t\t\tdefender_state,
\t\t\tfalse,
\t\t\tfalse,
\t\t\tsave_overrides,
\t\t\t{"magical": true}
\t\t)
\t\tvar successful_save: bool = bool(save_result.get("success", false))
\t\tvar result := AttackResult.new()
\t\tresult.attack_name = str(ability.get("name", "Заклинание области"))
\t\tresult.target_name = str(target_context.get("target_name", target.name))
\t\tresult.damage_type = _srd_rules.normalize_damage_type(str(ability.get("damage_type", "force")))
\t\tresult.is_spell = true
\t\tresult.automatic_hit = true
\t\tresult.hit = not successful_save or save_for_half
\t\tresult.natural_roll = int(save_result.get("natural", 0))
\t\tresult.total = int(save_result.get("total", 0))
\t\tresult.damage = floori(float(shared_damage) / 2.0) if successful_save and save_for_half else (0 if successful_save else shared_damage)
\t\tresult.damage_before_mitigation = result.damage
\t\tresult.note = "%s: спасбросок %s %d против Сл %d — %s." % [
\t\t\tresult.target_name,
\t\t\tsave_ability,
\t\t\tresult.total,
\t\t\tspell_dc,
\t\t\t"успех" if successful_save else "провал"
\t\t]
\t\tresolutions.append({"target": target, "result": result, "save": save_result})
\treturn {
\t\t"success": true,
\t\t"message": "%s: область затронула целей — %d." % [str(ability.get("name", "Заклинание")), resolutions.size()],
\t\t"slot_level": slot_level,
\t\t"resource_key": str(payment.get("resource_key", "")),
\t\t"targets_count": resolutions.size(),
\t\t"shared_damage": shared_damage,
\t\t"resolutions": resolutions
\t}


'''
if marker not in ability:
    raise RuntimeError("area executor insertion marker missing")
ability = ability.replace(marker, area_executor + marker, 1)
ability_path.write_text(ability, encoding="utf-8")

# Describe areas in the character sheet.
spell_path = ROOT / "scripts/systems/spellcasting_system.gd"
spell = spell_path.read_text(encoding="utf-8")
spell = replace_once(
    spell,
    '''\tvar range_text: String = "На себя" if str(spell.get("target", "")) == "self" else "%d футов" % maxi(int(spell.get("range_ft", 0)), 0)
''',
    '''\tvar range_text: String = "На себя" if str(spell.get("target", "")) == "self" else "%d футов" % maxi(int(spell.get("range_ft", 0)), 0)
\tvar area_value: Variant = spell.get("area", {})
\tif area_value is Dictionary and SpellAreaSystem.new().is_area_definition(area_value as Dictionary):
\t\tvar origin_text: String = "От себя" if str((area_value as Dictionary).get("origin", "point")) == "self" else range_text
\t\trange_text = "%s · %s" % [origin_text, SpellAreaSystem.new().area_label(area_value as Dictionary)]
''',
    "spell area description",
)
spell_path.write_text(spell, encoding="utf-8")

# Area targeting, preview, confirmation and multi-target application in production combat.
game_path = ROOT / "scripts/game/game_srd_combat.gd"
game = game_path.read_text(encoding="utf-8")
game = replace_once(
    game,
    "var _srd_dice: DiceRoller = DiceRoller.new()\n",
    "var _srd_dice: DiceRoller = DiceRoller.new()\nvar _spell_area_system: SpellAreaSystem = SpellAreaSystem.new()\nvar _spell_area_runtime: SpellcastingSystem = SpellcastingSystem.new()\nvar _spell_area_targeting_active: bool = false\nvar _pending_area_spell: Dictionary = {}\nvar _pending_area_cells: Array[Vector2i] = []\nvar _pending_area_origin_cell: Vector2i = Vector2i.ZERO\nvar _pending_area_origin_world: Vector2 = Vector2.ZERO\nvar _pending_area_aim_cell: Vector2i = Vector2i.ZERO\nvar _spell_area_confirm_button: Button\nvar _spell_area_cancel_button: Button\n",
    "area runtime fields",
)
game = replace_once(
    game,
    '''\t_srd_combat_ui.hide_requested.connect(_on_hide_requested)
\t_state_for(player)
''',
    '''\t_srd_combat_ui.hide_requested.connect(_on_hide_requested)
\t_build_spell_area_controls()
\t_state_for(player)
''',
    "area controls ready",
)
process_marker = "func _process(delta: float) -> void:\n"
area_ui_methods = '''func _unhandled_input(event: InputEvent) -> void:
\tif not _spell_area_targeting_active:
\t\tsuper._unhandled_input(event)
\t\treturn
\tif event is InputEventKey:
\t\tvar key_event := event as InputEventKey
\t\tif key_event.pressed and not key_event.echo:
\t\t\tif key_event.keycode in [KEY_ESCAPE, KEY_BACKSPACE]:
\t\t\t\t_cancel_spell_area_targeting()
\t\t\t\tget_viewport().set_input_as_handled()
\t\t\t\treturn
\t\t\tif key_event.keycode in [KEY_ENTER, KEY_KP_ENTER, KEY_SPACE]:
\t\t\t\t_confirm_spell_area()
\t\t\t\tget_viewport().set_input_as_handled()
\t\t\t\treturn
\tvar screen_position: Vector2 = Vector2.INF
\tif event is InputEventMouseButton and (event as InputEventMouseButton).pressed and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
\t\tscreen_position = (event as InputEventMouseButton).position
\telif event is InputEventScreenTouch and (event as InputEventScreenTouch).pressed:
\t\tscreen_position = (event as InputEventScreenTouch).position
\tif screen_position != Vector2.INF:
\t\tvar world_position: Vector2 = get_viewport().get_canvas_transform().affine_inverse() * screen_position
\t\t_set_spell_area_aim_world(world_position)
\t\tget_viewport().set_input_as_handled()


func _build_spell_area_controls() -> void:
\tvar interface: CanvasLayer = $Interface
\t_spell_area_confirm_button = Button.new()
\t_spell_area_confirm_button.name = "SpellAreaConfirmButton"
\t_spell_area_confirm_button.text = "СОТВОРИТЬ ОБЛАСТЬ"
\t_spell_area_confirm_button.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
\t_spell_area_confirm_button.offset_left = 400.0
\t_spell_area_confirm_button.offset_top = -94.0
\t_spell_area_confirm_button.offset_right = 700.0
\t_spell_area_confirm_button.offset_bottom = -22.0
\t_spell_area_confirm_button.add_theme_font_size_override("font_size", 19)
\t_spell_area_confirm_button.pressed.connect(_confirm_spell_area)
\t_spell_area_confirm_button.hide()
\tinterface.add_child(_spell_area_confirm_button)
\t_spell_area_cancel_button = Button.new()
\t_spell_area_cancel_button.name = "SpellAreaCancelButton"
\t_spell_area_cancel_button.text = "ОТМЕНА"
\t_spell_area_cancel_button.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
\t_spell_area_cancel_button.offset_left = 714.0
\t_spell_area_cancel_button.offset_top = -94.0
\t_spell_area_cancel_button.offset_right = 894.0
\t_spell_area_cancel_button.offset_bottom = -22.0
\t_spell_area_cancel_button.add_theme_font_size_override("font_size", 18)
\t_spell_area_cancel_button.pressed.connect(_cancel_spell_area_targeting)
\t_spell_area_cancel_button.hide()
\tinterface.add_child(_spell_area_cancel_button)


func _is_area_spell(ability: Dictionary) -> bool:
\tvar area_value: Variant = ability.get("area", {})
\treturn str(ability.get("effect", "")) == "area_saving_throw_spell" and area_value is Dictionary and _spell_area_system.is_area_definition(area_value as Dictionary)


func _begin_spell_area_targeting(ability: Dictionary) -> void:
\tif not _is_area_spell(ability):
\t\treturn
\tvar casting_context: Dictionary = _build_spellcasting_context()
\tif not _spell_area_runtime.can_cast_spell(GameState.player_character, ability, false, _turn_system.active, 0, casting_context):
\t\t_ability_panel.set_message("Заклинание не подготовлено, нет ячейки или недоступны компоненты.", false)
\t\treturn
\t_pending_area_spell = ability.duplicate(true)
\t_spell_area_targeting_active = true
\t_spell_area_confirm_button.show()
\t_spell_area_cancel_button.show()
\tvar area: Dictionary = ability.get("area", {}) as Dictionary
\tvar distance_feet: int = maxi(int(area.get("length_ft", area.get("radius_ft", area.get("size_ft", 15)))), 5)
\tvar initial_world: Vector2 = player.global_position + _get_player_facing_direction() * DistanceSystem.feet_to_pixels(distance_feet)
\tif _target_is_valid(_selected_target):
\t\tinitial_world = (_selected_target as Node2D).global_position
\t_set_spell_area_aim_world(initial_world)
\tshow_combat_message("Выберите направление или точку области. Подтвердите отдельной кнопкой.", true)


func _set_spell_area_aim_world(world_position: Vector2) -> void:
\tif not _spell_area_targeting_active or _pending_area_spell.is_empty():
\t\treturn
\tvar grid: BattleGrid = _get_battle_grid()
\tif grid == null:
\t\treturn
\tvar area: Dictionary = _pending_area_spell.get("area", {}) as Dictionary
\tvar caster_cell: Vector2i = grid.world_to_cell(player.global_position)
\tvar aim_cell: Vector2i = grid.world_to_cell(world_position)
\tif not grid.is_cell_valid(aim_cell):
\t\treturn
\tif str(area.get("origin", "point")) != "self":
\t\tvar maximum_range: int = maxi(int(_pending_area_spell.get("range_ft", 0)), 0)
\t\tif maximum_range > 0 and DistanceSystem.distance_feet(player.global_position, grid.cell_to_world_center(aim_cell)) > maximum_range:
\t\t\tshow_combat_message("Точка происхождения находится дальше %d футов." % maximum_range, false)
\t\t\treturn
\t\tvar resolved_world: Vector2 = _spell_area_system.resolve_point_of_origin(
\t\t\tplayer.global_position,
\t\t\tgrid.cell_to_world_center(aim_cell),
\t\t\t_combat_environment
\t\t)
\t\taim_cell = grid.world_to_cell(resolved_world)
\tif aim_cell == caster_cell:
\t\tvar fallback_world: Vector2 = player.global_position + _get_player_facing_direction() * grid.get_cell_size()
\t\taim_cell = grid.world_to_cell(fallback_world)
\t_pending_area_aim_cell = aim_cell
\t_pending_area_origin_cell = _spell_area_system.get_origin_cell(caster_cell, aim_cell, area)
\t_pending_area_origin_world = grid.cell_to_world_center(_pending_area_origin_cell)
\tvar cells: Array[Vector2i] = _spell_area_system.get_area_cells(grid, caster_cell, aim_cell, area)
\t_pending_area_cells = _spell_area_system.filter_cells_by_total_cover(grid, cells, _pending_area_origin_world, _combat_environment)
\tgrid.set_spell_area_preview(_pending_area_cells, _pending_area_origin_cell)
\tvar target_count: int = _collect_pending_area_targets().size()
\t_spell_area_confirm_button.text = "СОТВОРИТЬ · ЦЕЛЕЙ: %d" % target_count


func _collect_pending_area_targets() -> Array[Node]:
\tvar grid: BattleGrid = _get_battle_grid()
\tif grid == null:
\t\treturn []
\treturn _spell_area_system.collect_targets(
\t\tgrid,
\t\t_pending_area_cells,
\t\t_available_targets(),
\t\t_pending_area_origin_world,
\t\t_combat_environment
\t)


func _confirm_spell_area() -> void:
\tif not _spell_area_targeting_active or _pending_area_spell.is_empty():
\t\treturn
\tif _turn_system.active and not _turn_system.is_player_turn(player):
\t\t_ability_panel.set_message("Область можно применить только на своём ходу.", false)
\t\treturn
\tvar casting_context: Dictionary = _build_spellcasting_context()
\tif not _spell_area_runtime.can_cast_spell(GameState.player_character, _pending_area_spell, false, _turn_system.active, 0, casting_context):
\t\t_ability_panel.set_message("Заклинание недоступно: проверьте ячейку, подготовку и компоненты.", false)
\t\treturn
\tif _turn_system.active and not _turn_system.consume_action():
\t\t_ability_panel.set_message("Действие на этом ходу уже использовано.", false)
\t\treturn
\tvar targets: Array[Node] = _collect_pending_area_targets()
\tvar target_contexts: Array = []
\tvar save_ability: String = str(_pending_area_spell.get("save_ability", "dexterity"))
\tfor target: Node in targets:
\t\tif not _target_is_valid(target):
\t\t\tcontinue
\t\ttarget_contexts.append({
\t\t\t"target": target,
\t\t\t"target_name": _target_name(target),
\t\t\t"defender_state": _state_for(target),
\t\t\t"target_save_modifier": int(target.call("get_saving_throw_modifier", save_ability)) if target.has_method("get_saving_throw_modifier") else 0,
\t\t\t"total_cover": false
\t\t})
\tvar spell_name: String = str(_pending_area_spell.get("name", "Заклинание"))
\tvar cast_result: Dictionary = _ability_system.perform_area_spell(
\t\tGameState.player_character,
\t\t_pending_area_spell,
\t\ttarget_contexts,
\t\tcasting_context
\t)
\tif not bool(cast_result.get("success", false)):
\t\t_ability_panel.set_message(str(cast_result.get("message", "Заклинание не сработало.")), false)
\t\treturn
\t_set_combat_busy(true)
\tplayer.play_attack_animation(grid_cell_world(_pending_area_aim_cell))
\tawait get_tree().create_timer(0.24).timeout
\tvar total_damage: int = 0
\tvar applied_targets: int = 0
\tvar resolutions_value: Variant = cast_result.get("resolutions", [])
\tif resolutions_value is Array:
\t\tfor resolution_value: Variant in resolutions_value:
\t\t\tif not resolution_value is Dictionary:
\t\t\t\tcontinue
\t\t\tvar resolution: Dictionary = resolution_value as Dictionary
\t\t\tvar target: Node = resolution.get("target") as Node
\t\t\tvar result: AttackResult = resolution.get("result") as AttackResult
\t\t\tif not is_instance_valid(target) or result == null:
\t\t\t\tcontinue
\t\t\t_apply_mitigation_to_result(result, _state_for(target))
\t\t\ttotal_damage += result.damage
\t\t\tapplied_targets += 1
\t\t\ttarget.call("receive_player_attack", result, false)
\t_set_combat_busy(false)
\t_ability_panel.set_message("%s: целей %d, суммарный урон %d." % [spell_name, applied_targets, total_damage], true)
\tGameState.save_game()
\t_update_status()
\t_sync_exploration_hud_visibility()
\tvar combat_trigger: Node = targets[0] if not targets.is_empty() else null
\t_cancel_spell_area_targeting()
\tif not _turn_system.active and is_instance_valid(combat_trigger):
\t\t_start_turn_based_combat(combat_trigger)
\t_after_player_action()


func grid_cell_world(cell: Vector2i) -> Vector2:
\tvar grid: BattleGrid = _get_battle_grid()
\treturn grid.cell_to_world_center(cell) if grid != null and grid.is_cell_valid(cell) else player.global_position


func _cancel_spell_area_targeting() -> void:
\t_spell_area_targeting_active = false
\t_pending_area_spell.clear()
\t_pending_area_cells.clear()
\tif _spell_area_confirm_button != null:
\t\t_spell_area_confirm_button.hide()
\tif _spell_area_cancel_button != null:
\t\t_spell_area_cancel_button.hide()
\tvar grid: BattleGrid = _get_battle_grid()
\tif grid != null:
\t\tgrid.clear_spell_area_preview()


'''
if process_marker not in game:
    raise RuntimeError("game area UI insertion marker missing")
game = game.replace(process_marker, area_ui_methods + process_marker, 1)
# Block ordinary actions while selecting an area.
game = replace_once(
    game,
    "if GameState.input_locked or _any_overlay_visible() or _attack_in_progress or _enemy_turn_running:\n",
    "if GameState.input_locked or _any_overlay_visible() or _attack_in_progress or _enemy_turn_running or _spell_area_targeting_active:\n",
    "attack guard",
)
game = replace_once(
    game,
    "if GameState.input_locked or _attack_in_progress or _enemy_turn_running:\n",
    "if GameState.input_locked or _attack_in_progress or _enemy_turn_running:\n",
    "ability guard anchor",
)
# Handle repeated/alternate ability taps and enter targeting before action consumption.
game = replace_once(
    game,
    '''\tif ability.is_empty():
\t\t_ability_panel.set_message("Способность не найдена.", false)
\t\treturn
''',
    '''\tif ability.is_empty():
\t\t_ability_panel.set_message("Способность не найдена.", false)
\t\treturn
\tif _spell_area_targeting_active:
\t\tif ability_id == str(_pending_area_spell.get("id", "")):
\t\t\t_confirm_spell_area()
\t\t\treturn
\t\t_cancel_spell_area_targeting()
''',
    "area repeat ability",
)
game = replace_once(
    game,
    '''\tif not _srd_rules.can_take_action(_player_combat_state):
\t\t_ability_panel.set_message("Текущее состояние не позволяет применять способности.", false)
\t\treturn

\tvar target_type: String = str(ability.get("target", "self"))
''',
    '''\tif not _srd_rules.can_take_action(_player_combat_state):
\t\t_ability_panel.set_message("Текущее состояние не позволяет применять способности.", false)
\t\treturn
\tif _is_area_spell(ability):
\t\t_begin_spell_area_targeting(ability)
\t\treturn

\tvar target_type: String = str(ability.get("target", "self"))
''',
    "area ability dispatch",
)
# Block movement while targeting.
game = replace_once(
    game,
    "if GameState.input_locked or _any_overlay_visible() or _attack_in_progress or _enemy_turn_running:\n\t\treturn\n\tif step == Vector2i.ZERO:\n",
    "if GameState.input_locked or _any_overlay_visible() or _attack_in_progress or _enemy_turn_running or _spell_area_targeting_active:\n\t\treturn\n\tif step == Vector2i.ZERO:\n",
    "movement targeting guard",
)
game_path.write_text(game, encoding="utf-8")

print("Spell targeting areas patch applied.")
