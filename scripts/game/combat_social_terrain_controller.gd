class_name CombatSocialTerrainController
extends Node

const TERRAIN_MOVEMENT_SCRIPT: Script = preload("res://scripts/systems/terrain_aware_movement_system.gd")
const SOCIAL_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/combat_social_action_system.gd")

var _game: Node
var _action_ui: ActionCatalogUI
var _dialogue_ui: Node
var _social_system: CombatSocialActionSystem = SOCIAL_SYSTEM_SCRIPT.new() as CombatSocialActionSystem
var _class_data: ClassDataSystem = ClassDataSystem.new()
var _free_category_button: Button
var _initialized: bool = false
var _social_action_used_this_turn: bool = false
var _turn_signature: String = ""


func _ready() -> void:
	_game = get_parent()
	call_deferred("_try_initialize")


func _process(_delta: float) -> void:
	if not _initialized:
		_try_initialize()
		return
	_sync_player_terrain_trait()
	_refresh_turn_signature()
	_inject_free_action_entries()


func _try_initialize() -> void:
	if _initialized or _game == null:
		return
	var ui_value: Variant = _game.get("_action_catalog_ui")
	if not ui_value is ActionCatalogUI:
		return
	_action_ui = ui_value as ActionCatalogUI
	_dialogue_ui = get_tree().get_first_node_in_group("dialogue_ui")
	if _dialogue_ui == null:
		return
	_game.set("_movement_planner", TERRAIN_MOVEMENT_SCRIPT.new() as TerrainAwareMovementSystem)
	_install_free_category_button()
	if not _action_ui.action_requested.is_connected(_on_action_requested):
		_action_ui.action_requested.connect(_on_action_requested)
	_connect_dialogue_signals()
	_initialized = true
	_sync_player_terrain_trait()
	if _game.has_method("_invalidate_reachable_area"):
		_game.call("_invalidate_reachable_area")


func _connect_dialogue_signals() -> void:
	var runtime_callable := Callable(self, "_on_dialogue_runtime_choice_requested")
	if _dialogue_ui.has_signal("runtime_choice_requested") and not _dialogue_ui.is_connected("runtime_choice_requested", runtime_callable):
		_dialogue_ui.connect("runtime_choice_requested", runtime_callable)
	var attack_callable := Callable(self, "_on_dialogue_attack_requested")
	if _dialogue_ui.has_signal("attack_requested") and not _dialogue_ui.is_connected("attack_requested", attack_callable):
		_dialogue_ui.connect("attack_requested", attack_callable)


func _install_free_category_button() -> void:
	if _action_ui == null or _action_ui.category_row == null:
		return
	var existing: Node = _action_ui.category_row.get_node_or_null("FreeCategoryButton")
	if existing is Button:
		_free_category_button = existing as Button
		return
	_free_category_button = Button.new()
	_free_category_button.name = "FreeCategoryButton"
	_free_category_button.text = "СВОБОДНОЕ"
	_free_category_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_free_category_button.pressed.connect(Callable(_action_ui, "_select_category").bind("free"))
	_action_ui.category_row.add_child(_free_category_button)
	_action_ui.category_row.move_child(_free_category_button, 2)


func _refresh_turn_signature() -> void:
	var turn_value: Variant = _game.get("_turn_system")
	if not turn_value is TurnBasedCombatSystem:
		return
	var turn_system: TurnBasedCombatSystem = turn_value as TurnBasedCombatSystem
	var current_actor: Node = turn_system.current_actor()
	var signature: String = "%s:%s" % [turn_system.round_number, current_actor.get_instance_id() if is_instance_valid(current_actor) else 0]
	if signature == _turn_signature:
		return
	_turn_signature = signature
	var player: Node = _game.get_node_or_null("Player")
	if current_actor == player:
		_social_action_used_this_turn = false


func _inject_free_action_entries() -> void:
	if _action_ui == null:
		return
	var turn_value: Variant = _game.get("_turn_system")
	if not turn_value is TurnBasedCombatSystem:
		return
	var turn_system: TurnBasedCombatSystem = turn_value as TurnBasedCombatSystem
	var player: Node = _game.get_node_or_null("Player")
	var selected_target: Node = _game.get("_selected_target") as Node
	var player_turn: bool = turn_system.active and turn_system.current_actor() == player and not bool(_game.get("_enemy_turn_running"))
	var target_valid: bool = _target_is_valid(selected_target)
	var free_entries: Array[Dictionary] = [{
		"id": "combat_dialogue",
		"label": "РАЗГОВОР И ЖЕСТЫ",
		"enabled": player_turn and target_valid and not _social_action_used_this_turn,
		"description": "Открыть диалог с выбранной целью. Реплика или жест являются свободным действием; в окне всегда доступна атака.",
		"group": "speech"
	}]
	var entries_value: Variant = _action_ui.get("_entries")
	var entries: Dictionary = (entries_value as Dictionary).duplicate(true) if entries_value is Dictionary else {}
	entries["free"] = free_entries
	_action_ui.set("_entries", entries)
	if _action_ui.panel.visible and str(_action_ui.get("_selected_category")) == "free":
		_action_ui.call("_rebuild_action_grid")


func _on_action_requested(action_id: String) -> void:
	if action_id == "combat_dialogue":
		_open_combat_dialogue()
		return
	if action_id.begins_with("social:"):
		_perform_social_action(action_id.trim_prefix("social:"), _game.get("_selected_target") as Node)


