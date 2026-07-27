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
		_fail("Character creator scene failed to load for spell selection.")
		return
	var creator: Node = packed_scene.instantiate()
	if creator == null:
		_fail("Character creator scene failed to instantiate for spell selection.")
		return
	root.add_child(creator)
	for _frame: int in range(4):
		await process_frame

	creator.set("_selected_background_id", "acolyte")
	creator.set("_selected_class_id", "wizard")
	creator.set("_selected_spell_sources", {})
	creator.call("_show_step", 6)
	for _frame: int in range(2):
		await process_frame

	var title_label: Label = creator.get("_title_label") as Label
	var class_panel: PanelContainer = creator.find_child("SpellSource_class", true, false) as PanelContainer
	var feat_panel: PanelContainer = creator.find_child("SpellSource_magic_initiate", true, false) as PanelContainer
	var class_cantrip_grid: GridContainer = creator.find_child("SpellGrid_class_cantrip_ids", true, false) as GridContainer
	var class_spell_grid: GridContainer = creator.find_child("SpellGrid_class_spell_ids", true, false) as GridContainer
	var class_prepared_grid: GridContainer = creator.find_child("SpellGrid_class_prepared_ids", true, false) as GridContainer
	var feat_cantrip_grid: GridContainer = creator.find_child("SpellGrid_magic_initiate_cantrip_ids", true, false) as GridContainer
	var ability_picker: OptionButton = creator.find_child("MagicInitiateAbilityPicker", true, false) as OptionButton
	if title_label == null or title_label.text != "Заклинания":
		_fail("Wizard spell selection step did not open.")
		return
	if class_panel == null or feat_panel == null or not class_panel.is_visible_in_tree() or not feat_panel.is_visible_in_tree():
		_fail("Wizard and Magic Initiate source panels were not both visible.")
		return
	if (
		class_cantrip_grid == null
		or class_spell_grid == null
		or class_prepared_grid == null
		or feat_cantrip_grid == null
		or class_cantrip_grid.columns != 2
		or class_spell_grid.columns != 2
		or class_prepared_grid.columns != 2
		or feat_cantrip_grid.columns != 2
	):
		_fail("Spell choices did not use the two-column mobile layout.")
		return
	if ability_picker == null or ability_picker.item_count != 3:
		_fail("Magic Initiate ability picker did not expose Intelligence, Wisdom and Charisma.")
		return

	var sources: Dictionary = creator.get("_selected_spell_sources") as Dictionary
	var class_source: Dictionary = sources.get(SpellSelectionSystem.SOURCE_CLASS, {}) as Dictionary
	var feat_source: Dictionary = sources.get(SpellSelectionSystem.SOURCE_MAGIC_INITIATE, {}) as Dictionary
	var class_cantrips: Array = class_source.get(SpellSelectionSystem.CANTRIP_IDS_KEY, []) as Array
	var class_spells: Array = class_source.get(SpellSelectionSystem.SPELL_IDS_KEY, []) as Array
	var class_prepared: Array = class_source.get(SpellSelectionSystem.PREPARED_IDS_KEY, []) as Array
	var feat_cantrips: Array = feat_source.get(SpellSelectionSystem.CANTRIP_IDS_KEY, []) as Array
	var feat_spells: Array = feat_source.get(SpellSelectionSystem.SPELL_IDS_KEY, []) as Array
	if class_cantrips.size() != 3 or class_spells.size() != 6 or class_prepared.size() != 4:
		_fail("Wizard defaults did not expose the required 3 cantrips, 6 spellbook spells and 4 prepared spells.")
		return
	if feat_cantrips.size() != 2 or feat_spells.size() != 1:
		_fail("Magic Initiate defaults did not expose two cantrips and one level-one spell.")
		return
	if not bool(creator.call("_can_continue_current_step")):
		_fail("Complete Wizard and Magic Initiate spell choices were rejected.")
		return

	var toggled_cantrip: String = str(class_cantrips[0])
	creator.call(
		"_toggle_spell_choice",
		SpellSelectionSystem.SOURCE_CLASS,
		SpellSelectionSystem.CANTRIP_IDS_KEY,
		toggled_cantrip
	)
	await process_frame
	if bool(creator.call("_can_continue_current_step")):
		_fail("Incomplete Wizard cantrip selection did not block progression.")
		return
	creator.call(
		"_toggle_spell_choice",
		SpellSelectionSystem.SOURCE_CLASS,
		SpellSelectionSystem.CANTRIP_IDS_KEY,
		toggled_cantrip
	)
	await process_frame
	if not bool(creator.call("_can_continue_current_step")):
		_fail("Restored Wizard cantrip selection did not re-enable progression.")
		return

	ability_picker = creator.find_child("MagicInitiateAbilityPicker", true, false) as OptionButton
	var charisma_index: int = -1
	for item_index: int in range(ability_picker.item_count):
		if str(ability_picker.get_item_metadata(item_index)) == "charisma":
			charisma_index = item_index
			break
	if charisma_index < 0:
		_fail("Magic Initiate ability picker did not include Charisma metadata.")
		return
	creator.call("_on_magic_initiate_ability_selected", charisma_index, ability_picker)
	await process_frame
	sources = creator.get("_selected_spell_sources") as Dictionary
	feat_source = sources.get(SpellSelectionSystem.SOURCE_MAGIC_INITIATE, {}) as Dictionary
	if str(feat_source.get("ability_id", "")) != "charisma":
		_fail("Magic Initiate source did not retain the independently selected Charisma ability.")
		return

	print("Wizard and Magic Initiate mobile spell-selection smoke test passed.")
	creator.queue_free()
	quit(0)
