extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const STABILIZE_LABEL: String = "МЕДИЦИНА: СТАБИЛИЗИРОВАТЬ ИРИНУ"
const RECOVER_LABEL: String = "МЕДИЦИНА: ПРИВЕСТИ ИРИНУ В СОЗНАНИЕ"

var _completed: bool = false
var _stage: String = "init"


func _init() -> void:
	call_deferred("_run")
	call_deferred("_watchdog")


func _watchdog() -> void:
	await create_timer(40.0).timeout
	if not _completed:
		_fail("Irina field support/visibility/follow test timed out at stage: %s" % _stage)


func _run() -> void:
	_stage = "setup"
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())
	state.set("inventory", {})
	state.call("add_item", "healers_kit", 4, false)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(24):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var ally: ControllableAlly = game.call("get_controllable_ally_for_testing") as ControllableAlly
	var room: GuardPostPartyVisibility = game.get_node_or_null("StealthTestRoom") as GuardPostPartyVisibility
	if player == null or ally == null or room == null:
		_fail("Player, Irina or room fixture is missing.")
		return

	_stage = "medicine_stabilization"
	ally.global_position = player.global_position + Vector2(32.0, 0.0)
	ally.enter_dying()
	var entries: Dictionary = game.call("get_action_catalog_entries_for_testing") as Dictionary
	if not _has_action_label(entries, STABILIZE_LABEL):
		_fail("Action catalogue does not expose deterministic Irina stabilization.")
		return
	var stabilize: Dictionary = game.call("attempt_controllable_ally_medicine_for_testing", 20) as Dictionary
	if not bool(stabilize.get("success", false)) or not ally.get_combatant_state().stable:
		_fail("Successful Medicine check did not stabilize Irina: %s" % stabilize)
		return
	if ally.current_health != 0:
		_fail("Stabilization unexpectedly restored hit points.")
		return

	_stage = "medicine_consciousness"
	entries = game.call("get_action_catalog_entries_for_testing") as Dictionary
	if not _has_action_label(entries, RECOVER_LABEL):
		_fail("Stable Irina does not expose the second-stage consciousness action.")
		return
	var recovery: Dictionary = game.call("attempt_controllable_ally_medicine_for_testing", 20) as Dictionary
	if not bool(recovery.get("success", false)) or ally.current_health != 1:
		_fail("Second successful Medicine check did not restore Irina to 1 HP: %s" % recovery)
		return
	if ally.get_combatant_state().stable:
		_fail("Conscious Irina retained the stale stabilization flag.")
		return
	if (
		ally.get_combatant_state().has_condition("unconscious")
		or ally.get_combatant_state().has_condition("incapacitated")
	):
		_fail("Conscious Irina retained an incapacitating zero-HP condition.")
		return
	if int(state.call("get_item_count", "healers_kit")) != 2:
		_fail("Two successful field-support stages did not consume exactly two kit uses.")
		return

	_stage = "visibility_source"
	game.call("request_party_mode_for_testing", "solo")
	game.call("request_party_member_control_for_testing", ally.character_id)
	for _frame: int in range(4):
		await physics_frame
	var fog: PartyRoomFogOverlay = room.get_room_fog_for_testing() as PartyRoomFogOverlay
	if fog == null or fog.get_vision_source_for_testing() != ally:
		_fail("Solo control did not move fog-of-war vision to Irina.")
		return
	game.call("request_party_mode_for_testing", "party")
	for _frame: int in range(4):
		await physics_frame
	if fog.get_vision_source_for_testing() != player:
		_fail("Party mode did not return fog-of-war vision to the main hero.")
		return

	_stage = "follow_pathfinding"
	game.call("request_party_mode_for_testing", "solo")
	room.open_inner_gate("field_support_test")
	for _frame: int in range(6):
		await physics_frame
	var grid: BattleGrid = root.get_tree().get_first_node_in_group("battle_grid") as BattleGrid
	if grid == null:
		_fail("BattleGrid fixture is missing.")
		return
	var partition_x: float = room.get_inner_partition_global_x()
	ally.global_position = grid.cell_to_world_center(
		grid.world_to_cell(room.to_global(Vector2(548.0, -190.0)))
	)
	player.global_position = grid.cell_to_world_center(
		grid.world_to_cell(room.to_global(Vector2(716.0, -190.0)))
	)
	game.call("request_party_mode_for_testing", "party")
	var initial_distance: float = ally.global_position.distance_to(player.global_position)
	for _frame: int in range(24):
		await physics_frame
	var path: Array[Vector2i] = game.call("get_field_follow_path_for_testing") as Array[Vector2i]
	if path.size() <= 2:
		_fail("Irina follow did not build an obstacle-aware route around the partition.")
		return
	for _frame: int in range(360):
		await physics_frame
		if ally.global_position.distance_to(player.global_position) <= 96.0:
			break
	var final_distance: float = ally.global_position.distance_to(player.global_position)
	if final_distance >= initial_distance - 40.0:
		_fail("Irina did not make meaningful progress along the follow route.")
		return
	if ally.global_position.x <= partition_x:
		_fail("Irina remained stuck against the partition instead of using the open gate.")
		return

	game.queue_free()
	await process_frame
	_completed = true
	print("Irina field support, solo visibility and obstacle-aware follow passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Полевой лекарь"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.maximum_health = 16
	hero.current_health = 16
	hero.abilities["wisdom"] = 10
	hero.starter_loadout_granted = true
	return hero


func _has_action_label(entries: Dictionary, expected: String) -> bool:
	for category_id: String in ["action", "bonus", "free", "reaction"]:
		var values: Variant = entries.get(category_id, [])
		if not values is Array:
			continue
		for value: Variant in values as Array:
			if value is Dictionary and str((value as Dictionary).get("label", "")) == expected:
				return true
	return false


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
