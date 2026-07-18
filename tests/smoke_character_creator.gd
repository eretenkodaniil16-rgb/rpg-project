extends SceneTree

const CHARACTER_CREATOR_SCENE: String = "res://scenes/character_creation/character_creator.tscn"


func _init() -> void:
	call_deferred("_run_smoke_test")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run_smoke_test() -> void:
	var packed_scene: PackedScene = load(CHARACTER_CREATOR_SCENE) as PackedScene
	if packed_scene == null:
		_fail("Character creator scene failed to load.")
		return
	var creator: Node = packed_scene.instantiate()
	if creator == null:
		_fail("Character creator scene failed to instantiate.")
		return
	root.add_child(creator)
	for _frame: int in range(4):
		await process_frame

	var title_label: Label = creator.get("_title_label") as Label
	var progress_label: Label = creator.get("_progress_label") as Label
	var content_container: VBoxContainer = creator.get("_content_container") as VBoxContainer
	var back_button: Button = creator.get("_back_button") as Button
	var next_button: Button = creator.get("_next_button") as Button
	var name_input: LineEdit = creator.get_node_or_null("CharacterNameInput") as LineEdit
	if name_input == null:
		name_input = creator.find_child("CharacterNameInput", true, false) as LineEdit

	if title_label == null or title_label.text != "Имя героя":
		_fail("Character creator title was not initialized.")
		return
	if progress_label == null or progress_label.text != "Шаг 1 из 6":
		_fail("Character creator progress was not initialized.")
		return
	if content_container == null or content_container.get_child_count() < 3:
		_fail("Character creator content is empty.")
		return
	if name_input == null or not name_input.is_visible_in_tree():
		_fail("Character name input is not visible.")
		return
	if back_button == null or next_button == null or not back_button.is_visible_in_tree() or not next_button.is_visible_in_tree():
		_fail("Character creator navigation is not visible.")
		return

	print("Character creator visible UI smoke test passed.")
	creator.queue_free()
	quit(0)
