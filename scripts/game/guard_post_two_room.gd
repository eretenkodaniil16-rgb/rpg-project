class_name GuardPostTwoRoom
extends "res://scripts/game/stealth_test_room.gd"

const INNER_GATE_SCRIPT: Script = preload("res://scripts/game/stealth_door.gd")

const INNER_PARTITION_LOCAL_X: float = 632.0
const INNER_PARTITION_THICKNESS: float = 4.0
const INNER_PARTITION_TOP_SIZE: Vector2 = Vector2(INNER_PARTITION_THICKNESS, 251.0)
const INNER_PARTITION_BOTTOM_SIZE: Vector2 = Vector2(INNER_PARTITION_THICKNESS, 251.0)
const INNER_GATE_SIZE: Vector2 = Vector2(INNER_PARTITION_THICKNESS, 128.0)
const INNER_PARTITION_TOP_ID: String = "inner_partition_top"
const INNER_PARTITION_BOTTOM_ID: String = "inner_partition_bottom"
const INNER_GATE_BLOCKER_ID: String = "inner_watch_gate_blocker"
const INNER_GATE_ID: String = "inner_watch_gate"

const MODE_SEALED: String = "sealed"
const MODE_AUTHORIZED: String = "authorized"
const MODE_WATCHING: String = "watching"
const MODE_HOSTILE: String = "hostile"

var _inner_gate: StealthDoor
var _inner_navigation_region: NavigationRegion2D
var _inner_gate_navigation_link: NavigationLink2D
var _inner_watch_engaged: bool = false
var _inner_watch_mode: String = MODE_SEALED


func _ready() -> void:
	super._ready()
	_build_wall(
		"InnerPartitionTop",
		Vector2(INNER_PARTITION_LOCAL_X, -189.5),
		INNER_PARTITION_TOP_SIZE
	)
	_build_wall(
		"InnerPartitionBottom",
		Vector2(INNER_PARTITION_LOCAL_X, 189.5),
		INNER_PARTITION_BOTTOM_SIZE
	)
	_inner_gate = INNER_GATE_SCRIPT.new() as StealthDoor
	_inner_gate.name = "InnerWatchGate"
	_inner_gate.position = Vector2(INNER_PARTITION_LOCAL_X, 0.0)
	_inner_gate.door_id = INNER_GATE_ID
	_inner_gate.door_label = "Внутренняя дверь караульного поста"
	_inner_gate.door_size = INNER_GATE_SIZE
	add_child(_inner_gate)
	_inner_gate.set_door_state("open" if _inner_gate_should_start_open() else "locked", false)
	_apply_persisted_inner_watch_mode()
	queue_redraw()


func get_inner_gate() -> StealthDoor:
	return _inner_gate


func get_inner_partition_global_x() -> float:
	return to_global(Vector2(INNER_PARTITION_LOCAL_X, 0.0)).x


func get_inner_watch_mode_for_testing() -> String:
	return _inner_watch_mode


func open_inner_gate(reason_id: String = "") -> void:
	var state: Node = _game_state()
	if state != null:
		state.call("set_flag", "vault_inner_gate_open", true)
		if not reason_id.is_empty():
			state.call("set_flag", "vault_inner_gate_open_reason", reason_id)
	if _inner_gate != null and _inner_gate.get_door_state() != "open":
		_inner_gate.set_door_state("open", false)


func set_inner_watch_mode(mode: String) -> void:
	if mode not in [MODE_SEALED, MODE_AUTHORIZED, MODE_WATCHING, MODE_HOSTILE]:
		return
	_inner_watch_mode = mode
	_inner_watch_engaged = mode == MODE_HOSTILE
	for actor: Node2D in [_training_marksman, _training_mage]:
		if not is_instance_valid(actor):
			continue
		match mode:
			MODE_SEALED:
				actor.remove_from_group("combat_targets")
				actor.remove_from_group("stealth_alert_actors")
			MODE_AUTHORIZED:
				actor.remove_from_group("combat_targets")
				actor.remove_from_group("stealth_alert_actors")
				actor.add_to_group("context_action_targets")
				actor.set("hostile", false)
				if actor.has_method("set_exploration_alert_state"):
					actor.call("set_exploration_alert_state", StealthAlertSystem.STATE_CALM, 0.0, Vector2.ZERO)
			MODE_WATCHING:
				if not actor.is_in_group("combat_targets"):
					actor.add_to_group("combat_targets")
				if not actor.is_in_group("stealth_alert_actors"):
					actor.add_to_group("stealth_alert_actors")
				actor.set("hostile", false)
			MODE_HOSTILE:
				if not actor.is_in_group("combat_targets"):
					actor.add_to_group("combat_targets")
				if not actor.is_in_group("stealth_alert_actors"):
					actor.add_to_group("stealth_alert_actors")
				if actor.has_method("activate_combat_participant"):
					actor.call("activate_combat_participant")


