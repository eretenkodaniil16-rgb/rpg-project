from __future__ import annotations

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


game_path = ROOT / "scripts/game/game_srd_combat.gd"
text = game_path.read_text(encoding="utf-8")
text = replace_once(
    text,
    'const SRD_COMBAT_UI_SCRIPT: Script = preload("res://scripts/ui/srd_combat_ui.gd")\n',
    'const SRD_COMBAT_UI_SCRIPT: Script = preload("res://scripts/ui/srd_combat_ui.gd")\nconst SPELL_REACTION_PROMPT_SCRIPT: Script = preload("res://scripts/ui/spell_reaction_prompt.gd")\nconst RUNE_TRAINING_CONSTRUCT_SCRIPT: Script = preload("res://scripts/game/rune_training_construct.gd")\n',
    "runtime preloads",
)
text = replace_once(
    text,
    'var _spell_area_cancel_button: Button\n',
    'var _spell_area_cancel_button: Button\nvar _spell_reaction_system: SpellReactionSystem = SpellReactionSystem.new()\nvar _spell_reaction_prompt: SpellReactionPrompt\nvar _rune_training_construct: RuneTrainingConstruct\nvar _reaction_decision_in_progress: bool = false\n',
    "runtime fields",
)
text = replace_once(
    text,
    '\t_build_spell_area_controls()\n\t_state_for(player)\n',
    '\t_build_spell_area_controls()\n\t_build_spell_reaction_runtime()\n\t_state_for(player)\n',
    "runtime ready hook",
)

marker = 'func _build_spell_area_controls() -> void:\n'
runtime_methods = '''func _build_spell_reaction_runtime() -> void:
\t_spell_reaction_prompt = SPELL_REACTION_PROMPT_SCRIPT.new() as SpellReactionPrompt
\t_spell_reaction_prompt.name = "SpellReactionPrompt"
\t$Interface.add_child(_spell_reaction_prompt)
\t_rune_training_construct = RUNE_TRAINING_CONSTRUCT_SCRIPT.new() as RuneTrainingConstruct
\t_rune_training_construct.name = "RuneTrainingConstruct"
\t_rune_training_construct.position = Vector2(860.0, 245.0)
\tadd_child(_rune_training_construct)


func get_spell_reaction_prompt() -> SpellReactionPrompt:
\treturn _spell_reaction_prompt


func get_rune_training_construct() -> RuneTrainingConstruct:
\treturn _rune_training_construct


func _any_overlay_visible() -> bool:
\treturn super._any_overlay_visible() or (_spell_reaction_prompt != null and _spell_reaction_prompt.visible)


'''
if marker not in text:
    raise RuntimeError("spell area controls marker missing")
text = text.replace(marker, runtime_methods + marker, 1)

text = replace_function(text, "_run_enemy_turn", '''func _run_enemy_turn(actor: Node) -> void:
\tif not _turn_system.active or _turn_system.current_actor() != actor:
\t\treturn
\t_enemy_turn_running = true
\t_refresh_turn_interface()
\twhile _turn_system.active and _any_overlay_visible():
\t\tawait get_tree().process_frame
\tawait get_tree().create_timer(0.3).timeout
\tvar state: CombatantState = _state_for(actor)
\tif not _srd_rules.can_take_action(state):
\t\t_enemy_turn_running = false
\t\t_advance_combat_turn()
\t\treturn
\tif state.has_condition("grappled"):
\t\tvar escape_dc: int = _condition_save_dc(state, "grappled", 10)
\t\tvar escape: Dictionary = _srd_rules.resolve_d20_test(int(actor.call("get_initiative_modifier")) if actor.has_method("get_initiative_modifier") else 0, escape_dc)
\t\tif bool(escape.get("success", false)):
\t\t\tstate.remove_condition("grappled")
\t\t\t_release_grapples_for(actor)
\t\tshow_combat_message("%s пытается вырваться из захвата." % _target_name(actor), bool(escape.get("success", false)))
\telse:
\t\tvar spell_id: String = str(actor.call("get_combat_spell_id")) if actor.has_method("get_combat_spell_id") else ""
\t\tvar spell: Dictionary = _spell_area_runtime.get_spell_definition(spell_id) if not spell_id.is_empty() else {}
\t\tvar desired_range: int = DistanceSystem.MELEE_REACH_FEET
\t\tif not spell.is_empty():
\t\t\tvar area_value: Variant = spell.get("area", {})
\t\t\tif area_value is Dictionary:
\t\t\t\tvar area: Dictionary = area_value as Dictionary
\t\t\t\tdesired_range = maxi(int(area.get("length_ft", area.get("radius_ft", area.get("size_ft", 15)))), 5)
\t\t\telse:
\t\t\t\tdesired_range = maxi(int(spell.get("range_ft", 5)), 5)
\t\tvar movement_feet: int = _srd_rules.effective_speed_feet(int(actor.call("get_combat_speed_feet")) if actor.has_method("get_combat_speed_feet") else 30, state)
\t\twhile movement_feet >= GRID_STEP_FEET_SRD and DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position) > desired_range:
\t\t\tvar cost: int = _move_enemy_srd_one_step(actor as Node2D, state)
\t\t\tif cost <= 0 or cost > movement_feet:
\t\t\t\tbreak
\t\t\tmovement_feet -= cost
\t\t\tawait _trigger_readied_attack_if_possible(actor)
\t\t\tif not _target_is_valid(actor):
\t\t\t\tbreak
\t\t\tawait get_tree().create_timer(0.1).timeout
\t\tif is_instance_valid(actor) and _target_is_valid(actor):
\t\t\tvar distance: int = DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position)
\t\t\tif not spell.is_empty() and distance <= desired_range:
\t\t\t\tvar slot_level: int = int(actor.call("get_combat_spell_slot_level")) if actor.has_method("get_combat_spell_slot_level") else maxi(int(spell.get("spell_level", 0)), 1)
\t\t\t\tawait _resolve_npc_spell_turn(actor, spell, slot_level)
\t\t\telif distance <= DistanceSystem.MELEE_REACH_FEET and actor.has_method("perform_combat_turn_attack"):
\t\t\t\tactor.call("perform_combat_turn_attack")
\t\t\t\t_update_status()
\t\t\t\tawait get_tree().create_timer(0.35).timeout
\t_enemy_turn_running = false
\tif not _player_combat_state.dead:
\t\t_advance_combat_turn()''')

