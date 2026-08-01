class_name GamePauseSaveMenu
extends Control

signal main_menu_requested
signal menu_closed

const SAVE_SLOTS_PANEL_SCRIPT: Script = preload("res://scripts/ui/save_slots_panel.gd")

var _menu_panel: PanelContainer
var _save_slots_panel: SaveSlotsPanel
var _save_button: Button
var _save_status_label: Label
var _was_input_locked: bool = false
var _save_allowed: bool = true
var _save_block_reason: String = ""


func _ready() -> void:
	add_to_group("game_overlay")
	_build_ui()
	hide()


func toggle_menu() -> void:
	if visible:
		close_menu()
	else:
		open_menu()


func configure_save_availability(allowed: bool, block_reason: String = "") -> void:
	_save_allowed = allowed
	_save_block_reason = block_reason
	_refresh_save_availability()


func open_menu() -> void:
	var state: Node = _game_state()
	if state == null:
		push_error("GameState autoload is unavailable to the pause menu.")
		return
	_was_input_locked = bool(state.get("input_locked"))
	state.set("input_locked", true)
	_menu_panel.show()
	_save_slots_panel.hide()
	_refresh_save_availability()
	show()


func close_menu() -> void:
	if not visible:
		return
	hide()
	var state: Node = _game_state()
	if state != null:
		state.set("input_locked", _was_input_locked)
	menu_closed.emit()


func is_menu_open() -> bool:
	return visible


func is_save_available_for_testing() -> bool:
	return _save_allowed and is_instance_valid(_save_button) and not _save_button.disabled


func get_save_status_for_testing() -> String:
	return _save_status_label.text if is_instance_valid(_save_status_label) else ""


func _build_ui() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP

	var dimmer := ColorRect.new()
	dimmer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dimmer.color = Color(0.0, 0.0, 0.0, 0.66)
	dimmer.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dimmer)

	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)

	_menu_panel = PanelContainer.new()
	_menu_panel.custom_minimum_size = Vector2(520.0, 440.0)
	center.add_child(_menu_panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 38)
	margin.add_theme_constant_override("margin_top", 34)
	margin.add_theme_constant_override("margin_right", 38)
	margin.add_theme_constant_override("margin_bottom", 34)
	_menu_panel.add_child(margin)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 14)
	margin.add_child(vbox)

	var title := Label.new()
	title.text = "МЕНЮ"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 32)
	vbox.add_child(title)
	vbox.add_child(HSeparator.new())

	var resume_button := Button.new()
	resume_button.custom_minimum_size = Vector2(0.0, 62.0)
	resume_button.text = "ПРОДОЛЖИТЬ"
	resume_button.add_theme_font_size_override("font_size", 20)
	resume_button.pressed.connect(close_menu)
	vbox.add_child(resume_button)

	_save_button = Button.new()
	_save_button.custom_minimum_size = Vector2(0.0, 62.0)
	_save_button.text = "СОХРАНИТЬ ИГРУ"
	_save_button.add_theme_font_size_override("font_size", 20)
	_save_button.pressed.connect(_open_save_slots)
	vbox.add_child(_save_button)

	_save_status_label = Label.new()
	_save_status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_save_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_save_status_label.add_theme_color_override("font_color", Color(0.86, 0.66, 0.52, 1.0))
	_save_status_label.add_theme_font_size_override("font_size", 15)
	_save_status_label.hide()
	vbox.add_child(_save_status_label)

	var main_menu_button := Button.new()
	main_menu_button.custom_minimum_size = Vector2(0.0, 62.0)
	main_menu_button.text = "В ГЛАВНОЕ МЕНЮ"
	main_menu_button.add_theme_font_size_override("font_size", 20)
	main_menu_button.pressed.connect(_request_main_menu)
	vbox.add_child(main_menu_button)

	_save_slots_panel = SAVE_SLOTS_PANEL_SCRIPT.new() as SaveSlotsPanel
	_save_slots_panel.name = "SaveSlotsPanel"
	_save_slots_panel.closed.connect(_on_save_panel_closed)
	add_child(_save_slots_panel)
	_refresh_save_availability()


func _refresh_save_availability() -> void:
	if not is_instance_valid(_save_button) or not is_instance_valid(_save_status_label):
		return
	_save_button.disabled = not _save_allowed
	_save_button.text = "СОХРАНИТЬ ИГРУ" if _save_allowed else "СОХРАНЕНИЕ НЕДОСТУПНО"
	_save_status_label.text = _save_block_reason
	_save_status_label.visible = not _save_allowed and not _save_block_reason.is_empty()


func _open_save_slots() -> void:
	if not _save_allowed:
		return
	_menu_panel.hide()
	_save_slots_panel.open_for_save()


func _on_save_panel_closed() -> void:
	if visible:
		_menu_panel.show()


func _request_main_menu() -> void:
	main_menu_requested.emit()


func _game_state() -> Node:
	return get_node_or_null("/root/GameState")
