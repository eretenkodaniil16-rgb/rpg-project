extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("new_game")
	var character := PlayerCharacter.new()
	character.character_name = "Проверка интерфейса"
	character.character_class_id = "wizard"
	character.character_class_name = "Волшебник"
	character.maximum_health = 7
	character.current_health = 7
	state.set("player_character", character)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	var game: Node = packed.instantiate()
	root.add_child(game)
	await process_frame
	await process_frame
	await process_frame

	var inventory: Control = game.find_child("InventoryPanel", true, false) as Control
	var mobile_controls: Control = game.get_node_or_null("Interface/MobileControls") as Control
	var character_button: Button = game.find_child("CharacterButton", true, false) as Button
	var target_button: Button = game.find_child("TargetButton", true, false) as Button
	var attack_button: Button = game.find_child("AttackButton", true, false) as Button
	var target_label: Label = game.find_child("TargetLabel", true, false) as Label
	var ability_panel: Control = game.find_child("AbilityPanel", true, false) as Control
	var caretaker: Node = game.get_node_or_null("Caretaker")
	if inventory == null or mobile_controls == null or character_button == null or target_button == null or attack_button == null or target_label == null or ability_panel == null or caretaker == null:
		_fail("Required HUD, target, or inventory nodes are missing.")
		return
	if target_label.visible:
		_fail("Target distance must be hidden before manual target selection.")
		return

	game.call("_set_selected_target", caretaker)
	await process_frame
	await process_frame
	if not target_label.visible:
		_fail("Target distance did not appear after manual target selection.")
		return

	mobile_controls.show()
	character_button.show()
	target_button.show()
	attack_button.show()
	ability_panel.show()
	game.call("_open_inventory")
	await process_frame

	for item: CanvasItem in [mobile_controls, character_button, target_button, attack_button, target_label, ability_panel]:
		if item.visible:
			_fail("Exploration HUD remained visible over the inventory: %s" % item.name)
			return

	inventory.call("close_inventory")
	await process_frame
	await process_frame
	for item: CanvasItem in [mobile_controls, character_button, target_button, attack_button, target_label, ability_panel]:
		if not item.visible:
			_fail("Exploration HUD was not restored after closing inventory: %s" % item.name)
			return

	print("Overlay HUD visibility smoke test passed.")
	quit(0)
