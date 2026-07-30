extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null or not state.has_method("resolve_encounter"):
		_fail("Encounter-aware GameState is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path("user://savegame.json")
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	state.call("new_game")
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель сцены"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 1
	hero.maximum_health = 14
	hero.current_health = 14
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	state.set("player_character", hero)

	var scene: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if scene == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = scene.instantiate()
	root.add_child(game)
	for _frame: int in range(5):
		await process_frame
	if str(game.get_script().resource_path) != "res://scripts/game/game_advanced_combat_ai_runtime.gd":
		_fail("Game scene does not use the Combat AI runtime layered above pursuit and unified encounters.")
		return

	var dummy: Node = null
	for candidate: Node in get_nodes_in_group("combat_targets"):
		if candidate.has_method("get_encounter_id") and str(candidate.call("get_encounter_id")) == "training_construct":
			dummy = candidate
			break
	if dummy == null:
		_fail("Training dummy encounter actor is missing.")
		return
	game.call("_start_turn_based_combat", dummy)
	await process_frame
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_ACTIVE:
		_fail("Combat runtime did not start the actor encounter.")
		return
	if str(game.call("get_active_combat_encounter_id_for_testing")) != "training_construct":
		_fail("Combat runtime did not retain the active encounter ID.")
		return

	var killing_result := AttackResult.new()
	killing_result.hit = true
	killing_result.damage = 99
	killing_result.attack_name = "Тестовый удар"
	dummy.call("receive_player_attack", killing_result, false)
	await process_frame
	if str(state.call("get_encounter_status", "training_construct")) != EncounterSystem.STATUS_REWARDED:
		_fail("Destroying the training target did not resolve the encounter.")
		return
	if hero.experience != 25 or int(state.call("get_item_count", "straw_scrap")) != 1:
		_fail("Combat encounter reward and item were not applied once.")
		return
	game.call("_stop_turn_based_combat", "Тестовое завершение")
	await process_frame
	if not str(game.call("get_active_combat_encounter_id_for_testing")).is_empty():
		_fail("Combat encounter ID was not cleared after combat ended.")
		return

	dummy.call("reset_combat_state", true)
	var repeated_result := AttackResult.new()
	repeated_result.hit = true
	repeated_result.damage = 99
	dummy.call("receive_player_attack", repeated_result, false)
	await process_frame
	if hero.experience != 25 or int(state.call("get_item_count", "straw_scrap")) != 1:
		_fail("Resetting the actor allowed encounter rewards to be farmed.")
		return

	var dialogue: Control = game.get_node_or_null("Interface/DialogueUI") as Control
	var caretaker: Node = game.get_node_or_null("Caretaker")
	if dialogue == null or caretaker == null:
		_fail("Dialogue encounter integration nodes are missing.")
		return
	dialogue.call("start_dialogue", {
		"id": "encounter_smoke_dialogue",
		"speaker": "Смотритель",
		"text": "Проверка столкновения",
		"choices": []
	}, caretaker)
	dialogue.call("_on_choice_pressed", {
		"response": "Тайна раскрыта.",
		"encounter_id": "caretaker_revelation",
		"resolution_id": "persuaded"
	})
	await process_frame
	if str(state.call("get_encounter_status", "caretaker_revelation")) != EncounterSystem.STATUS_REWARDED:
		_fail("Dialogue choice did not resolve the unified encounter.")
		return
	if not bool(state.call("get_flag", "caretaker_convinced", false)) or hero.experience != 50:
		_fail("Dialogue encounter consequences were not applied.")
		return
	dialogue.call("_on_choice_pressed", {
		"response": "Альтернативная попытка.",
		"encounter_id": "caretaker_revelation",
		"resolution_id": "history"
	})
	await process_frame
	if hero.experience != 50 or bool(state.call("get_flag", "keeper_symbol_known", false)):
		_fail("A second dialogue solution changed a terminal encounter.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Unified combat and dialogue encounter runtime smoke test passed.")
	quit(0)
