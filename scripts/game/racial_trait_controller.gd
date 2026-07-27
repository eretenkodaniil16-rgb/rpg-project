class_name RacialTraitController
extends Node

var game: Node
var action_ui: ActionCatalogUI
var class_data := ClassDataSystem.new()
var last_turn_key: String = ""


func _ready() -> void:
	game = get_parent()
	call_deferred("initialize")


func _process(_delta: float) -> void:
	if action_ui == null:
		initialize()
		return
	sync_state()
	sync_speed()
	inject_ability()


func initialize() -> void:
	if game == null:
		return
	var ui_value: Variant = game.get("_action_catalog_ui")
	if ui_value is ActionCatalogUI:
		action_ui = ui_value as ActionCatalogUI
	sync_state()


func sync_state() -> void:
	if game == null:
		return
	var state_value: Variant = game.get("_player_combat_state")
	if not state_value is CombatantState:
		return
	var character: PlayerCharacter = get_character()
	if character == null:
		return
	var state: CombatantState = state_value as CombatantState
	for damage_type: String in character.racial_damage_resistances:
		if damage_type not in state.damage_resistances:
			state.damage_resistances.append(damage_type)
	state.saving_throw_advantage_conditions = character.racial_condition_save_advantage.duplicate()
	state.saving_throw_advantage_abilities = character.racial_save_advantage_abilities.duplicate()
	state.magical_save_advantage_abilities = character.racial_magical_save_advantage_abilities.duplicate()
	state.reroll_natural_one = character.reroll_natural_one


func sync_speed() -> void:
	if game == null:
		return
	var turn_value: Variant = game.get("_turn_system")
	if not turn_value is TurnBasedCombatSystem:
		return
	var turn_system: TurnBasedCombatSystem = turn_value as TurnBasedCombatSystem
	var player: Node = game.get_node_or_null("Player")
	var actor: Node = turn_system.current_actor()
	if not turn_system.active or actor != player:
		return
	var key: String = "%d:%d" % [turn_system.round_number, actor.get_instance_id()]
	if key == last_turn_key:
		return
	var character: PlayerCharacter = get_character()
	if character != null:
		turn_system.movement_remaining_feet = maxi(character.base_speed_feet, 0)
	last_turn_key = key


func inject_ability() -> void:
	if action_ui == null or game == null:
		return
	var character: PlayerCharacter = get_character()
	if character == null:
		return
	var ability: Dictionary = class_data.get_racial_ability(character)
	if ability.is_empty():
		return
	var entries_value: Variant = action_ui.get("_entries")
	if not entries_value is Dictionary:
		return
	var entries: Dictionary = (entries_value as Dictionary).duplicate(true)
	var category: String = "bonus" if str(ability.get("action_kind", "action")) == "bonus" else "action"
	var values: Array = entries.get(category, []) as Array
	var entry_id: String = "ability:%s" % str(ability.get("id", character.racial_ability_id))
	var turn_system: TurnBasedCombatSystem = game.get("_turn_system") as TurnBasedCombatSystem
	var player: Node = game.get_node_or_null("Player")
	var resource_key: String = str(ability.get("resource_key", "unlimited"))
	var enabled: bool = turn_system != null and turn_system.active and turn_system.current_actor() == player
	if resource_key != "unlimited":
		enabled = enabled and character.get_resource(resource_key) > 0
	if category == "bonus":
		enabled = enabled and turn_system.bonus_action_available
	else:
		enabled = enabled and turn_system.action_available
	var replacement: Dictionary = {
		"id": entry_id,
		"label": str(ability.get("name", "Расовая способность")),
		"enabled": enabled,
		"description": "%s Ресурс: %s." % [str(ability.get("description", "")), class_data.get_resource_text(character, ability)],
		"group": "attack" if str(ability.get("target", "self")) == "enemy" else "tactic"
	}
	var replaced: bool = false
	for index: int in range(values.size()):
		var value: Variant = values[index]
		if value is Dictionary and str((value as Dictionary).get("id", "")) == entry_id:
			values[index] = replacement
			replaced = true
			break
	if not replaced:
		values.append(replacement)
	entries[category] = values
	action_ui.set("_entries", entries)


func get_character() -> PlayerCharacter:
	var state: Node = get_node_or_null("/root/GameState")
	if state == null:
		return null
	var value: Variant = state.get("player_character")
	return value as PlayerCharacter if value is PlayerCharacter else null
