extends "res://scripts/game/game_guard_post_two_room_runtime.gd"

const FIRST_ROOM_PARLEY_ACTOR_IDS: Array[String] = ["caretaker", "service_guard"]
const SERVICE_GUARD_NOTICED_FLAG: String = "vault_guard_post_service_guard_noticed"
const INNER_AI_WATCHDOG_SECONDS: float = 0.8
const VISIBILITY_SAVE_MAIN_MENU_SCENE: String = "res://scenes/menus/main_menu.tscn"
const VISIBILITY_SAVE_GAME_SCENE: String = "res://scenes/game/game.tscn"
const VISIBILITY_SAVE_CHARACTER_CREATOR_SCENE: String = "res://scenes/character_creation/character_creator.tscn"
const PAUSE_SAVE_MENU_SCRIPT: Script = preload("res://scripts/ui/game_pause_save_menu.gd")

var _inner_ai_watchdog_elapsed: float = 0.0
var _inner_ai_watchdog_actor_id: String = ""
var _inner_ai_turn_started: Dictionary = {}
var _inner_ai_turn_completed: Dictionary = {}
var _peaceful_cleanup_applied: bool = false
var _pause_save_menu: GamePauseSaveMenu
var _defeat_transition_running: bool = false


func _ready() -> void:
	super._ready()
	_settle_pending_peaceful_outcome()
	_install_pause_save_menu()


func _process(delta: float) -> void:
	# Dialogue choices set their flags before the dialogue panel closes. Resolve
	# and clean the peaceful route before exploration detection receives a frame.
	_settle_pending_peaceful_outcome()
	super._process(delta)
	_clear_concealed_manual_target()
	_maintain_inner_watch_ai(delta)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") and is_instance_valid(_pause_save_menu) and _pause_save_menu.is_menu_open():
		_pause_save_menu.close_menu()
		get_viewport().set_input_as_handled()
		return
	super._unhandled_input(event)


func return_to_menu() -> void:
	if not is_instance_valid(_pause_save_menu):
		return
	if GameState.input_locked and not _pause_save_menu.is_menu_open():
		return
	_pause_save_menu.toggle_menu()


func _any_overlay_visible() -> bool:
	return super._any_overlay_visible() or (is_instance_valid(_pause_save_menu) and _pause_save_menu.is_menu_open())


func _target_is_valid(target: Node) -> bool:
	return super._target_is_valid(target) and _target_is_visible_to_player(target)


func _cycle_target() -> void:
	if GameState.input_locked or _attack_in_progress or _any_overlay_visible():
		return
	if _turn_system.active and not _turn_system.is_player_turn(player):
		show_combat_message("Сейчас ход другого участника.", false)
		return
	var targets: Array[Node] = _visible_active_targets()
	if targets.is_empty():
		_set_selected_target(null)
		show_combat_message("В поле зрения нет доступных целей.", false)
		return
	var current_index: int = targets.find(_selected_target)
	if current_index < 0:
		_set_selected_target(targets[0])
		show_combat_message("Цель выбрана. Расстояние показано на поле.", true)
	elif current_index + 1 < targets.size():
		_set_selected_target(targets[current_index + 1])
		show_combat_message("Выбрана следующая видимая цель.", true)
	else:
		_set_selected_target(null)
		show_combat_message("Цель снята.", true)


func handle_player_defeat(_source: Node = null) -> void:
	if _defeat_transition_running:
		return
	_defeat_transition_running = true
	GameState.input_locked = true
	if GameState.has_manual_save():
		show_combat_message("Персонаж погиб. Загружается последнее ручное сохранение.", false)
		await get_tree().create_timer(1.0).timeout
		if GameState.load_last_manual_save():
			GameState.input_locked = false
			get_tree().change_scene_to_file(VISIBILITY_SAVE_GAME_SCENE)
			return
		show_combat_message("Последнее сохранение повреждено. Начинается новая игра.", false)
	else:
		show_combat_message("Персонаж погиб. Ручных сохранений нет — игра начнётся сначала.", false)
		await get_tree().create_timer(1.0).timeout
	GameState.discard_autosave()
	GameState.new_game()
	GameState.input_locked = false
	get_tree().change_scene_to_file(VISIBILITY_SAVE_CHARACTER_CREATOR_SCENE)


func _broadcast_actor_alert(actor: Node, record: Dictionary) -> void:
	# The neutral caretaker does not raise a squad-wide hostile alert merely from
	# seeing the hero. The service guard may still relay a confirmed local alert
	# to the caretaker as an investigation; _begin_combat_from_alert keeps both
	# actors non-hostile until explicit provocation.
	if _actor_id(actor) == CARETAKER_ACTOR_ID and _first_room_actor_should_remain_neutral(actor):
		return
	super._broadcast_actor_alert(actor, record)


func _begin_combat_from_alert(actor: Node, record: Dictionary) -> void:
	if _first_room_actor_should_remain_neutral(actor):
		_handle_neutral_first_room_detection(actor, record)
		return
	super._begin_combat_from_alert(actor, record)


