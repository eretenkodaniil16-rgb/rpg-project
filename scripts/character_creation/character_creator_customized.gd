extends "res://scripts/character_creation/character_creator.gd"

const CREATION_STEPS: Array[String] = [
	"Имя героя",
	"Выбор расы",
	"Броски характеристик",
	"Распределение значений",
	"Выбор класса",
	"Подтверждение"
]

var _race_data: RaceDataSystem = RaceDataSystem.new()
var _races: Array[Dictionary] = []
var _selected_race_id: String = RaceDataSystem.DEFAULT_RACE_ID
var _custom_creator_initialized: bool = false


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_initialize_custom_creator()


func _initialize_custom_creator() -> void:
	if _custom_creator_initialized:
		return
	_custom_creator_initialized = true
	_build_layout()
	_title_label.text = "Создание персонажа"
	_progress_label.text = "Загрузка данных…"
	_load_classes()
	_races = _race_data.get_races()
	_show_step(0)


func _show_step(step_index: int) -> void:
	_current_step = clampi(step_index, 0, CREATION_STEPS.size() - 1)
	_clear_content()
	_message_label.text = ""
	_title_label.text = CREATION_STEPS[_current_step]
	_progress_label.text = "Шаг %d из %d" % [_current_step + 1, CREATION_STEPS.size()]
	match _current_step:
		0: _build_name_step()
		1: _build_race_step()
		2: _build_roll_step()
		3: _build_assignment_step()
		4: _build_class_step()
		5: _build_confirmation_step()
	_update_navigation()


func _build_name_step() -> void:
	_add_paragraph("Введите имя персонажа. Следующим шагом будет выбор расы, которая определит цвет тестового спрайта и расовые особенности.")
	var name_label: Label = _make_label("Имя", 20)
	_content_container.add_child(name_label)
	var name_input: LineEdit = LineEdit.new()
	name_input.name = "CharacterNameInput"
	name_input.custom_minimum_size = Vector2(0.0, 58.0)
	name_input.placeholder_text = "От 2 до 20 символов"
	name_input.max_length = 20
	name_input.text = _character_name
	name_input.add_theme_font_size_override("font_size", 22)
	name_input.text_changed.connect(_on_name_changed)
	_content_container.add_child(name_input)
	if not OS.has_feature("mobile"):
		name_input.call_deferred("grab_focus")
	_add_paragraph("Имя будет отображаться в сохранении, интерфейсе и диалогах.", Color(0.68, 0.73, 0.82, 1.0))


func _build_race_step() -> void:
	_add_paragraph("Выберите расу. Цветные карточки заменяют прежний выбор цвета: цвет теперь показывает выбранную расу и используется тестовым спрайтом героя.")
	if _races.is_empty():
		_add_paragraph("Не удалось загрузить список рас.", Color(1.0, 0.4, 0.4, 1.0))
		return
	var race_grid: GridContainer = GridContainer.new()
	race_grid.columns = 3
	race_grid.add_theme_constant_override("h_separation", 12)
	race_grid.add_theme_constant_override("v_separation", 12)
	_content_container.add_child(race_grid)
	for race: Dictionary in _races:
		var race_id: String = str(race.get("id", "human"))
		var color: Color = Color.from_string(str(race.get("color_hex", PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX)), Color.WHITE)
		var selected: bool = race_id == _selected_race_id
		var card: Button = Button.new()
		card.custom_minimum_size = Vector2(0.0, 82.0)
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.toggle_mode = true
		card.button_pressed = selected
		card.text = ("✓ " if selected else "") + str(race.get("name", race_id))
		card.add_theme_font_size_override("font_size", 18)
		var font_color: Color = Color(0.07, 0.08, 0.1, 1.0) if color.get_luminance() > 0.62 else Color.WHITE
		card.add_theme_color_override("font_color", font_color)
		card.add_theme_color_override("font_hover_color", font_color)
		card.add_theme_stylebox_override("normal", _make_race_style(color, selected, false))
		card.add_theme_stylebox_override("hover", _make_race_style(color, selected, true))
		card.add_theme_stylebox_override("pressed", _make_race_style(color.darkened(0.08), true, false))
		card.add_theme_stylebox_override("focus", _make_race_style(color, true, true))
		card.pressed.connect(_select_race.bind(race_id))
		race_grid.add_child(card)
	var selected_race: Dictionary = _get_selected_race()
	if selected_race.is_empty():
		return
	var details: PanelContainer = PanelContainer.new()
	_content_container.add_child(details)
	var margin: MarginContainer = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 20)
	margin.add_theme_constant_override("margin_top", 16)
	margin.add_theme_constant_override("margin_right", 20)
	margin.add_theme_constant_override("margin_bottom", 16)
	details.add_child(margin)
	var box: VBoxContainer = VBoxContainer.new()
	box.add_theme_constant_override("separation", 7)
	margin.add_child(box)
	box.add_child(_make_label(str(selected_race.get("name", "")), 25, Color(1.0, 0.82, 0.38, 1.0)))
	var description: Label = _make_label(str(selected_race.get("description", "")), 17)
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(description)
	box.add_child(_make_label("Размер: %s · скорость: %d футов · тёмное зрение: %s" % [
		"маленький" if str(selected_race.get("size", "medium")) == "small" else "средний",
		int(selected_race.get("speed_ft", 30)),
		("нет" if int(selected_race.get("darkvision_ft", 0)) <= 0 else "%d футов" % int(selected_race.get("darkvision_ft", 0)))
	], 17, Color(0.72, 0.82, 1.0, 1.0)))
	var traits_value: Variant = selected_race.get("traits", [])
	if traits_value is Array:
		for trait_value: Variant in traits_value:
			if trait_value is Dictionary:
				var trait_data: Dictionary = trait_value as Dictionary
				var trait_label: Label = _make_label("• %s — %s" % [str(trait_data.get("name", "Особенность")), str(trait_data.get("description", ""))], 16)
				trait_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				box.add_child(trait_label)


