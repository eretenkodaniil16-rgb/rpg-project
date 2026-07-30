class_name ActionCatalogUI
extends Control

signal action_requested(action_id: String)
signal jump_requested

const CATEGORY_ORDER: Array[String] = ["action", "bonus", "reaction"]
const CATEGORY_LABELS: Dictionary = {
	"action": "ДЕЙСТВИЕ",
	"bonus": "ДОП. ДЕЙСТВИЕ",
	"reaction": "РЕАКЦИЯ"
}
const ACTION_GROUP_ORDER: Array[String] = ["target", "world", "attack", "movement", "spell", "tactic"]
const ACTION_GROUP_LABELS: Dictionary = {
	"target": "ЦЕЛЬ",
	"world": "МИР",
	"attack": "АТАКИ",
	"movement": "ПЕРЕМЕЩЕНИЕ",
	"spell": "ЗАКЛИНАНИЯ",
	"tactic": "ТАКТИКА"
}
const WORLD_INTERACTION_ACTION_ID: String = "world_interact"

var catalog_button: Button
var confirm_move_button: Button
var end_turn_button: Button
var jump_button: Button
var panel: PanelContainer
var header_label: Label
var resource_label: Label
var description_label: Label
var category_row: HBoxContainer
var action_group_row: HBoxContainer
var action_grid: GridContainer
var close_button: Button

var _entries: Dictionary = {}
var _selected_category: String = "action"
var _selected_action_group: String = "target"
var _last_signature: String = ""
var _combat_active: bool = false
var _player_turn: bool = false
var _group_buttons: Dictionary = {}
var _category_buttons: Dictionary = {}


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_interface()
	panel.hide()


func refresh(
	combat_active: bool,
	player_turn: bool,
	overlay_visible: bool,
	entries: Dictionary,
	resource_text: String,
	movement_plan_text: String,
	has_movement_plan: bool = false,
	planned_cost_feet: int = 0
) -> void:
	var mode_changed: bool = _combat_active != combat_active
	_combat_active = combat_active
	_player_turn = player_turn
	var show_catalog_controls: bool = not overlay_visible
	catalog_button.hide()
	end_turn_button.visible = combat_active and show_catalog_controls
	confirm_move_button.visible = combat_active and show_catalog_controls and player_turn and has_movement_plan
	jump_button.hide()
	if overlay_visible and panel.visible:
		panel.hide()
	_entries = entries.duplicate(true)
	_append_world_interaction_entry()
	resource_label.text = resource_text
	header_label.text = "БОЕВЫЕ ДЕЙСТВИЯ · %s" % movement_plan_text if combat_active else "ДЕЙСТВИЯ"
	catalog_button.disabled = true
	end_turn_button.disabled = not player_turn
	confirm_move_button.disabled = not player_turn or not has_movement_plan
	confirm_move_button.text = "ПЕРЕМЕСТИТЬСЯ · %d ФТ" % planned_cost_feet if has_movement_plan else "ПЕРЕМЕСТИТЬСЯ"
	category_row.visible = combat_active
	if mode_changed:
		_selected_category = "action"
		_selected_action_group = "attack" if combat_active else "target"
		_last_signature = ""
	_ensure_valid_selection()
	if panel.visible:
		var signature: String = JSON.stringify([
			_entries,
			_selected_category,
			_selected_action_group,
			combat_active,
			player_turn,
			resource_text,
			movement_plan_text
		])
		if signature != _last_signature:
			_last_signature = signature
			_rebuild_action_grid()


func is_catalog_open() -> bool:
	return panel.visible


func toggle_catalog() -> void:
	_toggle_catalog()


func close_catalog() -> void:
	panel.hide()
	_last_signature = ""


func get_entries_for_testing() -> Dictionary:
	return _entries.duplicate(true)


func _append_world_interaction_entry() -> void:
	if not _combat_active:
		return
	var player: Node = get_tree().get_first_node_in_group("player")
	if not is_instance_valid(player):
		return
	var interactable_value: Variant = player.get("interactable")
	var interactable: Node = interactable_value as Node if interactable_value is Node and is_instance_valid(interactable_value as Node) else null
	var label: String = "НЕТ ОБЪЕКТА РЯДОМ"
	var description: String = "Подойдите к двери или другому доступному объекту мира."
	var enabled: bool = false
	if interactable != null and interactable.has_method("perform_world_interaction"):
		label = str(interactable.call("get_combat_interaction_label")) if interactable.has_method("get_combat_interaction_label") else "ВЗАИМОДЕЙСТВОВАТЬ"
		description = str(interactable.call("get_combat_interaction_description")) if interactable.has_method("get_combat_interaction_description") else "Взаимодействовать с соседним объектом мира."
		enabled = _player_turn
		if interactable.has_method("can_perform_world_interaction"):
			enabled = enabled and bool(interactable.call("can_perform_world_interaction"))
	var action_value: Variant = _entries.get("action", [])
	var action_entries: Array = action_value as Array if action_value is Array else []
	action_entries.append({
		"id": WORLD_INTERACTION_ACTION_ID,
		"label": label,
		"enabled": enabled,
		"description": description,
		"group": "world"
	})
	_entries["action"] = action_entries