func _start_inner_watch_combat() -> void:
	if _turn_system.active:
		return
	_prepare_inner_watch_combatants()
	_enemy_turn_running = false
	_inner_ai_watchdog_elapsed = 0.0
	_inner_ai_watchdog_actor_id = ""
	super._start_inner_watch_combat()


func _run_enemy_turn(actor: Node) -> void:
	var actor_id: String = _actor_id(actor)
	if actor_id in SECOND_ROOM_ACTOR_IDS:
		_inner_ai_turn_started[actor_id] = int(_inner_ai_turn_started.get(actor_id, 0)) + 1
	await super._run_enemy_turn(actor)
	if actor_id in SECOND_ROOM_ACTOR_IDS:
		_inner_ai_turn_completed[actor_id] = int(_inner_ai_turn_completed.get(actor_id, 0)) + 1


func _resolve_room(encounter_id: String, resolution_id: String, context: Dictionary) -> void:
	super._resolve_room(encounter_id, resolution_id, context)
	if encounter_id == FIRST_ROOM_ENCOUNTER_ID and resolution_id == "peaceful_passage":
		_apply_peaceful_guard_post_state()


func get_inner_watch_ai_turn_started_for_testing(actor_id: String) -> int:
	return int(_inner_ai_turn_started.get(actor_id, 0))


func get_inner_watch_ai_turn_completed_for_testing(actor_id: String) -> int:
	return int(_inner_ai_turn_completed.get(actor_id, 0))


func prepare_inner_watch_combatants_for_testing() -> void:
	_prepare_inner_watch_combatants()


func get_pause_save_menu_for_testing() -> GamePauseSaveMenu:
	return _pause_save_menu


func get_visible_targets_for_testing() -> Array[Node]:
	return _visible_active_targets()


func _first_room_actor_should_remain_neutral(actor: Node) -> bool:
	var actor_id: String = _actor_id(actor)
	if actor_id not in FIRST_ROOM_PARLEY_ACTOR_IDS:
		return false
	if bool(GameState.get_flag(ROOM_ONE_COMBAT_STARTED_FLAG, false)):
		return false
	if actor.has_method("is_hostile") and bool(actor.call("is_hostile")):
		return false
	var outcome: String = str(GameState.get_flag(ROOM_ONE_OUTCOME_FLAG, ""))
	if outcome == "peaceful":
		return true
	var status: String = str(GameState.get_encounter_status(FIRST_ROOM_ENCOUNTER_ID))
	return status not in [EncounterSystem.STATUS_RESOLVED, EncounterSystem.STATUS_REWARDED]


func _handle_neutral_first_room_detection(actor: Node, record: Dictionary) -> void:
	var actor_id: String = _actor_id(actor)
	if actor_id.is_empty():
		return
	var noticed_flag: String = CARETAKER_NOTICED_FLAG if actor_id == CARETAKER_ACTOR_ID else SERVICE_GUARD_NOTICED_FLAG
	var first_contact: bool = not bool(GameState.get_flag(noticed_flag, false))
	record["state"] = StealthAlertSystem.STATE_SUSPICIOUS
	record["suspicion"] = StealthAlertSystem.SUSPICION_SUSPICIOUS
	record["search_seconds_remaining"] = 0.0
	record["alert_cooldown_seconds"] = 0.0
	_alert_records[actor_id] = record
	if actor.has_method("set_exploration_alert_state"):
		actor.call(
			"set_exploration_alert_state",
			StealthAlertSystem.STATE_SUSPICIOUS,
			StealthAlertSystem.SUSPICION_SUSPICIOUS,
			_stealth_alerts.vector_from_value(record.get("last_known_position", []))
		)
	actor.set("hostile", false)
	GameState.set_flag(noticed_flag, true)
	_persist_alert_record(actor_id, first_contact)
	if not first_contact:
		return
	if actor_id == CARETAKER_ACTOR_ID:
		show_combat_message("Смотритель замечает героя, но не нападает. С ним можно поговорить через ДЕЙСТВИЯ.", true)
	else:
		show_combat_message("Служебный дозорный замечает героя, но ждёт решения Смотрителя.", true)


func _settle_pending_peaceful_outcome() -> void:
	if bool(GameState.get_flag(ROOM_ONE_COMBAT_STARTED_FLAG, false)):
		return
	var outcome: String = str(GameState.get_flag(ROOM_ONE_OUTCOME_FLAG, ""))
	if outcome == "peaceful":
		_apply_peaceful_guard_post_state()
		return
	if not bool(GameState.get_flag("caretaker_convinced", false)) or _turn_system.active:
		return
	var status: String = str(GameState.get_encounter_status(FIRST_ROOM_ENCOUNTER_ID))
	if status == EncounterSystem.STATUS_AVAILABLE and player != null and player.global_position.x >= FIRST_ROOM_APPROACH_X:
		_begin_encounter(FIRST_ROOM_ENCOUNTER_ID, "caretaker_dialogue")
		status = str(GameState.get_encounter_status(FIRST_ROOM_ENCOUNTER_ID))
	if status == EncounterSystem.STATUS_ACTIVE:
		_resolve_room(FIRST_ROOM_ENCOUNTER_ID, "peaceful_passage", {
			"source_type": "dialogue",
			"source_id": "caretaker_convinced_pre_alert"
		})
		_sync_room_from_persistent_state()


