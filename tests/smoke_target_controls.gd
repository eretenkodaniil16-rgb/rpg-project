extends SceneTree

const GAME_SCENE := "res://scenes/game/game.tscn"

func _init() -> void:
	call_deferred("_run")

func _fail(message: String) -> void:
	push_error(message)
	quit(1)

func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("Missing GameState.")
		return
	state.call("new_game")
	var ranger := PlayerCharacter.new()
	ranger.character_name = "Лучник"
	ranger.character_class_id = "ranger"
	ranger.character_class_name = "Следопыт"
	ranger.maximum_health = 12
	ranger.current_health = 12
	ranger.abilities["dexterity"] = 16
	state.set("player_character", ranger)
	state.set("player_position", Vector2(320, 360))
	var packed := load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate()
	root.add_child(game)
	await process_frame
	await process_frame
	await process_frame
	var action: Button = game.find_child("AttackButton", true, false) as Button
	var selector: Button = game.find_child("TargetButton", true, false) as Button
	var label: Label = game.find_child("TargetLabel", true, false) as Label
	var feed: CombatEventFeed = game.find_child("CombatEventFeed", true, false) as CombatEventFeed
	var dice: D20RollOverlay = game.find_child("D20RollOverlay", true, false) as D20RollOverlay
	var caretaker: Node = game.get_node_or_null("Caretaker")
	var dummy: Node = game.get_node_or_null("TrainingDummy")
	if action == null or selector == null or label == null or feed == null or dice == null:
		_fail("Target controls or combat presentation nodes are missing.")
		return
	if caretaker == null or dummy == null:
		_fail("Room targets missing.")
		return
	if not caretaker.is_in_group("combat_targets") or not dummy.is_in_group("combat_targets"):
		_fail("Target group registration failed.")
		return
	game.call("_set_selected_target", caretaker)
	await process_frame
	var arrows_before: int = int(state.call("get_item_count", "arrow"))
	game.call("_request_attack")
	await process_frame
	if int(state.call("get_item_count", "arrow")) != arrows_before - 1:
		_fail("Arrow count did not change.")
		return
	var projectile_found: bool = false
	for child: Node in game.get_children():
		if child is RangedProjectile:
			projectile_found = true
			break
	if not projectile_found:
		_fail("Ranged attack did not create a projectile visual.")
		return
	await create_timer(0.9).timeout
	if feed.card_count() < 1:
		_fail("Combat event feed did not receive the ranged attack result.")
		return
	if dice.queued_roll_count() < 1:
		_fail("D20 presentation did not receive the ranged attack roll.")
		return
	print("Target controls and compact combat presentation smoke test passed.")
	quit(0)
