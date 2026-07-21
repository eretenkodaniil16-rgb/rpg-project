class_name D20RollOverlay
extends Control

var _queue: Array[Dictionary] = []
var _running: bool = false
var _panel: PanelContainer
var _actor_label: Label
var _die_label: Label
var _result_label: Label


func _ready() -> void:
	add_to_group("dice_presenter")
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	z_index = 350
	_build_ui()
	hide()


func show_d20_roll(actor_name: String, purpose: String, natural: int, total: int, success: bool, first: int = 0, second: int = 0) -> void:
	_queue.append({
		"actor": actor_name,
		"purpose": purpose,
		"natural": clampi(natural, 1, 20),
		"total": total,
		"success": success,
		"first": first,
		"second": second
	})
	if not _running:
		call_deferred("_play_queue")


func queued_roll_count() -> int:
	return _queue.size() + (1 if _running else 0)


func _build_ui() -> void:
	_panel = PanelContainer.new()
	_panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_panel.offset_left = -155.0
	_panel.offset_top = 78.0
	_panel.offset_right = 155.0
	_panel.offset_bottom = 154.0
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.modulate = Color(1.0, 1.0, 1.0, 0.92)
	add_child(_panel)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 10)
	margin.add_theme_constant_override("margin_top", 7)
	margin.add_theme_constant_override("margin_right", 10)
	margin.add_theme_constant_override("margin_bottom", 7)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.add_child(margin)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(row)
	_die_label = Label.new()
	_die_label.text = "d20"
	_die_label.custom_minimum_size = Vector2(56.0, 56.0)
	_die_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_die_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_die_label.add_theme_font_size_override("font_size", 27)
	row.add_child(_die_label)
	var text_column := VBoxContainer.new()
	text_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text_column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(text_column)
	_actor_label = Label.new()
	_actor_label.add_theme_font_size_override("font_size", 14)
	_actor_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	text_column.add_child(_actor_label)
	_result_label = Label.new()
	_result_label.add_theme_font_size_override("font_size", 14)
	_result_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	text_column.add_child(_result_label)


func _play_queue() -> void:
	if _running or _queue.is_empty():
		return
	_running = true
	while not _queue.is_empty():
		var roll: Dictionary = _queue.pop_front()
		show()
		_actor_label.text = "%s · %s" % [str(roll.get("actor", "Участник")), str(roll.get("purpose", "Проверка"))]
		_result_label.text = "Бросок d20..."
		_panel.modulate = Color(1.0, 1.0, 1.0, 0.92)
		_panel.scale = Vector2(0.94, 0.94)
		var appear := create_tween()
		appear.tween_property(_panel, "scale", Vector2.ONE, 0.08)
		for index: int in range(7):
			_die_label.text = str(((index * 7 + int(roll.get("natural", 1))) % 20) + 1)
			_die_label.rotation_degrees = float(index * 38)
			await get_tree().create_timer(0.028).timeout
		var natural: int = int(roll.get("natural", 1))
		_die_label.text = str(natural)
		_die_label.rotation_degrees = 0.0
		var details: String = "Итог %d · %s" % [int(roll.get("total", natural)), "успех" if bool(roll.get("success", false)) else "неудача"]
		var first: int = int(roll.get("first", 0))
		var second: int = int(roll.get("second", 0))
		if second > 0:
			details += " · %d/%d" % [first, second]
		_result_label.text = details
		await get_tree().create_timer(0.48).timeout
		var fade := create_tween()
		fade.tween_property(_panel, "modulate:a", 0.0, 0.14)
		await fade.finished
		hide()
	_running = false