func _open_combat_dialogue() -> void:
	var turn_system: TurnBasedCombatSystem = _game.get("_turn_system") as TurnBasedCombatSystem
	var player: Node = _game.get_node_or_null("Player")
	var target: Node = _game.get("_selected_target") as Node
	if turn_system == null or player == null or not turn_system.active or turn_system.current_actor() != player:
		_show_message("Разговор в бою можно начать только на своём ходу.", false)
		return
	if _social_action_used_this_turn:
		_show_message("В этом ходу уже использована содержательная реплика или жест.", false)
		return
	if not _target_is_valid(target):
		_show_message("Сначала выберите противника, к которому хотите обратиться.", false)
		return
	var character: PlayerCharacter = _get_player_character()
	var race_id: String = character.race_id if character != null else ""
	var choices: Array[Dictionary] = []
	for action: Dictionary in _social_system.get_actions(race_id):
		choices.append({
			"text": str(action.get("label", "ОБЩЕНИЕ")),
			"runtime_action": "combat_social:%s" % str(action.get("id", ""))
		})
	var dialogue_data: Dictionary = {
		"speaker": _target_name(target),
		"text": "Выберите реплику или жест. Это не расходует действие. Атаковать можно прямо из этого окна.",
		"choices": choices
	}
	_action_ui.close_catalog()
	_dialogue_ui.call("start_dialogue", dialogue_data, target)


func _on_dialogue_runtime_choice_requested(action_id: String, target: Node) -> void:
	if not action_id.begins_with("combat_social:"):
		return
	_perform_social_action(action_id.trim_prefix("combat_social:"), target)


func _perform_social_action(action_id: String, target: Node) -> void:
	var turn_system: TurnBasedCombatSystem = _game.get("_turn_system") as TurnBasedCombatSystem
	var player: Node2D = _game.get_node_or_null("Player") as Node2D
	if turn_system == null or player == null or not turn_system.active or turn_system.current_actor() != player:
		_show_message("Обратиться к противнику можно только на своём ходу.", false)
		return
	if _social_action_used_this_turn:
		_show_message("В этом ходу уже использована содержательная реплика или жест.", false)
		return
	if not _target_is_valid(target):
		_show_message("Выбранная цель больше недоступна для общения.", false)
		return
	if _game.has_method("_set_selected_target"):
		_game.call("_set_selected_target", target)
	var character: PlayerCharacter = _get_player_character()
	var speaker_name: String = character.character_name.strip_edges() if character != null else "Герой"
	if speaker_name.is_empty():
		speaker_name = "Герой"
	var race_id: String = character.race_id if character != null else ""
	var result: Dictionary = _social_system.resolve_action(action_id, speaker_name, target, race_id)
	if not bool(result.get("success", false)):
		_show_message(str(result.get("message", "Свободное действие недоступно.")), false)
		return
	_social_action_used_this_turn = true
	_play_gesture(player, str(result.get("gesture", "")))
	_dialogue_ui.call(
		"show_runtime_response",
		str(result.get("target_name", _target_name(target))),
		str(result.get("dialogue_text", result.get("message", "")))
	)
	_show_message("Свободное действие общения использовано. Обычное действие сохранено.", true)


func _on_dialogue_attack_requested(target: Node) -> void:
	if not _target_is_valid(target):
		_show_message("Эту цель больше нельзя атаковать.", false)
		return
	if _game.has_method("_set_selected_target"):
		_game.call("_set_selected_target", target)
	if _game.has_method("_request_attack"):
		_game.call_deferred("_request_attack")


func _target_is_valid(target: Node) -> bool:
	if target == null or not is_instance_valid(target):
		return false
	if _game.has_method("_target_is_valid"):
		return bool(_game.call("_target_is_valid", target))
	return true


func _target_name(target: Node) -> String:
	if target == null:
		return "Неизвестный"
	return str(target.call("get_combat_name")) if target.has_method("get_combat_name") else str(target.name)


func _play_gesture(player: Node2D, gesture_id: String) -> void:
	if gesture_id.is_empty():
		return
	var body: Node2D = player.get_node_or_null("Body") as Node2D
	if body == null:
		return
	var original_position: Vector2 = body.position
	var original_rotation: float = body.rotation
	var tween: Tween = create_tween()
	if gesture_id == "lower_weapon":
		tween.tween_property(body, "position", original_position + Vector2(0.0, 10.0), 0.16)
		tween.parallel().tween_property(body, "rotation", original_rotation + 0.22, 0.16)
		tween.tween_property(body, "position", original_position, 0.2)
		tween.parallel().tween_property(body, "rotation", original_rotation, 0.2)
	elif gesture_id == "threaten":
		var facing: Vector2 = Vector2.RIGHT
		if player.has_method("get_facing_direction"):
			facing = player.call("get_facing_direction") as Vector2
		tween.tween_property(body, "position", original_position + facing * 13.0, 0.09)
		tween.tween_property(body, "position", original_position - facing * 5.0, 0.09)
		tween.tween_property(body, "position", original_position, 0.12)
	elif gesture_id == "thaumaturgy_voice":
		tween.tween_property(body, "scale", body.scale * 1.08, 0.12)
		tween.tween_property(body, "scale", body.scale, 0.18)


func _sync_player_terrain_trait() -> void:
	var state_value: Variant = _game.get("_player_combat_state")
	if not state_value is CombatantState:
		return
	var character: PlayerCharacter = _get_player_character()
	(state_value as CombatantState).ignores_nonmagical_difficult_terrain = character != null and _class_data.ignores_nonmagical_difficult_terrain(character)


func _get_player_character() -> PlayerCharacter:
	var state: Node = get_node_or_null("/root/GameState")
	if state == null:
		return null
	var value: Variant = state.get("player_character")
	return value as PlayerCharacter if value is PlayerCharacter else null


func _show_message(text: String, positive: bool) -> void:
	if _game.has_method("show_combat_message"):
		_game.call("show_combat_message", text, positive)


func social_action_used_for_testing() -> bool:
	return _social_action_used_this_turn
