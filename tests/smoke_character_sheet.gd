extends SceneTree

const SHEET_SCENE: String = "res://scenes/ui/character_sheet.tscn"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node("GameState")
	var character := PlayerCharacter.create_legacy_default()
	character.character_name = "Тестовый герой"
	character.character_class_name = "Следопыт"
	character.abilities["dexterity"] = 16
	var sheet := (load(SHEET_SCENE) as PackedScene).instantiate() as CharacterSheet
	root.add_child(sheet)
	await process_frame
	sheet.open_sheet(character)
	await process_frame
	assert(sheet.visible)
	var identity := sheet.find_child("IdentityLabel", true, false) as Label
	var grid := sheet.find_child("AbilitiesGrid", true, false) as GridContainer
	assert(identity.text.contains("Тестовый герой"))
	assert(identity.text.contains("Следопыт"))
	assert(grid.get_child_count() == 18)
	sheet.close_sheet()
	assert(not sheet.visible)
	assert(not bool(state.get("input_locked")))
	print("Character sheet smoke test passed.")
	quit(0)
