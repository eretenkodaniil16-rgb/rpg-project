extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	GameState.new_game()
	var wizard := PlayerCharacter.new()
	wizard.character_name = "Ритуалист"
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.race_name = "Человек"
	wizard.abilities["intelligence"] = 16
	wizard.base_abilities["intelligence"] = 16
	SpellcastingSystem.new().ensure_character(wizard, false)
	GameState.player_character = wizard

	var hub := CharacterHubInventory.new()
	root.add_child(hub)
	for _frame: int in range(3):
		await process_frame
	hub.open_tab(wizard, 2)
	await process_frame

	var ritual_button: Button = hub.get("_ritual") as Button
	var spell_prepare_button: Button = hub.get("_spell_prepare") as Button
	var quick_button: Button = hub.get("_prepare") as Button
	if ritual_button == null or spell_prepare_button == null or quick_button == null:
		_fail("Spell preparation, ritual or quick-action button was not built.")
		return

	var detect_magic: Dictionary = ClassDataSystem.new().get_ability_definition("detect_magic")
	hub.call("_select_power", detect_magic)
	await process_frame
	if not ritual_button.is_visible_in_tree() or ritual_button.disabled:
		_fail("Prepared ritual was not available outside combat.")
		return
	if quick_button.text.find("БЫСТР") < 0:
		_fail("Quick action was not kept separate from spell preparation.")
		return

	var magic_missile: Dictionary = ClassDataSystem.new().get_ability_definition("magic_missile")
	hub.call("_select_power", magic_missile)
	await process_frame
	if not spell_prepare_button.is_visible_in_tree():
		_fail("Level-one spell preparation control was not visible.")
		return

	var labels: Array[Node] = hub.find_children("*", "Label", true, false)
	if not _contains_label(labels, "Время мира:") or not _contains_label(labels, "Магия: атака"):
		_fail("Active character sheet did not show world time and spellcasting values.")
		return

	var spellcasting := SpellcastingSystem.new()
	spellcasting.begin_concentration(wizard, "detect_magic")
	hub.call("_refresh_all")
	await process_frame
	labels = hub.find_children("*", "Label", true, false)
	if not _contains_label(labels, "Концентрация: Обнаружение магии"):
		_fail("Active concentration was not shown in the character sheet.")
		return

	hub.close_sheet()
	hub.queue_free()
	print("Spell preparation and ritual UI smoke test passed.")
	quit(0)


func _contains_label(labels: Array[Node], fragment: String) -> bool:
	for node: Node in labels:
		var label: Label = node as Label
		if label != null and label.text.find(fragment) >= 0:
			return true
	return false