insert_marker = 'func _move_enemy_srd_one_step(actor: Node2D, state: CombatantState) -> int:\n'
reaction_methods = '''func _resolve_npc_spell_turn(actor: Node, spell: Dictionary, slot_level: int) -> Dictionary:
\tif actor == null or spell.is_empty() or not (actor is Node2D):
\t\treturn {"success": false, "message": "Вражеское заклинание не определено."}
\tvar distance: int = DistanceSystem.distance_feet((actor as Node2D).global_position, player.global_position)
\tvar cover: Dictionary = _combat_environment.get_cover(player.global_position, (actor as Node2D).global_position) if _combat_environment != null else {"total_cover": false}
\tif bool(cover.get("total_cover", false)):
\t\tshow_combat_message("%s не может выбрать героя целью из-за полного укрытия." % _target_name(actor), false)
\t\treturn {"success": false, "total_cover": true}
\tvar attempt := SpellCastAttempt.new(spell, actor, slot_level)
\tattempt.caster_constitution_modifier = int(actor.call("get_saving_throw_modifier", "constitution")) if actor.has_method("get_saving_throw_modifier") else 0
\tattempt.caster_state = _state_for(actor)
\tattempt.action_kind = "action"
\tvar casting_context: Dictionary = _build_spellcasting_context()
\tvar offer: Dictionary = _spell_reaction_system.evaluate_counterspell(
\t\tGameState.player_character,
\t\tattempt,
\t\t_turn_system.has_reaction(player),
\t\ttrue,
\t\tdistance,
\t\tcasting_context
\t)
\tif bool(offer.get("available", false)) and _spell_reaction_prompt != null:
\t\t_reaction_decision_in_progress = true
\t\t_sync_exploration_hud_visibility()
\t\tvar use_counterspell: bool = await _spell_reaction_prompt.request_counterspell(attempt, offer)
\t\t_reaction_decision_in_progress = false
\t\t_sync_exploration_hud_visibility()
\t\tif use_counterspell:
\t\t\tvar save_overrides: Array[int] = []
\t\t\tif actor.has_method("get_counterspell_save_roll_overrides"):
\t\t\t\tvar override_value: Variant = actor.call("get_counterspell_save_roll_overrides")
\t\t\t\tif override_value is Array:
\t\t\t\t\tfor value: Variant in override_value:
\t\t\t\t\t\tsave_overrides.append(int(value))
\t\t\tvar reaction_result: Dictionary = _spell_reaction_system.resolve_counterspell(
\t\t\t\tGameState.player_character,
\t\t\t\tattempt,
\t\t\t\t_turn_system.has_reaction(player),
\t\t\t\ttrue,
\t\t\t\tdistance,
\t\t\t\tcasting_context,
\t\t\t\tsave_overrides
\t\t\t)
\t\t\tif bool(reaction_result.get("consume_reaction", false)):
\t\t\t\t_turn_system.consume_reaction(player)
\t\t\tshow_combat_message(str(reaction_result.get("message", "Контрзаклинание разрешено.")), bool(reaction_result.get("countered", false)))
\t\t\tGameState.save_game()
\t\t\tif bool(reaction_result.get("countered", false)):
\t\t\t\treturn {"success": true, "countered": true, "original_slot_expended": false}
\t\telse:
\t\t\tattempt.mark_proceeds()
\telse:
\t\tattempt.mark_proceeds()
\tif not attempt.should_expend_original_resource():
\t\treturn {"success": true, "countered": true, "original_slot_expended": false}
\tif not actor.has_method("consume_combat_spell_slot") or not bool(actor.call("consume_combat_spell_slot", slot_level)):
\t\tshow_combat_message("У %s не осталось ячейки для %s." % [_target_name(actor), attempt.get_spell_name()], false)
\t\treturn {"success": false, "message": "Исходная ячейка недоступна."}
\tattempt.mark_original_resource_expended("enemy_spell_slots_%d" % slot_level)
\tvar resolution: Dictionary = _resolve_npc_spell_against_player(actor, spell, slot_level)
\tresolution["countered"] = false
\tresolution["original_slot_expended"] = true
\treturn resolution


func _resolve_npc_spell_against_player(actor: Node, spell: Dictionary, slot_level: int) -> Dictionary:
\tvar effect: String = str(spell.get("effect", ""))
\tif effect != "area_saving_throw_spell" and effect != "saving_throw_spell":
\t\tshow_combat_message("Для вражеского заклинания %s ещё нет исполнителя." % str(spell.get("name", "Заклинание")), false)
\t\treturn {"success": false, "message": "Исполнитель заклинания отсутствует."}
\tvar save_ability: String = str(spell.get("save_ability", "dexterity"))
\tvar save_modifier: int = GameState.player_character.get_saving_throw_modifier(save_ability)
\tvar save_dc: int = int(actor.call("get_spell_save_dc")) if actor.has_method("get_spell_save_dc") else 12
\tvar save: Dictionary = _srd_rules.resolve_saving_throw(
\t\tsave_ability,
\t\tsave_modifier,
\t\tsave_dc,
\t\t_player_combat_state,
\t\tfalse,
\t\tfalse,
\t\t[],
\t\t{"magical": true, "spell_id": str(spell.get("id", ""))}
\t)
\tvar dice_value: Variant = spell.get("damage_dice", [1, 6])
\tvar base_dice: Array[int] = [1, 6]
\tif dice_value is Array and (dice_value as Array).size() >= 2:
\t\tbase_dice = [maxi(int((dice_value as Array)[0]), 1), maxi(int((dice_value as Array)[1]), 2)]
\tvar scaled_dice: Array[int] = _spell_area_runtime.scale_dice_for_slot(spell, base_dice, slot_level, "damage")
\tvar rolled_damage: int = 0
\tfor _index: int in range(scaled_dice[0]):
\t\trolled_damage += _srd_dice.roll_die(scaled_dice[1])
\trolled_damage += _spell_area_runtime.damage_bonus_for_slot(spell, slot_level)
\tvar save_success: bool = bool(save.get("success", false))
\tvar applied_damage: int = rolled_damage
\tif save_success:
\t\tapplied_damage = floori(float(rolled_damage) / 2.0) if bool(spell.get("save_for_half", false)) else 0
\tshow_combat_message("%s сотворяет %s. Спасбросок %s: %d против Сл %d." % [
\t\t_target_name(actor),
\t\tstr(spell.get("name", "заклинание")),
\t\tsave_ability,
\t\tint(save.get("total", 0)),
\t\tsave_dc
\t], save_success)
\tif applied_damage > 0:
\t\tapply_damage_to_player(applied_damage, str(spell.get("damage_type", "force")), false, actor)
\treturn {
\t\t"success": true,
\t\t"save": save,
\t\t"rolled_damage": rolled_damage,
\t\t"applied_damage": applied_damage,
\t\t"slot_level": slot_level
\t}


'''
if insert_marker not in text:
    raise RuntimeError("enemy movement marker missing")