func activate_inner_watch_combat() -> void:
	_inner_watch_engaged = true
	set_inner_watch_mode(MODE_HOSTILE)


func activate_tactical_training_squad() -> void:
	if _activating_tactical_squad:
		return
	_activating_tactical_squad = true
	if _inner_watch_engaged:
		for actor: Node2D in [_training_marksman, _training_mage]:
			if is_instance_valid(actor) and actor.has_method("activate_combat_participant"):
				actor.call("activate_combat_participant")
	elif is_instance_valid(_patrol_observer) and _patrol_observer.has_method("activate_combat_participant"):
		_patrol_observer.call("activate_combat_participant")
	_activating_tactical_squad = false


func _prepare_dormant_training_actor(actor: Node2D) -> void:
	actor.remove_from_group("stealth_alert_actors")
	actor.remove_from_group("combat_targets")
	actor.add_to_group("context_action_targets")


func set_navigation_door_state(door_id: String, door_state: String) -> void:
	if door_id != INNER_GATE_ID:
		super.set_navigation_door_state(door_id, door_state)
		return
	if _inner_gate_navigation_link != null:
		_inner_gate_navigation_link.enabled = door_state in ["open", "broken"]
	if _combat_environment != null:
		var should_block: bool = door_state not in ["open", "broken"]
		_combat_environment.set_cover_object_active(INNER_GATE_BLOCKER_ID, should_block, false)
		_combat_environment.set_edge_blocker_active(INNER_GATE_BLOCKER_ID, should_block)


func _register_combat_obstacles() -> void:
	await super._register_combat_obstacles()
	if _combat_environment == null:
		return
	var grid: BattleGrid = get_tree().get_first_node_in_group("battle_grid") as BattleGrid
	if grid == null:
		return
	var top_wall: Node2D = get_node_or_null("InnerPartitionTop") as Node2D
	var bottom_wall: Node2D = get_node_or_null("InnerPartitionBottom") as Node2D
	if top_wall != null:
		var top_rect: Rect2 = _rect_around(top_wall.global_position, INNER_PARTITION_TOP_SIZE)
		_add_environment_obstacle(INNER_PARTITION_TOP_ID, top_rect, true, false, true, false)
		_combat_environment.register_edge_blocker(
			INNER_PARTITION_TOP_ID,
			_vertical_edge_pairs(grid, top_wall.global_position.x, top_rect),
			true
		)
	if bottom_wall != null:
		var bottom_rect: Rect2 = _rect_around(bottom_wall.global_position, INNER_PARTITION_BOTTOM_SIZE)
		_add_environment_obstacle(INNER_PARTITION_BOTTOM_ID, bottom_rect, true, false, true, false)
		_combat_environment.register_edge_blocker(
			INNER_PARTITION_BOTTOM_ID,
			_vertical_edge_pairs(grid, bottom_wall.global_position.x, bottom_rect),
			true
		)
	if _inner_gate != null:
		var gate_active: bool = _inner_gate.get_door_state() not in ["open", "broken"]
		_add_environment_obstacle(
			INNER_GATE_BLOCKER_ID,
			_inner_gate.get_world_rect(),
			true,
			false,
			gate_active,
			false
		)
		_combat_environment.register_edge_blocker(
			INNER_GATE_BLOCKER_ID,
			_vertical_edge_pairs(grid, _inner_gate.global_position.x, _inner_gate.get_world_rect()),
			gate_active
		)
	_combat_environment.call("_rebuild_collision_bodies")
	_combat_environment.queue_redraw()


