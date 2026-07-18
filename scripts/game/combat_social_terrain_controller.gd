class_name CombatSocialTerrainController
extends Node

const TERRAIN_MOVEMENT_SCRIPT: Script = preload("res://scripts/systems/terrain_aware_movement_system.gd")
const SOCIAL_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/combat_social_action_system.gd")

var _game: Node
var _action_ui: ActionCatalogUI
var _social_system: CombatSocialActionSystem = SOCIAL_SYSTEM_SCRIPT.new() as CombatSocialActionSystem
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
	_game.set("_movement_planner", TERRAIN_MOVEMENT_SCRIPT.new() as TerrainAwareMovementSystem)
	_install_free_category_button()
	if not _action_ui.action_requested.is_connected(_on_action_requested):
		_action_ui.action_requested.connect(_on_action_requested)
	_initialized = true
	_sync_player_terrain_trait()
	if _game.has_method("_invalidate_reachable_area"):
		_game.call("_invalidate_reachable_area")


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
	var target_valid: bool = selected_target != null and is_instance_valid(selected_target)
	if _game.has_method("_target_is_valid"):
		target_valid = bool(_game.call("_target_is_valid", selected_target))
	var free_entries: Array[Dictionary] = []
	for action: Dictionary in _social_system.get_actions():
		free_entries.append({
			"id": "social:%s" % str(action.get("id", "")),
			"label": str(action.get("label", "ОБЩЕНИЕ")),
			"enabled": player_turn and target_valid and not _social_action_used_this_turn,
			"description": str(action.get("description", "Короткая реплика или жест без расхода действия.")),
			"group": str(action.get("kind", "speech"))
		})
	var entries_value: Variant = _action_ui.get("_entries")
	var entries: Dictionary = (entries_value as Dictionary).duplicate(true) if entries_value is Dictionary else {}
	entries["free"] = free_entries
	_action_ui.set("_entries", entries)
	if _action_ui.panel.visible and str(_action_ui.get("_selected_category")) == "free":
		_action_ui.call("_rebuild_action_grid")


func _on_action_requested(action_id: String) -> void:
	if not action_id.begins_with("social:"):
		return
	_perform_social_action(action_id.trim_prefix("social:"))


func _perform_social_action(action_id: String) -> void:
	var turn_system: TurnBasedCombatSystem = _game.get("_turn_system") as TurnBasedCombatSystem
	var player: Node2D = _game.get_node_or_null("Player") as Node2D
	var target: Node = _game.get("_selected_target") as Node
	if turn_system == null or player == null or not turn_system.active or turn_system.current_actor() != player:
		_show_message("Обратиться к противнику можно только на своём ходу.", false)
		return
	if _social_action_used_this_turn:
		_show_message("В этом ходу уже использована содержательная реплика или жест.", false)
		return
	if target == null or not is_instance_valid(target):
		_show_message("Сначала выберите противника, к которому хотите обратиться.", false)
		return
	if _game.has_method("_target_is_valid") and not bool(_game.call("_target_is_valid", target)):
		_show_message("Выбранная цель больше недоступна для общения.", false)
		return
	var speaker_name: String = GameState.player_character.character_name.strip_edges()
	if speaker_name.is_empty():
		speaker_name = "Герой"
	var result: Dictionary = _social_system.resolve_action(action_id, speaker_name, target)
	if not bool(result.get("success", false)):
		_show_message(str(result.get("message", "Свободное действие недоступно.")), false)
		return
	_social_action_used_this_turn = true
	_action_ui.close_catalog()
	_play_gesture(player, str(result.get("gesture", "")))
	_show_message(str(result.get("message", "")), true)


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


func _sync_player_terrain_trait() -> void:
	var state_value: Variant = _game.get("_player_combat_state")
	if not state_value is CombatantState:
		return
	var class_data := ClassDataSystem.new()
	(state_value as CombatantState).ignores_nonmagical_difficult_terrain = class_data.ignores_nonmagical_difficult_terrain(GameState.player_character)


func _show_message(text: String, positive: bool) -> void:
	if _game.has_method("show_combat_message"):
		_game.call("show_combat_message", text, positive)


func social_action_used_for_testing() -> bool:
	return _social_action_used_this_turn
