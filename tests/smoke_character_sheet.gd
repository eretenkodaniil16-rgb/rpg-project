extends SceneTree

const SHEET_SCENE: String = "res://scenes/ui/character_sheet.tscn"


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
	var packed: PackedScene = load(SHEET_SCENE) as PackedScene
	if packed == null:
		_fail("Character sheet scene failed to load.")
		return
	var sheet: Control = packed.instantiate() as Control
	root.add_child(sheet)
	await process_frame

	var character := PlayerCharacter.create_legacy_default()
	character.character_name = "Тестовый герой"
	character.character_class_name = "Следопыт"
	character.abilities["dexterity"] = 16
	sheet.call("open_sheet", character)
	await process_frame

	if not sheet.visible:
		_fail("Character sheet did not become visible.")
		return
	var identity := sheet.find_child("IdentityLabel", true, false) as Label
	var grid := sheet.find_child("AbilitiesGrid", true, false) as GridContainer
	if identity == null or not identity.text.contains("Тестовый герой") or not identity.text.contains("Следопыт"):
		_fail("Character identity was not rendered.")
		return
	if grid == null or grid.get_child_count() != 18:
		_fail("Expected 18 ability cells, got %d." % (grid.get_child_count() if grid != null else -1))
		return

	sheet.call("close_sheet")
	if sheet.visible or bool(state.get("input_locked")):
		_fail("Character sheet did not close cleanly.")
		return
	print("Character sheet smoke test passed.")
	quit(0)
