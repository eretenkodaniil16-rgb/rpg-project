class_name ActionCatalogUI
extends Control

signal action_requested(action_id: String)
signal jump_requested

const CATEGORY_ORDER: Array[String] = ["movement", "action", "bonus", "reaction"]
const CATEGORY_LABELS: Dictionary = {
	"movement": "ПЕРЕМЕЩЕНИЕ",
	"action": "ДЕЙСТВИЕ",
	"bonus": "ДОП. ДЕЙСТВИЕ",
	"reaction": "РЕАКЦИЯ"
}

var catalog_button: Button
var jump_button: Button
var panel: PanelContainer
var header_label: Label
var resource_label: Label
var description_label: Label
var category_row: HBoxContainer
var action_grid: GridContainer
var close_button: Button

var _entries: Dictionary = {}
var _selected_category: String = "movement"
var _last_signature: String = ""


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
	movement_plan_text: String
) -> void:
	catalog_button.visible = combat_active and not overlay_visible
	jump_button.visible = not combat_active and not overlay_visible
	if not combat_active:
		panel.hide()
	if not catalog_button.visible and panel.visible:
		panel.hide()
	_entries = entries.duplicate(true)
	resource_label.text = resource_text
	header_label.text = "БОЕВЫЕ ДЕЙСТВИЯ · %s" % movement_plan_text
	catalog_button.disabled = not player_turn
	if panel.visible:
		var signature: String = JSON.stringify([_entries, _selected_category, player_turn, resource_text, movement_plan_text])
		if signature != _last_signature:
			_last_signature = signature
			_rebuild_action_grid()


func is_catalog_open() -> bool:
	return panel.visible


func close_catalog() -> void:
	panel.hide()


func _build_interface() -> void:
	catalog_button = Button.new()
	catalog_button.name = "ActionCatalogButton"
	catalog_button.text = "ДЕЙСТВИЯ"
	catalog_button.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	catalog_button.offset_left = -260.0
	catalog_button.offset_top = -145.0
	catalog_button.offset_right = -28.0
	catalog_button.offset_bottom = -82.0
	catalog_button.add_theme_font_size_override("font_size", 20)
	catalog_button.mouse_filter = Control.MOUSE_FILTER_STOP
	catalog_button.pressed.connect(_toggle_catalog)
	add_child(catalog_button)

	jump_button = Button.new()
	jump_button.name = "ExplorationJumpButton"
	jump_button.text = "ПРЫЖОК"
	jump_button.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	jump_button.offset_left = -260.0
	jump_button.offset_top = -145.0
	jump_button.offset_right = -28.0
	jump_button.offset_bottom = -82.0
	jump_button.add_theme_font_size_override("font_size", 20)
	jump_button.mouse_filter = Control.MOUSE_FILTER_STOP
	jump_button.pressed.connect(func() -> void: jump_requested.emit())
	add_child(jump_button)

	panel = PanelContainer.new()
	panel.name = "ActionCatalogPanel"
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.offset_left = -500.0
	panel.offset_top = -245.0
	panel.offset_right = 500.0
	panel.offset_bottom = 245.0
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 24)
	margin.add_theme_constant_override("margin_top", 20)
	margin.add_theme_constant_override("margin_right", 24)
	margin.add_theme_constant_override("margin_bottom", 20)
	panel.add_child(margin)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	margin.add_child(column)

	var top_row := HBoxContainer.new()
	column.add_child(top_row)
	header_label = Label.new()
	header_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header_label.add_theme_font_size_override("font_size", 22)
	top_row.add_child(header_label)
	close_button = Button.new()
	close_button.text = "ЗАКРЫТЬ"
	close_button.pressed.connect(close_catalog)
	top_row.add_child(close_button)

	resource_label = Label.new()
	resource_label.add_theme_color_override("font_color", Color(0.65, 0.9, 1.0, 1.0))
	resource_label.add_theme_font_size_override("font_size", 16)
	resource_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(resource_label)

	category_row = HBoxContainer.new()
	category_row.add_theme_constant_override("separation", 8)
	column.add_child(category_row)
	for category_id: String in CATEGORY_ORDER:
		var category_button := Button.new()
		category_button.name = "%sCategoryButton" % category_id.capitalize()
		category_button.text = str(CATEGORY_LABELS.get(category_id, category_id))
		category_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		category_button.pressed.connect(_select_category.bind(category_id))
		category_row.add_child(category_button)

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0.0, 285.0)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(scroll)
	action_grid = GridContainer.new()
	action_grid.columns = 3
	action_grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	action_grid.add_theme_constant_override("h_separation", 10)
	action_grid.add_theme_constant_override("v_separation", 10)
	scroll.add_child(action_grid)

	description_label = Label.new()
	description_label.custom_minimum_size = Vector2(0.0, 52.0)
	description_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	description_label.add_theme_color_override("font_color", Color(0.86, 0.84, 0.72, 1.0))
	column.add_child(description_label)


func _toggle_catalog() -> void:
	panel.visible = not panel.visible
	if panel.visible:
		_last_signature = ""
		_rebuild_action_grid()


func _select_category(category_id: String) -> void:
	_selected_category = category_id
	_last_signature = ""
	_rebuild_action_grid()


func _rebuild_action_grid() -> void:
	for child: Node in action_grid.get_children():
		child.queue_free()
	var values: Variant = _entries.get(_selected_category, [])
	var category_entries: Array = values as Array if values is Array else []
	if category_entries.is_empty():
		var empty_label := Label.new()
		empty_label.text = "В этой категории сейчас нет доступных возможностей."
		empty_label.custom_minimum_size = Vector2(860.0, 60.0)
		empty_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		action_grid.add_child(empty_label)
		description_label.text = ""
		return
	for entry_value: Variant in category_entries:
		if not entry_value is Dictionary:
			continue
		var entry := entry_value as Dictionary
		var button := Button.new()
		button.name = "%sActionButton" % str(entry.get("id", "action")).capitalize()
		button.text = str(entry.get("label", "Действие"))
		button.custom_minimum_size = Vector2(285.0, 64.0)
		button.disabled = not bool(entry.get("enabled", true))
		button.tooltip_text = str(entry.get("description", ""))
		button.pressed.connect(_emit_action.bind(str(entry.get("id", "")), str(entry.get("description", ""))))
		button.mouse_entered.connect(_show_description.bind(str(entry.get("description", ""))))
		action_grid.add_child(button)
	description_label.text = "Выберите действие. Ресурс указан названием категории."


func _emit_action(action_id: String, description: String) -> void:
	description_label.text = description
	action_requested.emit(action_id)


func _show_description(text_value: String) -> void:
	description_label.text = text_value
