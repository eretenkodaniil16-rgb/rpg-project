class_name ExperienceRewardToast
extends Control

signal notification_shown(text: String)

var _panel: PanelContainer
var _label: Label
var _queue: Array[String] = []
var _showing: bool = false


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	z_index = 3950
	_build_ui()
	var state: Node = _game_state()
	if state == null:
		return
	if state.has_signal("experience_gained"):
		state.connect("experience_gained", Callable(self, "_on_experience_gained"))
	if state.has_signal("level_up_available"):
		state.connect("level_up_available", Callable(self, "_on_level_up_available"))


func get_current_text_for_testing() -> String:
	return _label.text if _label != null else ""


func _build_ui() -> void:
	_panel = PanelContainer.new()
	_panel.name = "ExperienceRewardPanel"
	_panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_panel.offset_left = -280.0
	_panel.offset_top = 22.0
	_panel.offset_right = 280.0
	_panel.offset_bottom = 94.0
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.hide()
	add_child(_panel)

	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.055, 0.075, 0.11, 0.96)
	style.border_color = Color(0.78, 0.61, 0.25, 1.0)
	style.set_border_width_all(3)
	style.corner_radius_top_left = 14
	style.corner_radius_top_right = 14
	style.corner_radius_bottom_left = 14
	style.corner_radius_bottom_right = 14
	_panel.add_theme_stylebox_override("panel", style)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 18)
	margin.add_theme_constant_override("margin_top", 12)
	margin.add_theme_constant_override("margin_right", 18)
	margin.add_theme_constant_override("margin_bottom", 12)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.add_child(margin)

	_label = Label.new()
	_label.name = "ExperienceRewardLabel"
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_label.add_theme_font_size_override("font_size", 19)
	_label.add_theme_color_override("font_color", Color(1.0, 0.93, 0.72, 1.0))
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(_label)


func _on_experience_gained(_reward_id: String, amount: int, _total_experience: int, label: String) -> void:
	_enqueue("+%d опыта · %s" % [amount, label])


func _on_level_up_available(_current_level: int, target_level: int, pending_level_count: int) -> void:
	var suffix: String = ""
	if pending_level_count > 1:
		suffix = " · доступно уровней: %d" % pending_level_count
	_enqueue("ДОСТУПНО ПОВЫШЕНИЕ ДО %d УРОВНЯ%s" % [target_level, suffix])


func _enqueue(text: String) -> void:
	if text.is_empty():
		return
	_queue.append(text)
	if not _showing:
		_show_next.call_deferred()


func _show_next() -> void:
	if _showing or _queue.is_empty() or _panel == null:
		return
	_showing = true
	_label.text = _queue.pop_front()
	_panel.modulate = Color(1.0, 1.0, 1.0, 0.0)
	_panel.show()
	notification_shown.emit(_label.text)
	var fade_in: Tween = create_tween()
	fade_in.tween_property(_panel, "modulate:a", 1.0, 0.12)
	await fade_in.finished
	await get_tree().create_timer(1.7).timeout
	var fade_out: Tween = create_tween()
	fade_out.tween_property(_panel, "modulate:a", 0.0, 0.18)
	await fade_out.finished
	_panel.hide()
	_showing = false
	if not _queue.is_empty():
		_show_next.call_deferred()


func _game_state() -> Node:
	var main_loop: MainLoop = Engine.get_main_loop()
	if main_loop is SceneTree:
		return (main_loop as SceneTree).root.get_node_or_null("GameState")
	return null