func _build_interface() -> void:
	# Compatibility node for older tests and saved scene references. The real mobile entry point is InteractButton.
	catalog_button = Button.new()
	catalog_button.name = "ActionCatalogButton"
	catalog_button.text = "ДЕЙСТВИЯ"
	catalog_button.hide()
	catalog_button.disabled = true
	catalog_button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	catalog_button.pressed.connect(toggle_catalog)
	add_child(catalog_button)

	end_turn_button = _make_bottom_rail_button("EndTurnFixedButton", "КОНЕЦ ХОДА", -214.0, -154.0, 16)
	end_turn_button.pressed.connect(func() -> void: action_requested.emit("end_turn"))
	add_child(end_turn_button)

	confirm_move_button = _make_bottom_rail_button("ConfirmMovementFloatingButton", "ПЕРЕМЕСТИТЬСЯ", -284.0, -224.0, 15)
	confirm_move_button.pressed.connect(func() -> void: action_requested.emit("confirm_move"))
	add_child(confirm_move_button)

	# Compatibility node. The active mobile jump button is created next to the joystick.
	jump_button = Button.new()
	jump_button.name = "ExplorationJumpButtonLegacy"
	jump_button.text = "ПРЫЖОК"
	jump_button.hide()
	jump_button.pressed.connect(func() -> void: jump_requested.emit())
	add_child(jump_button)

	panel = PanelContainer.new()
	panel.name = "ActionCatalogPanel"
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.offset_left = -430.0
	panel.offset_top = -235.0
	panel.offset_right = 430.0
	panel.offset_bottom = 235.0
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.z_index = 170
	panel.modulate = Color(1.0, 1.0, 1.0, 0.96)
	add_child(panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 20)
	margin.add_theme_constant_override("margin_top", 16)
	margin.add_theme_constant_override("margin_right", 20)
	margin.add_theme_constant_override("margin_bottom", 16)
	panel.add_child(margin)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 8)
	margin.add_child(column)

	var top_row := HBoxContainer.new()
	column.add_child(top_row)
	header_label = Label.new()
	header_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header_label.add_theme_font_size_override("font_size", 20)
	top_row.add_child(header_label)
	close_button = Button.new()
	close_button.text = "ЗАКРЫТЬ"
	close_button.custom_minimum_size = Vector2(130.0, 48.0)
	close_button.pressed.connect(close_catalog)
	top_row.add_child(close_button)

	resource_label = Label.new()
	resource_label.add_theme_color_override("font_color", Color(0.65, 0.9, 1.0, 1.0))
	resource_label.add_theme_font_size_override("font_size", 15)
	resource_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(resource_label)

	category_row = HBoxContainer.new()
	category_row.add_theme_constant_override("separation", 8)
	column.add_child(category_row)
	for category_id: String in CATEGORY_ORDER:
		var category_button := Button.new()
		category_button.name = "%sCategoryButton" % category_id.capitalize()
		category_button.text = str(CATEGORY_LABELS.get(category_id, category_id))
		category_button.custom_minimum_size = Vector2(0.0, 48.0)
		category_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		category_button.pressed.connect(_select_category.bind(category_id))
		category_row.add_child(category_button)
		_category_buttons[category_id] = category_button

	action_group_row = HBoxContainer.new()
	action_group_row.add_theme_constant_override("separation", 6)
	column.add_child(action_group_row)
	for group_id: String in ACTION_GROUP_ORDER:
		var group_button := Button.new()
		group_button.name = "%sActionGroupButton" % group_id.capitalize()
		group_button.text = str(ACTION_GROUP_LABELS.get(group_id, group_id))
		group_button.custom_minimum_size = Vector2(0.0, 44.0)
		group_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		group_button.pressed.connect(_select_action_group.bind(group_id))
		action_group_row.add_child(group_button)
		_group_buttons[group_id] = group_button

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0.0, 210.0)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(scroll)
	action_grid = GridContainer.new()
	action_grid.columns = 2
	action_grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	action_grid.add_theme_constant_override("h_separation", 10)
	action_grid.add_theme_constant_override("v_separation", 8)
	scroll.add_child(action_grid)

	description_label = Label.new()
	description_label.custom_minimum_size = Vector2(0.0, 46.0)
	description_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	description_label.add_theme_color_override("font_color", Color(0.86, 0.84, 0.72, 1.0))
	column.add_child(description_label)


