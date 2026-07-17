extends SceneTree

const GAME_SCENE := "res://scenes/game/game.tscn"

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var state := root.get_node_or_null("GameState")
	assert(state != null)
	state.call("new_game")
	var game := (load(GAME_SCENE) as PackedScene).instantiate()
	root.add_child(game)
	await process_frame
	await process_frame

	var journal := game.find_child("QuestJournal", true, false) as Control
	var inventory := game.find_child("InventoryPanel", true, false) as Control
	assert(game.find_child("QuestButton", true, false) is Button)
	assert(game.find_child("InventoryButton", true, false) is Button)
	assert(journal != null and inventory != null)

	journal.call("open_journal")
	await process_frame
	assert(journal.visible)
	journal.call("close_journal")
	state.call("add_item", "straw_scrap", 2, false)
	inventory.call("open_inventory")
	await process_frame
	assert(inventory.visible)
	inventory.call("close_inventory")
	assert(not bool(state.get("input_locked")))
	print("Quest and inventory UI smoke test passed.")
	quit(0)
