extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	state.set("player_character", _make_hero())
	state.set("inventory", {})

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate() if packed != null else null
	if game == null:
		_fail("Game scene could not be loaded.")
		return
	root.add_child(game)
	for _frame: int in range(18):
		await process_frame

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var guard: Node = game.call("get_patrol_actor_for_testing", "service_guard") as Node
	var panel: LootContainerPanel = game.call("get_loot_container_panel_for_testing") as LootContainerPanel
	if player == null or guard == null or panel == null or not guard is Node2D:
		_fail("Guard, player or loot panel fixture is missing.")
		return
	(guard as Node2D).global_position = player.global_position + Vector2(32.0, 0.0)
	guard.call("_activate_body_from_defeat", CorpseInteractionSystem.BODY_DEAD)
	if not bool(guard.call("is_dead_body")):
		_fail("Service guard did not enter the persistent dead-body state.")
		return
	game.call("select_context_target_for_testing", guard)
	var entries: Dictionary = game.call("get_action_catalog_entries_for_testing") as Dictionary
	var open_found: bool = false
	for value: Variant in entries.get("action", []) as Array:
		if not value is Dictionary:
			continue
		var entry: Dictionary = value as Dictionary
		var action_id: String = str(entry.get("id", ""))
		if action_id.begins_with("corpse_loot_item__") or action_id == "corpse_loot_all":
			_fail("Legacy per-item corpse action remained beside the common loot panel action.")
			return
		if action_id == "open_selected_body_loot":
			open_found = str(entry.get("label", "")) == "ОБЫСКАТЬ: СЛУЖЕБНЫЙ ДОЗОРНЫЙ"
	if not open_found:
		_fail("Dead guard has no explicit Russian common-panel action.")
		return

	game.call("_on_feedback_catalog_action_requested", "open_selected_body_loot")
	if not panel.is_open():
		_fail("Opening corpse loot did not show the common mobile panel.")
		return
	var labels: Array[String] = panel.get_item_action_labels_for_testing()
	for expected: String in [
		"ПОДОБРАТЬ: КОЖАНЫЙ ДОСПЕХ",
		"ПОДОБРАТЬ: КОРОТКИЙ МЕЧ",
		"ПОДОБРАТЬ: ЗОЛОТАЯ МОНЕТА ×4"
	]:
		if expected not in labels:
			_fail("Corpse panel is missing Russian action: %s; actual: %s" % [expected, labels])
			return
	game.call("take_active_loot_item_for_testing", "gold_coin")
	if int(state.call("get_item_count", "gold_coin")) != 4:
		_fail("Corpse panel did not transfer the guard's four coins.")
		return
	var remaining: Array[Dictionary] = guard.call("get_remaining_corpse_loot") as Array[Dictionary]
	for entry: Dictionary in remaining:
		if str(entry.get("item_id", "")) == "gold_coin":
			_fail("Transferred coins remained on the corpse.")
			return
	panel.close_panel()

	game.queue_free()
	await process_frame
	print("Corpse loot uses the common Russian mobile pickup panel.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель обыска"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.maximum_health = 12
	hero.current_health = 12
	hero.starter_loadout_granted = true
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
