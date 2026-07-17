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
	character.character_name = "Испытатель"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.maximum_health = 13
	character.current_health = 7
	state.set("player_character", character)

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Game scene failed to load.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	await process_frame
	await process_frame

	var panel: Node = game.find_child("AbilityPanel", true, false)
	var dummy: Node = game.find_child("TrainingDummy", true, false)
	if panel == null or dummy == null:
		_fail("Ability panel or training dummy is missing.")
		return
	if not character.starter_loadout_granted:
		_fail("Starter loadout was not granted.")
		return
	if character.equipped_weapon_id != "greatsword" or character.equipped_armor_id != "chain_mail":
		_fail("Fighter starter equipment was not applied.")
		return
	if int(state.call("get_item_count", "greatsword")) != 1:
		_fail("Starter weapon is absent from inventory.")
		return
	if character.signature_ability_id != "second_wind":
		_fail("Fighter signature ability is incorrect.")
		return

	panel.call("_on_ability_pressed")
	await process_frame
	if character.current_health <= 7:
		_fail("Second Wind did not heal the character.")
		return
	if character.get_resource("second_wind") != 1:
		_fail("Second Wind resource was not consumed.")
		return

	print("Ability panel smoke test passed.")
	quit(0)
