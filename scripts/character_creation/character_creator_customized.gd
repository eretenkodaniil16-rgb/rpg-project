extends "res://scripts/character_creation/character_creator.gd"

const COLOR_OPTIONS: Array = [
	{"id": "azure", "name": "Лазурный", "hex": "#4DA3E8"},
	{"id": "crimson", "name": "Красный", "hex": "#D95555"},
	{"id": "emerald", "name": "Зелёный", "hex": "#4FB878"},
	{"id": "violet", "name": "Фиолетовый", "hex": "#9368D8"},
	{"id": "gold", "name": "Золотой", "hex": "#E0B84F"}
]

var _selected_color_id: String = "azure"


func _build_name_step() -> void:
	super._build_name_step()
	_add_paragraph("Выберите основной цвет персонажа. Он сохранится вместе с героем и будет отображаться в игре.", Color(0.68, 0.73, 0.82, 1.0))

	var selected_color: Dictionary = _get_selected_color()
	var preview_panel: PanelContainer = PanelContainer.new()
	_content_container.add_child(preview_panel)

	var preview_margin: MarginContainer = MarginContainer.new()
	preview_margin.add_theme_constant_override("margin_left", 18)
	preview_margin.add_theme_constant_override("margin_top", 14)
	preview_margin.add_theme_constant_override("margin_right", 18)
	preview_margin.add_theme_constant_override("margin_bottom", 14)
	preview_panel.add_child(preview_margin)

	var preview_row: HBoxContainer = HBoxContainer.new()
	preview_row.add_theme_constant_override("separation", 18)
	preview_margin.add_child(preview_row)

	var preview: ColorRect = ColorRect.new()
	preview.custom_minimum_size = Vector2(72.0, 72.0)
	preview.color = Color.from_string(str(selected_color.get("hex", PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX)), Color(0.3, 0.64, 0.91, 1.0))
	preview.mouse_filter = Control.MOUSE_FILTER_IGNORE
	preview_row.add_child(preview)

	var preview_text: VBoxContainer = VBoxContainer.new()
	preview_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	preview_row.add_child(preview_text)
	preview_text.add_child(_make_label("Цвет героя: %s" % str(selected_color.get("name", "Лазурный")), 21))
	preview_text.add_child(_make_label("Позже сюда можно будет добавить причёски, одежду и портреты.", 16, Color(0.68, 0.73, 0.82, 1.0)))

	var color_grid: GridContainer = GridContainer.new()
	color_grid.columns = 5
	color_grid.add_theme_constant_override("h_separation", 10)
	color_grid.add_theme_constant_override("v_separation", 10)
	_content_container.add_child(color_grid)

	for color_value: Variant in COLOR_OPTIONS:
		var color_data: Dictionary = color_value as Dictionary
		var color_id: String = str(color_data.get("id", "azure"))
		var color_name: String = str(color_data.get("name", color_id))
		var color: Color = Color.from_string(str(color_data.get("hex", PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX)), Color.WHITE)
		var is_selected: bool = color_id == _selected_color_id
		var button: Button = _make_button(("✓ " if is_selected else "") + color_name, 174.0)
		button.add_theme_font_size_override("font_size", 16)
		button.add_theme_color_override("font_color", Color(0.08, 0.08, 0.1, 1.0) if color.get_luminance() > 0.62 else Color.WHITE)
		button.add_theme_color_override("font_hover_color", Color(0.08, 0.08, 0.1, 1.0) if color.get_luminance() > 0.62 else Color.WHITE)
		button.add_theme_stylebox_override("normal", _make_color_style(color, is_selected, false))
		button.add_theme_stylebox_override("hover", _make_color_style(color, is_selected, true))
		button.add_theme_stylebox_override("pressed", _make_color_style(color.darkened(0.08), true, false))
		button.add_theme_stylebox_override("focus", _make_color_style(color, true, true))
		button.pressed.connect(_select_color.bind(color_id))
		color_grid.add_child(button)


func _build_confirmation_step() -> void:
	super._build_confirmation_step()
	var selected_color: Dictionary = _get_selected_color()
	var color_row: HBoxContainer = HBoxContainer.new()
	color_row.add_theme_constant_override("separation", 14)
	_content_container.add_child(color_row)

	var swatch: ColorRect = ColorRect.new()
	swatch.custom_minimum_size = Vector2(48.0, 48.0)
	swatch.color = Color.from_string(str(selected_color.get("hex", PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX)), Color(0.3, 0.64, 0.91, 1.0))
	swatch.mouse_filter = Control.MOUSE_FILTER_IGNORE
	color_row.add_child(swatch)
	color_row.add_child(_make_label("Выбранный цвет: %s" % str(selected_color.get("name", "Лазурный")), 19))


func _finish_creation() -> void:
	var selected_class: Dictionary = _get_selected_class()
	if selected_class.is_empty():
		_message_label.text = "Выберите класс персонажа."
		return

	var character: PlayerCharacter = PlayerCharacter.new()
	character.character_name = _character_name
	character.character_class_id = _selected_class_id
	character.character_class_name = str(selected_class.get("name", ""))
	character.appearance_color_hex = str(_get_selected_color().get("hex", PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX))
	for ability_id: String in ABILITY_IDS:
		character.abilities[ability_id] = _score_for_ability(ability_id)
	character.maximum_health = _calculate_starting_health(selected_class)
	character.current_health = character.maximum_health

	GameState.begin_new_game(character)
	if not GameState.save_game():
		_message_label.text = "Не удалось сохранить созданного персонажа."
		return
	get_tree().change_scene_to_file(GAME_SCENE)


func _select_color(color_id: String) -> void:
	_selected_color_id = color_id
	_show_step(0)


func _get_selected_color() -> Dictionary:
	for color_value: Variant in COLOR_OPTIONS:
		var color_data: Dictionary = color_value as Dictionary
		if str(color_data.get("id", "")) == _selected_color_id:
			return color_data
	return COLOR_OPTIONS[0] as Dictionary


func _make_color_style(color: Color, selected: bool, hover: bool) -> StyleBoxFlat:
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = color.lightened(0.10) if hover else color
	style.corner_radius_top_left = 10
	style.corner_radius_top_right = 10
	style.corner_radius_bottom_left = 10
	style.corner_radius_bottom_right = 10
	var border_width: int = 4 if selected else 1
	style.border_width_left = border_width
	style.border_width_top = border_width
	style.border_width_right = border_width
	style.border_width_bottom = border_width
	style.border_color = Color.WHITE if selected else Color(1.0, 1.0, 1.0, 0.28)
	return style