func _apply_peaceful_guard_post_state() -> void:
	if _peaceful_cleanup_applied and str(GameState.get_flag(ROOM_ONE_OUTCOME_FLAG, "")) == "peaceful":
		return
	if str(GameState.get_flag(ROOM_ONE_OUTCOME_FLAG, "")) != "peaceful":
		return
	_peaceful_cleanup_applied = true
	for actor_id: String in FIRST_ROOM_PARLEY_ACTOR_IDS:
		var actor: Node = _find_guard_post_actor(actor_id)
		if is_instance_valid(actor):
			actor.set("hostile", false)
			if actor.has_method("set_exploration_alert_state"):
				actor.call("set_exploration_alert_state", StealthAlertSystem.STATE_CALM, 0.0, Vector2.ZERO)
		var record: Dictionary = GameState.get_stealth_alert_record(actor_id)
		record["state"] = StealthAlertSystem.STATE_CALM
		record["suspicion"] = 0.0
		record["last_known_position"] = []
		record["search_seconds_remaining"] = 0.0
		record["alert_cooldown_seconds"] = 0.0
		_alert_records[actor_id] = record
		_alert_broadcasted.erase(actor_id)
		_persist_alert_record(actor_id, false)
	GameState.save_game()


func _find_guard_post_actor(actor_id: String) -> Node:
	for actor: Node in _guard_post_candidate_nodes():
		if is_instance_valid(actor) and _actor_id(actor) == actor_id:
			return actor
	return null


func _prepare_inner_watch_combatants() -> void:
	var room: Node = _two_room_node()
	if room == null:
		return
	if room.has_method("activate_inner_watch_combat"):
		room.call("activate_inner_watch_combat")
	for method_name: String in ["get_training_marksman", "get_training_mage"]:
		if not room.has_method(method_name):
			continue
		var actor: Node = room.call(method_name) as Node
		if not is_instance_valid(actor):
			continue
		if not actor.is_in_group("combat_targets"):
			actor.add_to_group("combat_targets")
		if not actor.is_in_group("stealth_alert_actors"):
			actor.add_to_group("stealth_alert_actors")
		if actor.has_method("activate_combat_participant"):
			actor.call("activate_combat_participant")
		elif actor.has_method("enter_combat_hostile"):
			actor.call("enter_combat_hostile")
		if actor.has_method("set_facing_direction") and player != null:
			actor.call("set_facing_direction", player.global_position - (actor as Node2D).global_position)


func _maintain_inner_watch_ai(delta: float) -> void:
	if not _turn_system.active or _enemy_turn_running:
		_reset_inner_ai_watchdog()
		return
	var actor: Node = _turn_system.current_actor()
	if not is_instance_valid(actor) or actor == player:
		_reset_inner_ai_watchdog()
		return
	var actor_id: String = _actor_id(actor)
	if actor_id not in SECOND_ROOM_ACTOR_IDS:
		_reset_inner_ai_watchdog()
		return
	if _any_overlay_visible():
		return
	if actor_id != _inner_ai_watchdog_actor_id:
		_inner_ai_watchdog_actor_id = actor_id
		_inner_ai_watchdog_elapsed = 0.0
	_inner_ai_watchdog_elapsed += maxf(delta, 0.0)
	if _inner_ai_watchdog_elapsed < INNER_AI_WATCHDOG_SECONDS:
		return
	_inner_ai_watchdog_elapsed = 0.0
	call_deferred("_run_enemy_turn", actor)


func _reset_inner_ai_watchdog() -> void:
	_inner_ai_watchdog_elapsed = 0.0
	_inner_ai_watchdog_actor_id = ""


func _install_pause_save_menu() -> void:
	if is_instance_valid(_pause_save_menu):
		return
	_pause_save_menu = PAUSE_SAVE_MENU_SCRIPT.new() as GamePauseSaveMenu
	_pause_save_menu.name = "GamePauseSaveMenu"
	_pause_save_menu.main_menu_requested.connect(_leave_to_main_menu)
	$Interface.add_child(_pause_save_menu)


func _leave_to_main_menu() -> void:
	GameState.input_locked = false
	GameState.save_game()
	get_tree().change_scene_to_file(VISIBILITY_SAVE_MAIN_MENU_SCENE)


func _visible_active_targets() -> Array[Node]:
	var result: Array[Node] = []
	for target: Node in _available_targets():
		if _target_is_visible_to_player(target):
			result.append(target)
	return result


func _target_is_visible_to_player(target: Node) -> bool:
	if not is_instance_valid(target) or not (target is Node2D):
		return false
	var visibility: Node = get_tree().get_first_node_in_group("player_visibility")
	if visibility == null or not visibility.has_method("is_world_position_visible"):
		return true
	return bool(visibility.call("is_world_position_visible", (target as Node2D).global_position))


func _clear_concealed_manual_target() -> void:
	if is_instance_valid(_selected_target) and not _target_is_visible_to_player(_selected_target):
		_set_selected_target(null)
