class_name SrdCombatUI
extends Control

signal prone_toggle_requested
signal grapple_requested
signal shove_prone_requested
signal shove_push_requested
signal escape_grapple_requested
signal ready_attack_requested
signal hide_requested

var status_label: Label
var prone_button: Button
var grapple_button: Button
var shove_prone_button: Button
var shove_push_button: Button
var escape_button: Button
var ready_button: Button
var hide_button: Button


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_interface()
	hide()


func refresh(
	combat_active: bool,
	player_turn: bool,
	overlay_visible: bool,
	action_available: bool,
	movement_remaining: int,
	player_state: CombatantState,
	selected_target_state: CombatantState,
	cover_text: String
) -> void:
	visible = combat_active and not overlay_visible
	if not visible:
		return
	var condition_text: String = SrdCombatRules.new().format_conditions(player_state)
	status_label.text = "Состояния: %s · Укрытие цели: %s" % [condition_text, cover_text]
	var can_use_action: bool = player_turn and action_available and SrdCombatRules.new().can_take_action(player_state)
	prone_button.disabled = not player_turn or (player_state != null and player_state.has_condition("grappled"))
	prone_button.text = "ВСТАТЬ" if player_state != null and player_state.has_condition("prone") else "ЛЕЧЬ"
	if player_state != null and player_state.has_condition("prone"):
		prone_button.disabled = prone_button.disabled or movement_remaining < 15
	grapple_button.disabled = not can_use_action or selected_target_state == null
	shove_prone_button.disabled = not can_use_action or selected_target_state == null
	shove_push_button.disabled = not can_use_action or selected_target_state == null
	escape_button.disabled = not can_use_action or player_state == null or not player_state.has_condition("grappled")
	ready_button.disabled = not can_use_action
	hide_button.disabled = not can_use_action


func _build_interface() -> void:
	status_label = Label.new()
	status_label.name = "SrdStatusLabel"
	status_label.offset_left = 120.0
	status_label.offset_top = 252.0
	status_label.offset_right = 1160.0
	status_label.offset_bottom = 282.0
	status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	status_label.add_theme_color_override("font_color", Color(0.82, 0.9, 0.74, 1.0))
	status_label.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.9))
	status_label.add_theme_constant_override("shadow_offset_x", 2)
	status_label.add_theme_constant_override("shadow_offset_y", 2)
	status_label.add_theme_font_size_override("font_size", 14)
	add_child(status_label)

	prone_button = _create_button("ProneButton", "ЛЕЧЬ", 112.0, 252.0, 286.0)
	prone_button.pressed.connect(func() -> void: prone_toggle_requested.emit())
	add_child(prone_button)
	grapple_button = _create_button("GrappleButton", "ЗАХВАТ", 262.0, 402.0, 286.0)
	grapple_button.pressed.connect(func() -> void: grapple_requested.emit())
	add_child(grapple_button)
	shove_prone_button = _create_button("ShoveProneButton", "СБИТЬ", 412.0, 552.0, 286.0)
	shove_prone_button.pressed.connect(func() -> void: shove_prone_requested.emit())
	add_child(shove_prone_button)
	shove_push_button = _create_button("ShovePushButton", "ТОЛКНУТЬ", 562.0, 712.0, 286.0)
	shove_push_button.pressed.connect(func() -> void: shove_push_requested.emit())
	add_child(shove_push_button)
	escape_button = _create_button("EscapeGrappleButton", "ВЫРВАТЬСЯ", 722.0, 872.0, 286.0)
	escape_button.pressed.connect(func() -> void: escape_grapple_requested.emit())
	add_child(escape_button)
	ready_button = _create_button("ReadyAttackButton", "ГОТОВИТЬ", 882.0, 1022.0, 286.0)
	ready_button.pressed.connect(func() -> void: ready_attack_requested.emit())
	add_child(ready_button)
	hide_button = _create_button("HideButton", "СКРЫТЬСЯ", 1032.0, 1172.0, 286.0)
	hide_button.pressed.connect(func() -> void: hide_requested.emit())
	add_child(hide_button)


func _create_button(node_name: String, text_value: String, left: float, right: float, top: float) -> Button:
	var button := Button.new()
	button.name = node_name
	button.text = text_value
	button.offset_left = left
	button.offset_top = top
	button.offset_right = right
	button.offset_bottom = top + 48.0
	button.mouse_filter = Control.MOUSE_FILTER_STOP
	button.add_theme_font_size_override("font_size", 13)
	return button
