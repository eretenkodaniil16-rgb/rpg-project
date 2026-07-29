class_name DialogueVisualController
extends Node

const PORTRAIT_SCRIPT: Script = preload("res://scripts/ui/dialogue_portrait.gd")

var _dialogue_ui: Control
var _portrait: DialoguePortrait
var _bottom_panel: PanelContainer
var _interact_button: Button
var _last_target_id: int = -1


func setup(dialogue_ui: Control) -> void:
	_dialogue_ui = dialogue_ui
	_build_layout()
	_configure_context_button()
	set_process(true)


func _process(_delta: float) -> void:
	if _dialogue_ui == null or not is_instance_valid(_dialogue_ui):
		return
	_update_portrait()
	_update_context_button_visibility()


func _update_portrait() -> void:
	var target_value: Variant = _dialogue_ui.get("_dialogue_target")
	var target: Node = target_value as Node if target_value is Node else null
	var target_id: int = target.get_instance_id() if target != null and is_instance_valid(target) else 0
	if target_id == _last_target_id:
		return
	_last_target_id = target_id
	if _portrait == null:
		return
	if target_id == 0:
		_portrait.clear_character()
	else:
		_portrait.set_character(target)


func _build_layout() -> void:
	if _dialogue_ui == null:
		return
	_bottom_panel = _dialogue_ui.get_node_or_null("BottomPanel") as PanelContainer
	var margin: MarginContainer = _dialogue_ui.get_node_or_null("BottomPanel/MarginContainer") as MarginContainer
	var column: VBoxContainer = _dialogue_ui.get_node_or_null("BottomPanel/MarginContainer/VBoxContainer") as VBoxContainer
	if _bottom_panel == null or margin == null or column == null:
		return

	_bottom_panel.offset_left = 24.0
	_bottom_panel.offset_top = -360.0
	_bottom_panel.offset_right = -24.0
	_bottom_panel.offset_bottom = -10.0
	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = Color(0.025, 0.045, 0.065, 0.96)
	panel_style.border_color = Color(0.72, 0.58, 0.31, 0.92)
	panel_style.set_border_width_all(2)
	panel_style.corner_radius_top_left = 8
	panel_style.corner_radius_top_right = 8
	panel_style.corner_radius_bottom_left = 8
	panel_style.corner_radius_bottom_right = 8
	panel_style.shadow_color = Color(0.0, 0.0, 0.0, 0.45)
	panel_style.shadow_size = 10
	_bottom_panel.add_theme_stylebox_override("panel", panel_style)
	margin.add_theme_constant_override("margin_left", 18)
	margin.add_theme_constant_override("margin_top", 16)
	margin.add_theme_constant_override("margin_right", 18)
	margin.add_theme_constant_override("margin_bottom", 16)

	var existing_row: Node = margin.get_node_or_null("DialogueContentRow")
	if existing_row is HBoxContainer:
		_portrait = existing_row.get_node_or_null("CharacterPortrait") as DialoguePortrait
		return

	var row := HBoxContainer.new()
	row.name = "DialogueContentRow"
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_theme_constant_override("separation", 18)
	margin.remove_child(column)
	margin.add_child(row)

	_portrait = PORTRAIT_SCRIPT.new() as DialoguePortrait
	_portrait.name = "CharacterPortrait"
	_portrait.custom_minimum_size = Vector2(180.0, 0.0)
	_portrait.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_child(_portrait)

	column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	column.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_child(column)
	var speaker: Label = column.get_node_or_null("SpeakerLabel") as Label
	var text: Label = column.get_node_or_null("TextLabel") as Label
	if speaker != null:
		speaker.add_theme_font_size_override("font_size", 23)
	if text != null:
		text.custom_minimum_size = Vector2(0.0, 70.0)
		text.add_theme_font_size_override("font_size", 18)


func _configure_context_button() -> void:
	if _dialogue_ui == null:
		return
	_interact_button = _dialogue_ui.get_node_or_null("../MobileControls/InteractButton") as Button
	if _interact_button != null:
		_interact_button.text = "ДЕЙСТВИЯ"


func _update_context_button_visibility() -> void:
	# The persistent lower-right button belongs to MobileControls and ActionCatalogUI.
	# Dialogue presentation must not rename, move or hide it.
	if _interact_button != null and is_instance_valid(_interact_button):
		_interact_button.text = "ДЕЙСТВИЯ"


func get_portrait_for_testing() -> DialoguePortrait:
	return _portrait


func get_bottom_panel_for_testing() -> PanelContainer:
	return _bottom_panel


func get_context_button_for_testing() -> Button:
	return _interact_button
