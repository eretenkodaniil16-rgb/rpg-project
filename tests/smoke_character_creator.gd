extends SceneTree

const CHARACTER_CREATOR_SCENE: String = "res://scenes/character_creation/character_creator.tscn"
const CAROUSEL_COPY_COUNT: int = 3


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

	creator.call("_show_step", 1)
	for _frame: int in range(3):
		await process_frame
	var race_showcase: Control = creator.find_child("RaceShowcase", true, false) as Control
	var race_carousel: ScrollContainer = creator.find_child("RaceCarousel", true, false) as ScrollContainer
	var race_previous: Button = creator.find_child("RacePreviousButton", true, false) as Button
	var race_next: Button = creator.find_child("RaceNextButton", true, false) as Button
	if race_showcase == null or race_carousel == null:
		_fail("Race showcase or carousel is missing.")
		return
	if race_previous == null or race_next == null or not race_previous.is_visible_in_tree() or not race_next.is_visible_in_tree():
		_fail("Race previous/next buttons are missing or hidden.")
		return
	if not race_showcase.is_visible_in_tree() or race_carousel.get_child_count() == 0:
		_fail("Race showcase is not visible or contains no cards.")
		return
	var race_strip: HBoxContainer = race_carousel.get_child(0) as HBoxContainer
	var races: Array = creator.get("_races") as Array
	if race_strip == null or race_strip.get_child_count() != races.size() * CAROUSEL_COPY_COUNT:
		_fail("Race carousel is not cyclic: expected %d cards, got %d." % [races.size() * CAROUSEL_COPY_COUNT, 0 if race_strip == null else race_strip.get_child_count()])
		return
	if races.size() > 1:
		var first_race_id: String = str((races[0] as Dictionary).get("id", ""))
		var last_race_id: String = str((races[races.size() - 1] as Dictionary).get("id", ""))
		creator.set("_selected_race_id", first_race_id)
		creator.call("_select_adjacent_race", -1)
		if str(creator.get("_selected_race_id")) != last_race_id:
			_fail("Race arrow did not wrap from first race to last race.")
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
	creator.set("_selected_race_id", "elf")
	var base_dexterity: int = int(creator.call("_score_for_ability", "dexterity"))
	var final_dexterity: int = int(creator.call("_final_score_for_ability", "dexterity"))
	if base_dexterity != 16:
		_fail("Assigned Dexterity score was not retained; got %d." % base_dexterity)
		return
	if final_dexterity != 18:
		_fail("Elf Dexterity racial bonus was not applied; got %d." % final_dexterity)
		return
	var final_wisdom: int = int(creator.call("_final_score_for_ability", "wisdom"))
	if final_wisdom != 11:
		_fail("Elf Wisdom racial bonus was not applied; got %d." % final_wisdom)
		return

	creator.call("_show_step", 4)
	for _frame: int in range(3):
		await process_frame
	var class_showcase: Control = creator.find_child("ClassShowcase", true, false) as Control
	var class_carousel: ScrollContainer = creator.find_child("ClassCarousel", true, false) as ScrollContainer
	var class_previous: Button = creator.find_child("ClassPreviousButton", true, false) as Button
	var class_next: Button = creator.find_child("ClassNextButton", true, false) as Button
	if class_showcase == null or class_carousel == null:
		_fail("Class showcase or carousel is missing.")
		return
	if class_previous == null or class_next == null or not class_previous.is_visible_in_tree() or not class_next.is_visible_in_tree():
		_fail("Class previous/next buttons are missing or hidden.")
		return
	if not class_showcase.is_visible_in_tree() or class_carousel.get_child_count() == 0:
		_fail("Class showcase is not visible or contains no cards.")
		return
	var class_strip: HBoxContainer = class_carousel.get_child(0) as HBoxContainer
	var classes: Array = creator.get("_classes") as Array
	if class_strip == null or class_strip.get_child_count() != classes.size() * CAROUSEL_COPY_COUNT:
		_fail("Class carousel is not cyclic: expected %d cards, got %d." % [classes.size() * CAROUSEL_COPY_COUNT, 0 if class_strip == null else class_strip.get_child_count()])
		return
	if classes.size() > 1:
		var first_class_id: String = str((classes[0] as Dictionary).get("id", ""))
		var last_class_id: String = str((classes[classes.size() - 1] as Dictionary).get("id", ""))
		creator.set("_selected_class_id", first_class_id)
		creator.call("_select_adjacent_class", -1)
		if str(creator.get("_selected_class_id")) != last_class_id:
			_fail("Class arrow did not wrap from first class to last class.")
			return

	print("Character creator cyclic showcase and racial bonuses smoke test passed.")
	creator.queue_free()
	quit(0)
