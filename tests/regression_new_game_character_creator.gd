extends SceneTree

const MAIN_MENU_SCENE: String = "res://scenes/menus/main_menu.tscn"
const CHARACTER_CREATOR_SCENE: String = "res://scenes/character_creation/character_creator.tscn"


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	if not _assert_character_creator_has_no_empty_first_frame():
		return

	var menu_scene: PackedScene = load(MAIN_MENU_SCENE) as PackedScene
	if menu_scene == null:
		_fail("Main menu scene failed to load.")
		return
	var menu: Node = menu_scene.instantiate()
	root.add_child(menu)
	current_scene = menu
	await process_frame

	var new_game_button: Button = menu.find_child("NewGameButton", true, false) as Button
	if new_game_button == null:
		_fail("New Game button is missing from the main menu.")
		return
	new_game_button.pressed.emit()

	for _frame: int in range(10):
		await process_frame
		if current_scene != null and current_scene.name == "CharacterCreator":
			break
	if current_scene == null or current_scene.name != "CharacterCreator":
		_fail("New Game did not switch to CharacterCreator.")
		return

	var creator: Node = current_scene
	var title: Label = creator.get("_title_label") as Label
	var name_input: LineEdit = creator.find_child("CharacterNameInput", true, false) as LineEdit
	var content: VBoxContainer = creator.get("_content_container") as VBoxContainer
	var back_button: Button = creator.get("_back_button") as Button
	var next_button: Button = creator.get("_next_button") as Button
	if title == null or title.text != "Имя героя" or not title.is_visible_in_tree():
		_fail("Character creator has no visible title.")
		return
	if name_input == null or not name_input.is_visible_in_tree():
		_fail("Character creator has no visible name input.")
		return
	if content == null or not content.is_visible_in_tree() or content.get_child_count() == 0:
		_fail("Character creator has no visible content.")
		return
	if back_button == null or next_button == null or not back_button.is_visible_in_tree() or not next_button.is_visible_in_tree():
		_fail("Character creator navigation buttons are missing or hidden.")
		return

	print("Main menu to visible CharacterCreator regression test passed.")
	quit(0)


func _assert_character_creator_has_no_empty_first_frame() -> bool:
	var packed_scene: PackedScene = load(CHARACTER_CREATOR_SCENE) as PackedScene
	if packed_scene == null:
		_fail("Character creator scene failed to load for the first-frame check.")
		return false
	var creator: Node = packed_scene.instantiate()
	if creator == null:
		_fail("Character creator scene failed to instantiate for the first-frame check.")
		return false

	# root is already inside the SceneTree. Node._ready() therefore runs during
	# add_child(), and these assertions deliberately happen before any await.
	root.add_child(creator)
	var title: Label = creator.get("_title_label") as Label
	var name_input: LineEdit = creator.find_child("CharacterNameInput", true, false) as LineEdit
	var content: VBoxContainer = creator.get("_content_container") as VBoxContainer
	var back_button: Button = creator.get("_back_button") as Button
	var next_button: Button = creator.get("_next_button") as Button
	if title == null or title.text != "Имя героя":
		_fail("Character creator title was not initialized during add_child().")
		return false
	if name_input == null:
		_fail("Character name input was not created during add_child().")
		return false
	if content == null or content.get_child_count() == 0:
		_fail("Character creator content was empty immediately after add_child().")
		return false
	if back_button == null or next_button == null:
		_fail("Character creator navigation was not created during add_child().")
		return false

	root.remove_child(creator)
	creator.free()
	return true