text = text.replace(insert_marker, reaction_methods + insert_marker, 1)
game_path.write_text(text, encoding="utf-8")

# Update the workflow to cover the runtime path and smoke test.
workflow_path = ROOT / ".github/workflows/validate-spell-reactions-counterspell.yml"
workflow = workflow_path.read_text(encoding="utf-8")
workflow = replace_once(
    workflow,
    '      - "scripts/systems/spellcasting_system.gd"\n      - "tests/test_spell_reactions_counterspell.gd"\n',
    '      - "scripts/systems/spellcasting_system.gd"\n      - "scripts/game/game_srd_combat.gd"\n      - "scripts/game/rune_training_construct.gd"\n      - "scripts/ui/spell_reaction_prompt.gd"\n      - "tests/test_spell_reactions_counterspell.gd"\n      - "tests/smoke_spell_reaction_prompt_runtime.gd"\n',
    "pull request paths",
)
workflow = replace_once(
    workflow,
    '      - "scripts/systems/spellcasting_system.gd"\n      - "tests/test_spell_reactions_counterspell.gd"\n',
    '      - "scripts/systems/spellcasting_system.gd"\n      - "scripts/game/game_srd_combat.gd"\n      - "scripts/game/rune_training_construct.gd"\n      - "scripts/ui/spell_reaction_prompt.gd"\n      - "tests/test_spell_reactions_counterspell.gd"\n      - "tests/smoke_spell_reaction_prompt_runtime.gd"\n',
    "push paths",
)
workflow += '''\n      - name: Smoke test Counterspell runtime prompt\n        shell: bash\n        run: ./Godot_v4.7.1-stable_linux.x86_64 --headless --path "$GITHUB_WORKSPACE" --script res://tests/smoke_spell_reaction_prompt_runtime.gd\n'''
workflow_path.write_text(workflow, encoding="utf-8")

print("Counterspell runtime integration applied.")
