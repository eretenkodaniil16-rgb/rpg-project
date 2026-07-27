class_name TurnCombatUI
extends Control

signal dash_requested
signal disengage_requested
signal dodge_requested
signal end_turn_requested

var initiative_label: Label
var resource_label: Label
var dash_button: Button
var disengage_button: Button
var dodge_button: Button
var end_turn_button: Button


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_interface()
	hide()


func refresh(turn_system: TurnBasedCombatSystem, player: Node, overlay_visible: bool, enemy_turn_running: bool) -> void:
	var should_show: bool = turn_system != null and turn_system.active and not overlay_visible
	visible = should_show
	if not should_show:
		return
	initiative_label.text = "Раунд %d · %s" % [
		turn_system.round_number,
		"  |  ".join(turn_system.get_order_labels())
	]
	var player_turn: bool = turn_system.is_player_turn(player) and not enemy_turn_running
	if player_turn:
		resource_label.text = "Действие: %s · Бонус: %s · Реакция: %s · Перемещение: %d футов" % [
			"готово" if turn_system.action_available else "использовано",
			"готово" if turn_system.bonus_action_available else "использовано",
			"готова" if turn_system.reaction_available else "использована",
			turn_system.movement_remaining_feet
		]
	else:
		var actor: Node = turn_system.current_actor()
		var actor_name: String = "Противник"
		if is_instance_valid(actor):
			actor_name = str(actor.call("get_combat_name")) if actor.has_method("get_combat_name") else actor.name
		resource_label.text = "Ход: %s" % actor_name
	dash_button.disabled = not player_turn or not turn_system.action_available
	disengage_button.disabled = not player_turn or not turn_system.action_available
	dodge_button.disabled = not player_turn or not turn_system.action_available
	end_turn_button.disabled = not player_turn


func _build_interface() -> void:
	initiative_label = Label.new()
	initiative_label.name = "InitiativeLabel"
	initiative_label.offset_left = 150.0
	initiative_label.offset_top = 132.0
	initiative_label.offset_right = 1130.0
	initiative_label.offset_bottom = 162.0
	initiative_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	initiative_label.add_theme_color_override("font_color", Color(0.9, 0.86, 0.62, 1.0))
	initiative_label.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.9))
	initiative_label.add_theme_constant_override("shadow_offset_x", 2)
	initiative_label.add_theme_constant_override("shadow_offset_y", 2)
	initiative_label.add_theme_font_size_override("font_size", 16)
	add_child(initiative_label)

	resource_label = Label.new()
	resource_label.name = "TurnResourceLabel"
	resource_label.offset_left = 150.0
	resource_label.offset_top = 163.0
	resource_label.offset_right = 1130.0
	resource_label.offset_bottom = 193.0
	resource_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	resource_label.add_theme_color_override("font_color", Color(0.68, 0.9, 1.0, 1.0))
	resource_label.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.9))
	resource_label.add_theme_constant_override("shadow_offset_x", 2)
	resource_label.add_theme_constant_override("shadow_offset_y", 2)
	resource_label.add_theme_font_size_override("font_size", 16)
	add_child(resource_label)

	dash_button = _create_button("DashButton", "РЫВОК", 250.0, 405.0)
	dash_button.pressed.connect(func() -> void: dash_requested.emit())
	add_child(dash_button)
	disengage_button = _create_button("DisengageButton", "ОТХОД", 415.0, 580.0)
	disengage_button.pressed.connect(func() -> void: disengage_requested.emit())
	add_child(disengage_button)
	dodge_button = _create_button("DodgeButton", "УКЛОНЕНИЕ", 590.0, 765.0)
	dodge_button.pressed.connect(func() -> void: dodge_requested.emit())
	add_child(dodge_button)
	end_turn_button = _create_button("EndTurnButton", "ЗАВЕРШИТЬ ХОД", 775.0, 1030.0)
	end_turn_button.pressed.connect(func() -> void: end_turn_requested.emit())
	add_child(end_turn_button)


func _create_button(node_name: String, text_value: String, left: float, right: float) -> Button:
	var button := Button.new()
	button.name = node_name
	button.text = text_value
	button.offset_left = left
	button.offset_top = 198.0
	button.offset_right = right
	button.offset_bottom = 248.0
	button.mouse_filter = Control.MOUSE_FILTER_STOP
	button.add_theme_font_size_override("font_size", 15)
	return button
