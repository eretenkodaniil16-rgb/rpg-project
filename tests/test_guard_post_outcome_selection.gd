extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const FIRST_ROOM_ACTOR_IDS: Array[String] = ["caretaker", "service_guard"]
const SECOND_ROOM_ACTOR_IDS: Array[String] = ["training_marksman", "training_mage"]


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())
	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Guard post game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(20):
		await process_frame
	game.set_process(false)

	if not _validate_room_outcomes(game, FIRST_ROOM_ACTOR_IDS, false):
		return
	if not _validate_room_outcomes(game, SECOND_ROOM_ACTOR_IDS, true):
		return

	game.queue_free()
	await process_frame
	print("Both guard-post rooms distinguish lethal, nonlethal, mixed and incomplete outcomes.")
	quit(0)


func _validate_room_outcomes(game: Node, actor_ids: Array[String], inner_room: bool) -> bool:
	var all_unconscious: Dictionary = {}
	var all_dead: Dictionary = {}
	var mixed: Dictionary = {}
	var incomplete: Dictionary = {}
	for index: int in range(actor_ids.size()):
		var actor_id: String = actor_ids[index]
		all_unconscious[actor_id] = "unconscious"
		all_dead[actor_id] = "dead"
		mixed[actor_id] = "dead" if index == 0 else "unconscious"
		incomplete[actor_id] = "active" if index == 0 else "unconscious"

	var subdued_id: String = "inner_watch_subdued" if inner_room else "guards_subdued"
	var defeated_id: String = "inner_watch_defeated" if inner_room else "guards_defeated"
	var mixed_id: String = "inner_watch_mixed" if inner_room else "mixed_neutralization"
	if str(game.call("_resolution_for_actor_states", all_unconscious, inner_room)) != subdued_id:
		_fail("All-unconscious room outcome is not nonlethal: %s" % JSON.stringify(actor_ids))
		return false
	if str(game.call("_resolution_for_actor_states", all_dead, inner_room)) != defeated_id:
		_fail("All-dead room outcome is not lethal: %s" % JSON.stringify(actor_ids))
		return false
	if str(game.call("_resolution_for_actor_states", mixed, inner_room)) != mixed_id:
		_fail("Mixed room outcome is not distinguished: %s" % JSON.stringify(actor_ids))
		return false
	if not str(game.call("_resolution_for_actor_states", incomplete, inner_room)).is_empty():
		_fail("Room resolved while an active participant remained: %s" % JSON.stringify(actor_ids))
		return false
	return true


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель исходов"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 3
	hero.maximum_health = 28
	hero.current_health = 28
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
