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
	var name_input: LineEdit = creator.find_child("CharacterNameInput", true, false) as LineEdit
	if title_label == null or title_label.text != "Имя героя":
		_fail("Character creator title was not initialized.")
		return
	if progress_label == null or progress_label.text != "Шаг 1 из 7":
		_fail("Character creator did not expose the seven-step SRD flow.")
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

	creator.call("_show_step", 1)
	await process_frame
	var races: Array = creator.get("_races") as Array
	if races.size() != 9 or content_container.get_child_count() < 2:
		_fail("Species selection did not load all nine species.")
		return

	var scores: Array = creator.get("_scores") as Array
	scores.clear()
	for score: int in [18, 16, 14, 12, 10, 8]:
		scores.append(score)
	var assignments: Dictionary = creator.get("_assignments") as Dictionary
	assignments.clear()
	assignments["strength"] = 0
	assignments["dexterity"] = 1
	assignments["constitution"] = 2
	assignments["intelligence"] = 3
	assignments["wisdom"] = 4
	assignments["charisma"] = 5

	creator.set("_selected_background_id", "soldier")
	creator.set("_background_ability_bonuses", {"strength": 1, "dexterity": 1, "constitution": 1})
	creator.set("_selected_languages", ["dwarvish", "orc"])
	creator.call("_show_step", 4)
	for _frame: int in range(2):
		await process_frame
	var backgrounds: Array = creator.get("_backgrounds") as Array
	if backgrounds.size() != 4:
		_fail("Origin step did not load the four SRD backgrounds.")
		return
	if not bool(creator.call("_is_origin_configuration_valid")):
		_fail("A valid Soldier origin configuration was rejected by the creator.")
		return
	if int(creator.call("_score_with_origin_bonus", "strength")) != 19:
		_fail("Origin ability increase was not included in the final Strength score.")
		return
	if int(creator.call("_score_with_origin_bonus", "wisdom")) != 10:
		_fail("Species or another source unexpectedly changed Wisdom.")
		return

	creator.set("_selected_class_id", "fighter")
	creator.call("_show_step", 5)
	for _frame: int in range(2):
		await process_frame
	var classes: Array = creator.get("_classes") as Array
	if classes.size() != 12 or content_container.get_child_count() < 2:
		_fail("Class selection did not load all twelve classes.")
		return
	if not bool(creator.call("_can_continue_current_step")):
		_fail("A selected class did not enable progression to confirmation.")
		return

	creator.call("_show_step", 6)
	for _frame: int in range(2):
		await process_frame
	if title_label.text != "Подтверждение" or not bool(creator.call("_can_continue_current_step")):
		_fail("Complete SRD character data did not reach confirmation.")
		return

	print("Character creator seven-step SRD origin smoke test passed.")
	creator.queue_free()
	quit(0)
