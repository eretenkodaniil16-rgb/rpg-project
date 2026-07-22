extends SceneTree

var _finished: bool = false


func _init() -> void:
	call_deferred("_run")
	call_deferred("_watchdog")


func _fail(message: String) -> void:
	_finished = true
	push_error(message)
	quit(1)


func _watchdog() -> void:
	await create_timer(30.0).timeout
	if not _finished:
		_fail("Spellcasting UI smoke test timed out after 30 seconds.")


func _run() -> void:
	print("spell-ui checkpoint 1: resolve autoload")
	var game_state: Node = root.get_node_or_null("GameState")
	if game_state == null:
		_fail("GameState autoload was not available to the spellcasting UI smoke test.")
		return
	game_state.call("new_game")
	var wizard := PlayerCharacter.new()
	wizard.character_name = "Ритуалист"
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.race_name = "Человек"
	wizard.abilities["intelligence"] = 16
	wizard.base_abilities["intelligence"] = 16
	SpellcastingSystem.new().ensure_character(wizard, false)
	game_state.set("player_character", wizard)

	print("spell-ui checkpoint 2: instantiate hub")
	var hub := CharacterHubInventory.new()
	root.add_child(hub)
	for _frame: int in range(3):
		await process_frame
	print("spell-ui checkpoint 3: open powers tab")
	hub.open_tab(wizard, 2)
	await process_frame

	var ritual_button: Button = hub.get("_ritual") as Button
	var spell_prepare_button: Button = hub.get("_spell_prepare") as Button
	var quick_button: Button = hub.get("_prepare") as Button
	if ritual_button == null or spell_prepare_button == null or quick_button == null:
		_fail("Spell preparation, ritual or quick-action button was not built.")
		return

	print("spell-ui checkpoint 4: select ritual")
	var detect_magic: Dictionary = ClassDataSystem.new().get_ability_definition("detect_magic")
	hub.call("_select_power", detect_magic)
	await process_frame
	if not ritual_button.is_visible_in_tree() or ritual_button.disabled:
		_fail("Prepared ritual was not available outside combat.")
		return
	if quick_button.text.find("БЫСТР") < 0:
		_fail("Quick action was not kept separate from spell preparation.")
		return

	print("spell-ui checkpoint 5: select prepared spell")
	var magic_missile: Dictionary = ClassDataSystem.new().get_ability_definition("magic_missile")
	hub.call("_select_power", magic_missile)
	await process_frame
	if not spell_prepare_button.is_visible_in_tree():
		_fail("Level-one spell preparation control was not visible.")
		return

	print("spell-ui checkpoint 6: inspect character summary")
	var labels: Array[Node] = hub.find_children("*", "Label", true, false)
	if not _contains_label(labels, "Время мира:") or not _contains_label(labels, "Магия: атака"):
		_fail("Active character sheet did not show world time and spellcasting values.")
		return

	print("spell-ui checkpoint 7: concentration refresh")
	var spellcasting := SpellcastingSystem.new()
	spellcasting.begin_concentration(wizard, "detect_magic")
	hub.call("_refresh_all")
	await process_frame
	labels = hub.find_children("*", "Label", true, false)
	if not _contains_label(labels, "Концентрация: Обнаружение магии"):
		_fail("Active concentration was not shown in the character sheet.")
		return

	_finished = true
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
