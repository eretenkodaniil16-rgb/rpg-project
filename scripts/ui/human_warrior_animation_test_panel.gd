extends CanvasLayer

const MODE_AUTO: StringName = &"auto"
const MODE_UNARMED: StringName = &"unarmed"
const MODE_ONEHAND: StringName = &"onehand"
const MODE_TWOHAND: StringName = &"twohand"

var _player: Node = null
var _combat_preview: bool = false
var _combat_button: Button = null
var _status_label: Label = null
var _refresh_accumulator: float = 0.0


func configure(player: Node) -> void:
	_player = player
	name = "HumanWarriorAnimationTestPanel"
	layer = 40
	_build_ui()
	_refresh_status()


func _process(delta: float) -> void:
	_refresh_accumulator += delta
	if _refresh_accumulator < 0.2:
		return
	_refresh_accumulator = 0.0
	_refresh_status()


func _build_ui() -> void:
	var panel := PanelContainer.new()
	panel.name = "AnimationTestPanel"
	panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	panel.offset_left = -286.0
	panel.offset_top = 104.0
	panel.offset_right = 286.0
	panel.offset_bottom = 162.0
	add_child(panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 8)
	margin.add_theme_constant_override("margin_top", 6)
	margin.add_theme_constant_override("margin_right", 8)
	margin.add_theme_constant_override("margin_bottom", 6)
	panel.add_child(margin)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 5)
	margin.add_child(row)

	_status_label = Label.new()
	_status_label.custom_minimum_size = Vector2(124.0, 0.0)
	_status_label.add_theme_font_size_override("font_size", 13)
	row.add_child(_status_label)

	_add_mode_button(row, "АВТО", MODE_AUTO)
	_add_mode_button(row, "БЕЗ", MODE_UNARMED)
	_add_mode_button(row, "1Р", MODE_ONEHAND)
	_add_mode_button(row, "2Р", MODE_TWOHAND)

	_combat_button = Button.new()
	_combat_button.custom_minimum_size = Vector2(94.0, 38.0)
	_combat_button.add_theme_font_size_override("font_size", 13)
	_combat_button.pressed.connect(_toggle_combat_preview)
	row.add_child(_combat_button)


func _add_mode_button(parent: HBoxContainer, label: String, mode: StringName) -> void:
	var button := Button.new()
	button.text = label
	button.custom_minimum_size = Vector2(58.0, 38.0)
	button.add_theme_font_size_override("font_size", 13)
	button.pressed.connect(_select_mode.bind(mode))
	parent.add_child(button)


func _select_mode(mode: StringName) -> void:
	if is_instance_valid(_player) and _player.has_method("set_visual_preview_mode"):
		_player.call("set_visual_preview_mode", mode)
	_refresh_status()


func _toggle_combat_preview() -> void:
	_combat_preview = not _combat_preview
	if is_instance_valid(_player) and _player.has_method("set_visual_combat_preview"):
		_player.call("set_visual_combat_preview", _combat_preview)
	_refresh_status()


func _refresh_status() -> void:
	if _combat_button != null:
		_combat_button.text = "БОЙ: %s" % ("ВКЛ" if _combat_preview else "ВЫКЛ")
	if _status_label == null:
		return
	if not is_instance_valid(_player) or not _player.has_method("get_visual_debug_state"):
		_status_label.text = "Анимация недоступна"
		return
	var state: Dictionary = _player.call("get_visual_debug_state") as Dictionary
	_status_label.text = "%s\n%s" % [
		str(state.get("mode", "auto")),
		str(state.get("animation", "fallback"))
	]