func _build_navigation() -> void:
	_west_navigation_region = _build_navigation_region(
		"WestServiceNavigationRegion",
		Rect2(Vector2(-200.0, -315.0), Vector2(192.0, 630.0))
	)
	_hall_navigation_region = _build_navigation_region(
		"OuterGuardRoomNavigationRegion",
		Rect2(Vector2(PARTITION_LOCAL_X, -315.0), Vector2(INNER_PARTITION_LOCAL_X - PARTITION_LOCAL_X, 630.0))
	)
	_inner_navigation_region = _build_navigation_region(
		"InnerWatchRoomNavigationRegion",
		Rect2(Vector2(INNER_PARTITION_LOCAL_X, -315.0), Vector2(358.0, 630.0))
	)
	_door_navigation_link = NavigationLink2D.new()
	_door_navigation_link.name = "WestServiceDoorNavigationLink"
	_door_navigation_link.start_position = Vector2(-40.0, 5.0)
	_door_navigation_link.end_position = Vector2(24.0, 5.0)
	_door_navigation_link.bidirectional = true
	_door_navigation_link.enter_cost = 0.0
	_door_navigation_link.travel_cost = 1.0
	_door_navigation_link.enabled = false
	add_child(_door_navigation_link)
	_inner_gate_navigation_link = NavigationLink2D.new()
	_inner_gate_navigation_link.name = "InnerWatchGateNavigationLink"
	_inner_gate_navigation_link.start_position = Vector2(INNER_PARTITION_LOCAL_X - 32.0, 0.0)
	_inner_gate_navigation_link.end_position = Vector2(INNER_PARTITION_LOCAL_X + 32.0, 0.0)
	_inner_gate_navigation_link.bidirectional = true
	_inner_gate_navigation_link.enter_cost = 0.0
	_inner_gate_navigation_link.travel_cost = 1.0
	_inner_gate_navigation_link.enabled = false
	add_child(_inner_gate_navigation_link)


func _draw() -> void:
	super._draw()
	var first_room := Rect2(Vector2(PARTITION_LOCAL_X, -315.0), Vector2(INNER_PARTITION_LOCAL_X - PARTITION_LOCAL_X, 630.0))
	var second_room := Rect2(Vector2(INNER_PARTITION_LOCAL_X, -315.0), Vector2(358.0, 630.0))
	draw_rect(first_room, Color(0.18, 0.13, 0.09, 0.16), true)
	draw_rect(second_room, Color(0.09, 0.12, 0.2, 0.2), true)
	draw_rect(first_room, Color(0.5, 0.38, 0.26, 0.65), false, 2.0)
	draw_rect(second_room, Color(0.28, 0.42, 0.62, 0.7), false, 2.0)
	draw_string(
		ThemeDB.fallback_font,
		Vector2(42.0, -280.0),
		"ПЕРВАЯ КОМНАТА · СМОТРИТЕЛЬ И ДОЗОРНЫЙ",
		HORIZONTAL_ALIGNMENT_LEFT,
		500.0,
		15,
		Color(0.88, 0.72, 0.48, 0.9)
	)
	draw_string(
		ThemeDB.fallback_font,
		Vector2(INNER_PARTITION_LOCAL_X + 28.0, -280.0),
		"ВНУТРЕННИЙ ПОСТ",
		HORIZONTAL_ALIGNMENT_LEFT,
		290.0,
		15,
		Color(0.58, 0.76, 1.0, 0.92)
	)


func _inner_gate_should_start_open() -> bool:
	var state: Node = _game_state()
	return state != null and bool(state.call("get_flag", "vault_inner_gate_open", false))


func _apply_persisted_inner_watch_mode() -> void:
	var state: Node = _game_state()
	if state == null:
		set_inner_watch_mode(MODE_SEALED)
		return
	var outcome: String = str(state.call("get_flag", "vault_guard_post_room1_outcome", ""))
	match outcome:
		"peaceful": set_inner_watch_mode(MODE_AUTHORIZED)
		"stealth": set_inner_watch_mode(MODE_WATCHING)
		_: set_inner_watch_mode(MODE_SEALED)


func _game_state() -> Node:
	return get_tree().root.get_node_or_null("GameState") if is_inside_tree() else null