func _build_confirmation_step() -> void:
	var selected_class: Dictionary = _get_selected_class()
	var selected_race: Dictionary = _get_selected_race()
	var summary_panel: PanelContainer = PanelContainer.new()
	_content_container.add_child(summary_panel)
	var summary_margin: MarginContainer = MarginContainer.new()
	summary_margin.add_theme_constant_override("margin_left", 26)
	summary_margin.add_theme_constant_override("margin_top", 22)
	summary_margin.add_theme_constant_override("margin_right", 26)
	summary_margin.add_theme_constant_override("margin_bottom", 22)
	summary_panel.add_child(summary_margin)
	var summary: VBoxContainer = VBoxContainer.new()
	summary.add_theme_constant_override("separation", 10)
	summary_margin.add_child(summary)
	summary.add_child(_make_label(_character_name, 30, Color(1.0, 0.82, 0.38, 1.0)))
	summary.add_child(_make_label("Раса: %s" % str(selected_race.get("name", "Не выбрана")), 21))
	summary.add_child(_make_label("Класс: %s · уровень 1" % str(selected_class.get("name", "Не выбран")), 21))
	var health: int = _calculate_starting_health(selected_class) + int(selected_race.get("hp_bonus_per_level", 0))
	summary.add_child(_make_label("Здоровье: %d · скорость: %d футов" % [health, int(selected_race.get("speed_ft", 30))], 20))
	var color_row: HBoxContainer = HBoxContainer.new()
	color_row.add_theme_constant_override("separation", 12)
	summary.add_child(color_row)
	var swatch: ColorRect = ColorRect.new()
	swatch.custom_minimum_size = Vector2(44.0, 44.0)
	swatch.color = Color.from_string(str(selected_race.get("color_hex", PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX)), Color.WHITE)
	color_row.add_child(swatch)
	color_row.add_child(_make_label("Цвет тестового спрайта определяется расой.", 17, Color(0.68, 0.73, 0.82, 1.0)))
	var abilities_grid: GridContainer = GridContainer.new()
	abilities_grid.columns = 3
	abilities_grid.add_theme_constant_override("h_separation", 18)
	abilities_grid.add_theme_constant_override("v_separation", 8)
	summary.add_child(abilities_grid)
	for ability_id: String in ABILITY_IDS:
		var score: int = _score_for_ability(ability_id)
		abilities_grid.add_child(_make_label(str(ABILITY_NAMES[ability_id]), 18))
		var score_label: Label = _make_label(str(score), 20)
		score_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		abilities_grid.add_child(score_label)
		var modifier_label: Label = _make_label(_format_modifier(PlayerCharacter.modifier_for_score(score)), 20, Color(0.72, 0.82, 1.0, 1.0))
		modifier_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		abilities_grid.add_child(modifier_label)
	_add_paragraph("После начала приключения имя, раса, характеристики и класс будут записаны в сохранение.", Color(0.68, 0.73, 0.82, 1.0))