func _make_bottom_rail_button(node_name: String, text_value: String, top: float, bottom: float, font_size: int) -> Button:
	var button := Button.new()
	button.name = node_name
	button.text = text_value
	button.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	button.offset_left = -198.0
	button.offset_top = top
	button.offset_right = -28.0
	button.offset_bottom = bottom
	button.add_theme_font_size_override("font_size", font_size)
	button.mouse_filter = Control.MOUSE_FILTER_STOP
	button.z_index = 120
	button.modulate = Color(1.0, 1.0, 1.0, 0.88)
	return button


func _toggle_catalog() -> void:
	panel.visible = not panel.visible
	if panel.visible:
		_last_signature = ""
		_ensure_valid_selection()
		_rebuild_action_grid()


func _select_category(category_id: String) -> void:
	_selected_category = category_id
	_last_signature = ""
	_ensure_valid_selection()
	_rebuild_action_grid()


func _select_action_group(group_id: String) -> void:
	_selected_action_group = group_id
	_last_signature = ""
	_rebuild_action_grid()


func _ensure_valid_selection() -> void:
	if not _combat_active:
		_selected_category = "action"
	var values: Variant = _entries.get(_selected_category, [])
	var category_entries: Array = values as Array if values is Array else []
	var available_groups: Array[String] = []
	for group_id: String in ACTION_GROUP_ORDER:
		for entry_value: Variant in category_entries:
			if entry_value is Dictionary and str((entry_value as Dictionary).get("group", "tactic")) == group_id:
				available_groups.append(group_id)
				break
	if _selected_category == "action" and _selected_action_group not in available_groups:
		_selected_action_group = available_groups[0] if not available_groups.is_empty() else "target"


func _rebuild_action_grid() -> void:
	for child: Node in action_grid.get_children():
		child.queue_free()
	_update_navigation_buttons()
	var values: Variant = _entries.get(_selected_category, [])
	var category_entries: Array = values as Array if values is Array else []
	var visible_entries: Array[Dictionary] = []
	for entry_value: Variant in category_entries:
		if not entry_value is Dictionary:
			continue
		var entry: Dictionary = entry_value as Dictionary
		if _selected_category == "action" and str(entry.get("group", "tactic")) != _selected_action_group:
			continue
		visible_entries.append(entry)
	if visible_entries.is_empty():
		var empty_label := Label.new()
		empty_label.text = "В этой категории сейчас нет возможностей."
		empty_label.custom_minimum_size = Vector2(760.0, 58.0)
		empty_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		action_grid.add_child(empty_label)
		description_label.text = ""
		return
	for entry: Dictionary in visible_entries:
		var available: bool = bool(entry.get("enabled", true))
		var description: String = str(entry.get("description", ""))
		var button := Button.new()
		button.name = "%sActionButton" % str(entry.get("id", "action")).capitalize()
		button.text = str(entry.get("label", "Действие"))
		button.custom_minimum_size = Vector2(390.0, 58.0)
		button.tooltip_text = description
		button.modulate = Color.WHITE if available else Color(0.62, 0.62, 0.62, 1.0)
		button.pressed.connect(_emit_action.bind(str(entry.get("id", "")), description, available))
		button.mouse_entered.connect(_show_description.bind(description))
		action_grid.add_child(button)
	description_label.text = "Выберите действие. Недоступные варианты объяснят ограничение."


func _update_navigation_buttons() -> void:
	for category_id: String in CATEGORY_ORDER:
		var category_button: Button = _category_buttons.get(category_id) as Button
		if category_button != null:
			var values: Variant = _entries.get(category_id, [])
			category_button.visible = _combat_active and values is Array and not (values as Array).is_empty()
	for group_id: String in ACTION_GROUP_ORDER:
		var group_button: Button = _group_buttons.get(group_id) as Button
		if group_button == null:
			continue
		var has_entries: bool = false
		var values: Variant = _entries.get("action", [])
		if values is Array:
			for entry_value: Variant in values as Array:
				if entry_value is Dictionary and str((entry_value as Dictionary).get("group", "tactic")) == group_id:
					has_entries = true
					break
		group_button.visible = _selected_category == "action" and has_entries
	action_group_row.visible = _selected_category == "action"


func _emit_action(action_id: String, description: String, available: bool) -> void:
	if not available:
		description_label.text = "Сейчас недоступно: %s" % description
		return
	close_catalog()
	if action_id == WORLD_INTERACTION_ACTION_ID:
		var player: Node = get_tree().get_first_node_in_group("player")
		if is_instance_valid(player) and player.has_method("request_interaction"):
			player.call("request_interaction")
		return
	action_requested.emit(action_id)


func _show_description(text_value: String) -> void:
	description_label.text = text_value
