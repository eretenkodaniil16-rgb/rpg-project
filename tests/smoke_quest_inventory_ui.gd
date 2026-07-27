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
	var hub := game.find_child("CharacterHub", true, false) as CharacterHub
	assert(game.find_child("QuestButton", true, false) is Button)
	assert(game.find_child("CharacterButton", true, false) is Button)
	assert(game.find_child("InventoryButton", true, false) == null)
	assert(journal != null and hub != null)

	journal.call("open_journal")
	await process_frame
	assert(journal.visible)
	journal.call("close_journal")

	state.call("add_item", "straw_scrap", 2, false)
	game.call("_open_inventory")
	await process_frame
	var tabs := hub.find_child("CharacterTabs", true, false) as TabContainer
	assert(hub.visible)
	assert(tabs != null and tabs.current_tab == 1)
	assert(bool(state.get("input_locked")))
	hub.close_sheet()
	assert(not bool(state.get("input_locked")))
	print("Quest journal and character-hub inventory smoke test passed.")
	quit(0)
