class_name D20RollOverlay
extends Control

const AUTO_MODIFIER: int = -999999

var _queue: Array[Dictionary] = []
var _running: bool = false
var _backdrop: ColorRect
var _panel: PanelContainer
var _actor_label: Label
var _die_label: Label
var _target_label: Label
var _modifier_label: Label
var _result_label: Label


func _ready() -> void:
	add_to_group("dice_presenter")
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	z_as_relative = false
	z_index = 4096
	_build_ui()
	hide()


func show_d20_roll(
	actor_name: String,
	purpose: String,
	natural: int,
	total: int,
	success: bool,
	first: int = 0,
	second: int = 0,
	target_number: int = 0,
	modifier: int = AUTO_MODIFIER
) -> void:
	var resolved_natural: int = clampi(natural, 1, 20)
	var resolved_modifier: int = total - resolved_natural if modifier == AUTO_MODIFIER else modifier
	_queue.append({
		"actor": actor_name,
		"purpose": purpose,
		"natural": resolved_natural,
		"total": total,
		"success": success,
		"first": first,
		"second": second,
		"target": maxi(target_number, 0),
		"modifier": resolved_modifier
	})
	if not _running:
		call_deferred("_play_queue")


func queued_roll_count() -> int:
	return _queue.size() + (1 if _running else 0)


func _build_ui() -> void:
	_backdrop = ColorRect.new()
	_backdrop.name = "D20Backdrop"
	_backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_backdrop.color = Color(0.0, 0.0, 0.0, 0.58)
	_backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_backdrop)

	_panel = PanelContainer.new()
	_panel.name = "D20ResultPanel"
	_panel.set_anchors_preset(Control.PRESET_CENTER)
	_panel.offset_left = -300.0
	_panel.offset_top = -170.0
	_panel.offset_right = 300.0
	_panel.offset_bottom = 170.0
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.add_theme_stylebox_override("panel", _panel_style())
	add_child(_panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 28)
	margin.add_theme_constant_override("margin_top", 24)
	margin.add_theme_constant_override("margin_right", 28)
	margin.add_theme_constant_override("margin_bottom", 24)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.add_child(margin)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(column)

	_actor_label = Label.new()
	_actor_label.name = "D20ActorLabel"
	_actor_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_actor_label.add_theme_font_size_override("font_size", 23)
	_actor_label.add_theme_color_override("font_color", Color(1.0, 0.90, 0.58, 1.0))
	_actor_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(_actor_label)

	var result_row := HBoxContainer.new()
	result_row.add_theme_constant_override("separation", 22)
	result_row.alignment = BoxContainer.ALIGNMENT_CENTER
	result_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(result_row)

	var die_panel := PanelContainer.new()
	die_panel.custom_minimum_size = Vector2(130.0, 130.0)
	die_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	die_panel.add_theme_stylebox_override("panel", _die_style())
	result_row.add_child(die_panel)

	_die_label = Label.new()
	_die_label.name = "D20NaturalLabel"
	_die_label.text = "d20"
	_die_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_die_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_die_label.add_theme_font_size_override("font_size", 58)
	_die_label.add_theme_color_override("font_color", Color.WHITE)
	_die_label.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.9))
	_die_label.add_theme_constant_override("shadow_offset_x", 3)
	_die_label.add_theme_constant_override("shadow_offset_y", 3)
	die_panel.add_child(_die_label)

	var details_column := VBoxContainer.new()
	details_column.custom_minimum_size = Vector2(330.0, 130.0)
	details_column.add_theme_constant_override("separation", 8)
	details_column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	result_row.add_child(details_column)

	_target_label = Label.new()
	_target_label.name = "D20TargetLabel"
	_target_label.add_theme_font_size_override("font_size", 21)
	_target_label.add_theme_color_override("font_color", Color(0.72, 0.90, 1.0, 1.0))
	details_column.add_child(_target_label)

	_modifier_label = Label.new()
	_modifier_label.name = "D20ModifierLabel"
	_modifier_label.add_theme_font_size_override("font_size", 21)
	_modifier_label.add_theme_color_override("font_color", Color(0.86, 0.86, 0.90, 1.0))
	details_column.add_child(_modifier_label)

	_result_label = Label.new()
	_result_label.name = "D20ResultLabel"
	_result_label.add_theme_font_size_override("font_size", 25)
	_result_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	details_column.add_child(_result_label)