func _finish_creation() -> void:
	var selected_class: Dictionary = _get_selected_class()
	if selected_class.is_empty() or _get_selected_race().is_empty():
		_message_label.text = "Выберите расу и класс персонажа."
		return
	var character: PlayerCharacter = PlayerCharacter.new()
	character.character_name = _character_name
	character.character_class_id = _selected_class_id
	character.character_class_name = str(selected_class.get("name", ""))
	for ability_id: String in ABILITY_IDS:
		character.abilities[ability_id] = _score_for_ability(ability_id)
	character.maximum_health = _calculate_starting_health(selected_class)
	character.current_health = character.maximum_health
	_race_data.apply_race(character, _selected_race_id, false)
	GameState.begin_new_game(character)
	if not GameState.save_game():
		_message_label.text = "Не удалось сохранить созданного персонажа."
		return
	get_tree().change_scene_to_file(GAME_SCENE)


func _select_race(race_id: String) -> void:
	_selected_race_id = race_id
	_show_step(1)


func _get_selected_race() -> Dictionary:
	return _race_data.get_race(_selected_race_id)


func _roll_next_ability_score() -> void:
	if _rolls.size() >= 6:
		return
	var roll_data: Dictionary = _dice_roller.roll_ability_score()
	_rolls.append(roll_data)
	_scores.append(int(roll_data.get("total", 0)))
	_show_step(2)


func _reset_rolls() -> void:
	_rolls.clear()
	_scores.clear()
	_assignments.clear()
	_selected_score_index = -1
	_selected_class_id = ""
	_show_step(2)


func _on_score_pressed(score_index: int) -> void:
	if _is_score_assigned(score_index):
		return
	_selected_score_index = -1 if _selected_score_index == score_index else score_index
	_show_step(3)


func _on_ability_pressed(ability_id: String) -> void:
	if _selected_score_index >= 0:
		var previously_assigned_index: int = -1
		if _assignments.has(ability_id):
			previously_assigned_index = int(_assignments[ability_id])
		_assignments[ability_id] = _selected_score_index
		_selected_score_index = previously_assigned_index
	elif _assignments.has(ability_id):
		_selected_score_index = int(_assignments[ability_id])
		_assignments.erase(ability_id)
	_show_step(3)


func _select_class(class_id: String) -> void:
	_selected_class_id = class_id
	_show_step(4)


func _on_back_pressed() -> void:
	if _current_step <= 0:
		_return_to_menu()
	else:
		_show_step(_current_step - 1)


func _on_next_pressed() -> void:
	if not _can_continue_current_step():
		_message_label.text = _validation_message_for_step()
		return
	if _current_step < CREATION_STEPS.size() - 1:
		_show_step(_current_step + 1)
	else:
		_finish_creation()


func _update_navigation() -> void:
	_back_button.text = "В меню" if _current_step == 0 else "Назад"
	_next_button.text = "Начать приключение" if _current_step == CREATION_STEPS.size() - 1 else "Продолжить"
	_next_button.disabled = not _can_continue_current_step()


func _can_continue_current_step() -> bool:
	match _current_step:
		0: return _is_name_valid()
		1: return not _selected_race_id.is_empty()
		2: return _rolls.size() == 6
		3: return _assignments.size() == ABILITY_IDS.size()
		4: return not _selected_class_id.is_empty()
		5: return _is_name_valid() and not _selected_race_id.is_empty() and _assignments.size() == ABILITY_IDS.size() and not _selected_class_id.is_empty()
	return false


func _validation_message_for_step() -> String:
	match _current_step:
		0: return "Введите имя длиной от 2 до 20 символов."
		1: return "Выберите расу персонажа."
		2: return "Выполните все шесть бросков характеристик."
		3: return "Распределите все шесть значений."
		4: return "Выберите класс персонажа."
	return "Не все данные заполнены."


func _make_race_style(color: Color, selected: bool, hover: bool) -> StyleBoxFlat:
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = color.lightened(0.10) if hover else color
	style.corner_radius_top_left = 10
	style.corner_radius_top_right = 10
	style.corner_radius_bottom_left = 10
	style.corner_radius_bottom_right = 10
	var width: int = 4 if selected else 1
	style.set_border_width_all(width)
	style.border_color = Color.WHITE if selected else Color(1.0, 1.0, 1.0, 0.28)
	return style
