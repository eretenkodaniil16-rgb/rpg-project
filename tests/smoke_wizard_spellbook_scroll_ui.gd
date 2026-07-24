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
	await create_timer(35.0).timeout
	if not _finished:
		_fail("Wizard spellbook scroll UI smoke test timed out.")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload was unavailable.")
		return
	state.call("new_game")
	var wizard := PlayerCharacter.new()
	wizard.character_name = "Архивариус"
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.level = 20
	wizard.maximum_health = 30
	wizard.current_health = 30
	wizard.abilities["intelligence"] = 30
	wizard.base_abilities["intelligence"] = 30
	wizard.skill_proficiencies.append("arcana")
	wizard.expertise_skills.append("arcana")
	wizard.spellbook_initialized = true
	wizard.known_features = ["fire_bolt", "ritual_adept"]
	state.set("player_character", wizard)
	state.call("add_item", "spellbook", 1, false)
	state.call("add_item", "gold_coin", 100, false)
	state.call("add_item", "spell_scroll_caustic_pulse", 1, false)

	var panel_scene: PackedScene = load("res://scenes/ui/inventory_panel.tscn") as PackedScene
	if panel_scene == null:
		_fail("Production InventoryPanel scene could not be loaded.")
		return
	var panel: Node = panel_scene.instantiate()
	root.add_child(panel)
	await process_frame
	panel.call("open_inventory")
	await process_frame
	var entry: Dictionary = state.call("get_item_definition", "spell_scroll_caustic_pulse") as Dictionary
	entry["quantity"] = 1
	panel.call("_show_details", entry)
	await process_frame
	var copy_button: Button = panel.get("_copy_scroll_button") as Button
	if copy_button == null or not copy_button.is_visible_in_tree():
		_fail("Spell scroll did not expose the transcription button in InventoryPanel.")
		return
	if copy_button.text != "ПЕРЕПИСАТЬ В КНИГУ":
		_fail("Spell scroll transcription button label was incorrect.")
		return
	var details: Label = panel.get("_details_label") as Label
	if details == null or details.text.find("50") < 0 or details.text.find("2 ч") < 0 or details.text.find("Сл 11") < 0:
		_fail("Scroll details did not show transcription cost, time, and Arcana DC.")
		return
	panel.call("_copy_selected_scroll")
	await process_frame
	if bool(state.call("has_item", "spell_scroll_caustic_pulse")):
		_fail("Inventory transcription did not consume the selected scroll.")
		return
	if "caustic_pulse" not in wizard.spellbook_spell_ids or "caustic_pulse" not in wizard.known_features:
		_fail("Inventory transcription did not add the formula to the Wizard spellbook.")
		return
	if details.text.find("переписана") < 0:
		_fail("Inventory panel did not display the successful transcription result.")
		return

	_finished = true
	panel.queue_free()
	print("Wizard spell scroll details, mobile transcription button, resource spending and spellbook update smoke test passed.")
	quit(0)