func _play_queue() -> void:
	if _running or _queue.is_empty():
		return
	_running = true
	while not _queue.is_empty():
		var roll: Dictionary = _queue.pop_front()
		show()
		move_to_front()
		_actor_label.text = "%s · %s" % [str(roll.get("actor", "Участник")), str(roll.get("purpose", "Проверка"))]
		_target_label.text = _target_text(int(roll.get("target", 0)))
		_modifier_label.text = "Модификатор: %s" % _signed_number(int(roll.get("modifier", 0)))
		_result_label.text = "Бросок d20..."
		_result_label.add_theme_color_override("font_color", Color.WHITE)
		_backdrop.modulate = Color.WHITE
		_panel.modulate = Color.WHITE
		_panel.scale = Vector2(0.86, 0.86)
		var appear := create_tween()
		appear.set_parallel(true)
		appear.tween_property(_panel, "scale", Vector2.ONE, 0.14)
		appear.tween_property(_backdrop, "modulate:a", 1.0, 0.12)
		for index: int in range(10):
			_die_label.text = str(((index * 7 + int(roll.get("natural", 1))) % 20) + 1)
			_die_label.rotation_degrees = float(index * 34)
			await get_tree().create_timer(0.045).timeout
		var natural: int = int(roll.get("natural", 1))
		var modifier: int = int(roll.get("modifier", 0))
		var total: int = int(roll.get("total", natural + modifier))
		var success: bool = bool(roll.get("success", false))
		_die_label.text = str(natural)
		_die_label.rotation_degrees = 0.0
		var equation: String = "d20 %d %s %s = %d" % [natural, "+" if modifier >= 0 else "−", str(absi(modifier)), total]
		var outcome: String = "УСПЕХ" if success else "НЕУДАЧА"
		var target: int = int(roll.get("target", 0))
		if target > 0:
			outcome += " · нужно %d" % target
		var first: int = int(roll.get("first", 0))
		var second: int = int(roll.get("second", 0))
		if second > 0:
			equation += "\nКости: %d и %d" % [first, second]
		_result_label.text = "%s\n%s" % [equation, outcome]
		_result_label.add_theme_color_override("font_color", Color(0.62, 1.0, 0.68, 1.0) if success else Color(1.0, 0.58, 0.52, 1.0))
		await get_tree().create_timer(1.55).timeout
		var fade := create_tween()
		fade.set_parallel(true)
		fade.tween_property(_panel, "modulate:a", 0.0, 0.18)
		fade.tween_property(_backdrop, "modulate:a", 0.0, 0.18)
		await fade.finished
		hide()
	_running = false


func _target_text(target_number: int) -> String:
	if target_number <= 0:
		return "Нужно выбросить: —"
	return "Нужно выбросить: %d или больше" % target_number


func _signed_number(value: int) -> String:
	return "+%d" % value if value >= 0 else str(value)


func _panel_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.055, 0.075, 0.11, 0.985)
	style.border_color = Color(0.94, 0.72, 0.30, 1.0)
	style.set_border_width_all(5)
	style.corner_radius_top_left = 18
	style.corner_radius_top_right = 18
	style.corner_radius_bottom_left = 18
	style.corner_radius_bottom_right = 18
	style.shadow_color = Color(0.0, 0.0, 0.0, 0.75)
	style.shadow_size = 24
	return style


func _die_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.16, 0.25, 0.42, 1.0)
	style.border_color = Color(0.68, 0.86, 1.0, 1.0)
	style.set_border_width_all(4)
	style.corner_radius_top_left = 20
	style.corner_radius_top_right = 20
	style.corner_radius_bottom_left = 20
	style.corner_radius_bottom_right = 20
	return style
