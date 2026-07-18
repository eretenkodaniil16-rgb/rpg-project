extends "res://scripts/game/game_planned_combat.gd"

const TERRAIN_MOVEMENT_SCRIPT: Script = preload("res://scripts/systems/terrain_aware_movement_system.gd")
const COMBAT_SOCIAL_SCRIPT: Script = preload("res://scripts/systems/combat_social_action_system.gd")

var _combat_social: CombatSocialActionSystem = COMBAT_SOCIAL_SCRIPT.new() as CombatSocialActionSystem
var _social_action_used_this_turn: bool = false
var _free_category_button: Button


func _ready() -> void:
	super._ready()
	_movement_planner = TERRAIN_MOVEMENT_SCRIPT.new() as TerrainAwareMovementSystem
	_sync_player_terrain_trait()
	_install_free_action_category()
	_invalidate_reachable_area()
	_refresh_reachable_area(true)
	_refresh_action_catalog()


func _process(delta: float) -> void:
	_sync_player_terrain_trait()
	super._process(delta)


func _begin_current_turn() -> void:
	if _turn_system.current_actor() == player:
		_social_action_used_this_turn = false
	super._begin_current_turn()


func _build_catalog_entries() -> Dictionary:
	var entries: Dictionary = super._build_catalog_entries()
	var player_turn: bool = _turn_system.active and _turn_system.is_player_turn(player) and not _enemy_turn_running
	var target_valid: bool = _target_is_valid(_selected_target)
	var free_entries: Array[Dictionary] = []
	for action: Dictionary in _combat_social.get_actions():
		var action_id: String = str(action.get("id", ""))
		free_entries.append(_entry(
			"social:%s" % action_id,
			str(action.get("label", "ОБЩЕНИЕ")),
			player_turn and target_valid and not _social_action_used_this_turn,
			str(action.get("description", "Короткая реплика или жест без расхода действия.")),
			str(action.get("kind", "speech"))
		))
	entries["free"] = free_entries
	return entries


func _on_catalog_action_requested(action_id: String) -> void:
	if action_id.begins_with("social:"):
		_perform_combat_social_action(action_id.trim_prefix("social:"))
		return
	super._on_catalog_action_requested(action_id)


func _perform_combat_social_action(action_id: String) -> void:
	if not _turn_system.active or not _turn_system.is_player_turn(player) or _enemy_turn_running:
		show_combat_message("Обратиться к противнику можно только на своём ходу.", false)
		return
	if _social_action_used_this_turn:
		show_combat_message("В этом ходу уже использована содержательная реплика или жест.", false)
		return
	if not _target_is_valid(_selected_target):
		show_combat_message("Сначала выберите противника, к которому хотите обратиться.", false)
		return
	var speaker_name: String = GameState.player_character.character_name.strip_edges()
	if speaker_name.is_empty():
		speaker_name = "Герой"
	var result: Dictionary = _combat_social.resolve_action(action_id, speaker_name, _selected_target)
	if not bool(result.get("success", false)):
		show_combat_message(str(result.get("message", "Свободное действие недоступно.")), false)
		return
	_social_action_used_this_turn = true
	if _action_catalog_ui != null:
		_action_catalog_ui.close_catalog()
	_play_social_gesture(str(result.get("gesture", "")))
	show_combat_message(str(result.get("message", "")), true)
	_refresh_action_catalog()


func _play_social_gesture(gesture_id: String) -> void:
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
		var facing: Vector2 = _get_player_facing_direction()
		tween.tween_property(body, "position", original_position + facing * 13.0, 0.09)
		tween.tween_property(body, "position", original_position - facing * 5.0, 0.09)
		tween.tween_property(body, "position", original_position, 0.12)


func _install_free_action_category() -> void:
	if _action_catalog_ui == null or _action_catalog_ui.category_row == null:
		return
	if _action_catalog_ui.category_row.get_node_or_null("FreeCategoryButton") != null:
		return
	_free_category_button = Button.new()
	_free_category_button.name = "FreeCategoryButton"
	_free_category_button.text = "СВОБОДНОЕ"
	_free_category_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_free_category_button.pressed.connect(Callable(_action_catalog_ui, "_select_category").bind("free"))
	_action_catalog_ui.category_row.add_child(_free_category_button)
	_action_catalog_ui.category_row.move_child(_free_category_button, 2)


func _sync_player_terrain_trait() -> void:
	if _player_combat_state == null:
		return
	_player_combat_state.ignores_nonmagical_difficult_terrain = _class_data.ignores_nonmagical_difficult_terrain(GameState.player_character)


func social_action_available_for_testing() -> bool:
	return _turn_system.active and _turn_system.is_player_turn(player) and not _social_action_used_this_turn
