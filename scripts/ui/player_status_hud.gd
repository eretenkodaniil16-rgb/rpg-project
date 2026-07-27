class_name PlayerStatusHud
extends Control

var _character: PlayerCharacter
var _health_label: Label
var _health_bar: ProgressBar
var _last_signature: String = ""


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	z_index = 80
	_build_ui()
	set_process(true)


func bind_character(character: PlayerCharacter) -> void:
	_character = character
	_last_signature = ""
	_refresh()


func _process(_delta: float) -> void:
	if _character == null:
		return
	var signature: String = "%d|%d" % [
		_character.current_health,
		_character.maximum_health
	]
	if signature == _last_signature:
		return
	_last_signature = signature
	_refresh()


func _build_ui() -> void:
	var panel := PanelContainer.new()
	panel.name = "PlayerStatusPanel"
	panel.position = Vector2(18.0, 104.0)
	panel.size = Vector2(270.0, 48.0)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.modulate = Color(1.0, 1.0, 1.0, 0.88)
	add_child(panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 10)
	margin.add_theme_constant_override("margin_top", 7)
	margin.add_theme_constant_override("margin_right", 10)
	margin.add_theme_constant_override("margin_bottom", 7)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(margin)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(row)

	_health_label = Label.new()
	_health_label.custom_minimum_size = Vector2(82.0, 0.0)
	_health_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_health_label.add_theme_font_size_override("font_size", 15)
	row.add_child(_health_label)

	_health_bar = ProgressBar.new()
	_health_bar.name = "GameplayHealthBar"
	_health_bar.custom_minimum_size = Vector2(160.0, 24.0)
	_health_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_health_bar.show_percentage = false
	_health_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(_health_bar)


func _refresh() -> void:
	if _character == null or _health_bar == null:
		return
	_health_label.text = "HP %d/%d" % [_character.current_health, _character.maximum_health]
	_health_bar.max_value = maxi(_character.maximum_health, 1)
	_health_bar.value = clampi(_character.current_health, 0, _character.maximum_health)
