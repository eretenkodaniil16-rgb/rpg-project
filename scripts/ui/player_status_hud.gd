class_name PlayerStatusHud
extends Control

var _character: PlayerCharacter
var _portrait_style: StyleBoxFlat
var _portrait_label: Label
var _identity_label: Label
var _health_label: Label
var _health_bar: ProgressBar
var _experience_label: Label
var _experience_bar: ProgressBar
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
	var signature: String = "%s|%s|%s|%d|%d|%d|%d" % [
		_character.character_name,
		_character.race_id,
		_character.character_class_id,
		_character.level,
		_character.current_health,
		_character.maximum_health,
		_character.experience
	]
	if signature == _last_signature:
		return
	_last_signature = signature
	_refresh()


func _build_ui() -> void:
	var panel := PanelContainer.new()
	panel.name = "PlayerStatusPanel"
	panel.position = Vector2(20.0, 104.0)
	panel.size = Vector2(350.0, 116.0)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.modulate = Color(1.0, 1.0, 1.0, 0.94)
	add_child(panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 10)
	margin.add_theme_constant_override("margin_top", 9)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_bottom", 9)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(margin)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(row)

	var portrait := PanelContainer.new()
	portrait.name = "PlayerPortrait"
	portrait.custom_minimum_size = Vector2(82.0, 82.0)
	portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_portrait_style = StyleBoxFlat.new()
	_portrait_style.bg_color = Color.from_string(PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX, Color(0.3, 0.64, 0.91, 1.0))
	_portrait_style.border_width_left = 3
	_portrait_style.border_width_top = 3
	_portrait_style.border_width_right = 3
	_portrait_style.border_width_bottom = 3
	_portrait_style.border_color = Color(0.88, 0.94, 1.0, 0.9)
	_portrait_style.corner_radius_top_left = 12
	_portrait_style.corner_radius_top_right = 12
	_portrait_style.corner_radius_bottom_left = 12
	_portrait_style.corner_radius_bottom_right = 12
	portrait.add_theme_stylebox_override("panel", _portrait_style)
	row.add_child(portrait)

	_portrait_label = Label.new()
	_portrait_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_portrait_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_portrait_label.add_theme_font_size_override("font_size", 34)
	_portrait_label.add_theme_color_override("font_color", Color.WHITE)
	_portrait_label.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.85))
	_portrait_label.add_theme_constant_override("shadow_offset_x", 2)
	_portrait_label.add_theme_constant_override("shadow_offset_y", 2)
	portrait.add_child(_portrait_label)

	var column := VBoxContainer.new()
	column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	column.add_theme_constant_override("separation", 3)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(column)

	_identity_label = Label.new()
	_identity_label.add_theme_font_size_override("font_size", 17)
	column.add_child(_identity_label)

	_health_label = Label.new()
	_health_label.add_theme_font_size_override("font_size", 14)
	column.add_child(_health_label)

	_health_bar = ProgressBar.new()
	_health_bar.name = "GameplayHealthBar"
	_health_bar.custom_minimum_size = Vector2(0.0, 18.0)
	_health_bar.show_percentage = false
	_health_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(_health_bar)

	_experience_label = Label.new()
	_experience_label.add_theme_font_size_override("font_size", 14)
	column.add_child(_experience_label)

	_experience_bar = ProgressBar.new()
	_experience_bar.name = "GameplayExperienceBar"
	_experience_bar.custom_minimum_size = Vector2(0.0, 14.0)
	_experience_bar.show_percentage = false
	_experience_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(_experience_bar)


func _refresh() -> void:
	if _character == null or _health_bar == null:
		return
	_portrait_style.bg_color = Color.from_string(
		_character.appearance_color_hex,
		Color.from_string(PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX, Color(0.3, 0.64, 0.91, 1.0))
	)
	_portrait_label.text = _initials(_character.character_name)
	_identity_label.text = "%s · ур. %d" % [_character.character_name, _character.level]
	_health_label.text = "Здоровье %d/%d" % [_character.current_health, _character.maximum_health]
	_health_bar.max_value = maxi(_character.maximum_health, 1)
	_health_bar.value = clampi(_character.current_health, 0, _character.maximum_health)
	var progress: int = ProgressionSystem.experience_progress_in_level(_character)
	var required: int = ProgressionSystem.experience_required_for_next_level(_character)
	_experience_label.text = "Опыт %d/%d" % [progress, required]
	_experience_bar.max_value = maxi(required, 1)
	_experience_bar.value = clampi(progress, 0, required)


func _initials(value: String) -> String:
	var words: PackedStringArray = value.strip_edges().split(" ", false)
	if words.is_empty():
		return "?"
	var result: String = words[0].left(1).to_upper()
	if words.size() > 1:
		result += words[1].left(1).to_upper()
	return result
