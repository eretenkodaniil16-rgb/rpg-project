extends "res://scripts/character_creation/character_creator.gd"

const CREATION_STEPS: Array[String] = [
	"Имя героя",
	"Выбор расы",
	"Броски характеристик",
	"Распределение значений",
	"Происхождение",
	"Выбор класса",
	"Подтверждение"
]
const SKILL_NAMES: Dictionary = {
	"acrobatics": "Акробатика",
	"animal_handling": "Уход за животными",
	"arcana": "Магия",
	"athletics": "Атлетика",
	"deception": "Обман",
	"history": "История",
	"insight": "Проницательность",
	"intimidation": "Запугивание",
	"investigation": "Анализ",
	"medicine": "Медицина",
	"nature": "Природа",
	"perception": "Восприятие",
	"performance": "Выступление",
	"persuasion": "Убеждение",
	"religion": "Религия",
	"sleight_of_hand": "Ловкость рук",
	"stealth": "Скрытность",
	"survival": "Выживание"
}

var _race_data: RaceDataSystem = RaceDataSystem.new()
var _origin_data: OriginDataSystem = OriginDataSystem.new()
var _class_proficiencies: ClassProficiencySystem = ClassProficiencySystem.new()
var _races: Array[Dictionary] = []
var _backgrounds: Array[Dictionary] = []
var _languages: Array[Dictionary] = []
var _selected_race_id: String = RaceDataSystem.DEFAULT_RACE_ID
var _selected_background_id: String = OriginDataSystem.DEFAULT_BACKGROUND_ID
var _background_ability_bonuses: Dictionary = {}
var _selected_languages: Array[String] = []
var _selected_class_skill_ids: Array[String] = []
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
	_backgrounds = _origin_data.get_backgrounds()
	_languages = _origin_data.get_standard_languages()
	_background_ability_bonuses = _origin_data.default_ability_bonuses(_selected_background_id)
	_selected_languages = _origin_data.default_languages()
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
		4: _build_origin_step()
		5: _build_class_step()
		6: _build_confirmation_step()
	_update_navigation()


func _build_name_step() -> void:
	_add_paragraph("Введите имя персонажа. Затем вы выберете вид, происхождение и класс по правилам SRD 5.2.1.")
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
	_add_paragraph("Выберите вид персонажа. Вид определяет размер, скорость и врождённые особенности, но не повышает характеристики.")
	if _races.is_empty():
		_add_paragraph("Не удалось загрузить список видов.", Color(1.0, 0.4, 0.4, 1.0))
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


func _build_origin_step() -> void:
	_add_paragraph("Происхождение даёт три очка характеристик, начальную черту, два навыка и владение инструментом. Общий язык известен автоматически; дополнительно выберите два стандартных языка.")
	if _backgrounds.is_empty():
		_add_paragraph("Не удалось загрузить происхождения.", Color(1.0, 0.4, 0.4, 1.0))
		return
	var background_grid: GridContainer = GridContainer.new()
	background_grid.columns = 2
	background_grid.add_theme_constant_override("h_separation", 12)
	background_grid.add_theme_constant_override("v_separation", 12)
	_content_container.add_child(background_grid)
	for background: Dictionary in _backgrounds:
		var background_id: String = str(background.get("id", ""))
		var selected: bool = background_id == _selected_background_id
		var card: Button = _make_button(("✓ " if selected else "") + str(background.get("name", background_id)), 0.0)
		card.toggle_mode = true
		card.button_pressed = selected
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.custom_minimum_size.y = 72.0
		card.pressed.connect(_select_background.bind(background_id))
		background_grid.add_child(card)

	var selected_background: Dictionary = _get_selected_background()
	if selected_background.is_empty():
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
	box.add_theme_constant_override("separation", 8)
	margin.add_child(box)
	box.add_child(_make_label(str(selected_background.get("name", "")), 25, Color(1.0, 0.82, 0.38, 1.0)))
	var description: Label = _make_label(str(selected_background.get("description", "")), 17)
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(description)
	box.add_child(_make_label("Начальная черта: %s" % str(selected_background.get("origin_feat_name", selected_background.get("origin_feat_id", "—"))), 18))
	box.add_child(_make_label("Навыки: %s" % _display_skill_ids(selected_background.get("skill_proficiencies", [])), 18))
	box.add_child(_make_label("Инструмент: %s" % _display_tool_ids(selected_background.get("tool_proficiencies", [])), 18))

	box.add_child(_make_label("Распределение характеристик", 21, Color(0.72, 0.82, 1.0, 1.0)))
	var bonus_options: Variant = selected_background.get("ability_options", [])
	if bonus_options is Array:
		var bonus_row: HBoxContainer = HBoxContainer.new()
		bonus_row.add_theme_constant_override("separation", 10)
		box.add_child(bonus_row)
		for ability_value: Variant in bonus_options:
			var ability_id: String = str(ability_value)
			var bonus: int = int(_background_ability_bonuses.get(ability_id, 0))
			var base_score: int = _score_for_ability(ability_id)
			var bonus_button: Button = _make_button("%s\n%d %+d = %d" % [
				str(ABILITY_NAMES.get(ability_id, ability_id)),
				base_score,
				bonus,
				base_score + bonus
			], 190.0)
			bonus_button.pressed.connect(_cycle_background_bonus.bind(ability_id))
			bonus_row.add_child(bonus_button)
	var bonus_validation: Dictionary = _origin_data.validate_ability_bonuses(_selected_background_id, _background_ability_bonuses, _base_abilities_dict())
	box.add_child(_make_label(str(bonus_validation.get("message", "")), 16, Color(0.63, 0.88, 0.67, 1.0) if bool(bonus_validation.get("success", false)) else Color(1.0, 0.68, 0.38, 1.0)))

	box.add_child(_make_label("Дополнительные языки", 21, Color(0.72, 0.82, 1.0, 1.0)))
	for slot_index: int in range(2):
		var language_row: HBoxContainer = HBoxContainer.new()
		language_row.add_theme_constant_override("separation", 12)
		box.add_child(language_row)
		language_row.add_child(_make_label("Язык %d" % (slot_index + 1), 18))
		var picker: OptionButton = OptionButton.new()
		picker.custom_minimum_size = Vector2(320.0, 54.0)
		picker.add_theme_font_size_override("font_size", 18)
		var selected_index: int = 0
		for language_index: int in range(_languages.size()):
			var language: Dictionary = _languages[language_index]
			picker.add_item(str(language.get("name", language.get("id", ""))), language_index)
			if slot_index < _selected_languages.size() and str(language.get("id", "")) == _selected_languages[slot_index]:
				selected_index = language_index
		picker.select(selected_index)
		picker.item_selected.connect(_on_language_selected.bind(slot_index))
		language_row.add_child(picker)
	var language_validation: Dictionary = _origin_data.validate_languages(_selected_languages)
	box.add_child(_make_label(str(language_validation.get("message", "")), 16, Color(0.63, 0.88, 0.67, 1.0) if bool(language_validation.get("success", false)) else Color(1.0, 0.68, 0.38, 1.0)))


func _append_class_proficiency_controls() -> void:
	var selected_class: Dictionary = _get_selected_class()
	if selected_class.is_empty():
		return
	_ensure_class_skill_selection()
	var panel: PanelContainer = PanelContainer.new()
	panel.name = "ClassTrainingPanel"
	_content_container.add_child(panel)
	var margin: MarginContainer = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 20)
	margin.add_theme_constant_override("margin_top", 18)
	margin.add_theme_constant_override("margin_right", 20)
	margin.add_theme_constant_override("margin_bottom", 18)
	panel.add_child(margin)
	var box: VBoxContainer = VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	margin.add_child(box)
	box.add_child(_make_label("Подготовка класса", 24, Color(1.0, 0.82, 0.38, 1.0)))
	box.add_child(_make_label("Оружие: %s" % _display_weapon_training(selected_class.get("weapon_proficiencies", [])), 17))
	box.add_child(_make_label("Доспехи: %s" % _display_armor_training(selected_class.get("armor_training", [])), 17))
	var required: int = _class_proficiencies.get_skill_choice_count(selected_class)
	box.add_child(_make_label("Выберите навыки класса · %d из %d" % [_selected_class_skill_ids.size(), required], 20, Color(0.72, 0.82, 1.0, 1.0)))
	var unavailable: Array[String] = _background_skill_ids()
	var options_grid: GridContainer = GridContainer.new()
	options_grid.name = "ClassSkillGrid"
	options_grid.columns = 2
	options_grid.add_theme_constant_override("h_separation", 10)
	options_grid.add_theme_constant_override("v_separation", 10)
	box.add_child(options_grid)
	for skill_id: String in _class_proficiencies.get_skill_options(selected_class):
		var selected: bool = skill_id in _selected_class_skill_ids
		var already_from_origin: bool = skill_id in unavailable
		var button: Button = Button.new()
		button.name = "ClassSkill_%s" % skill_id
		button.custom_minimum_size = Vector2(0.0, 56.0)
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.toggle_mode = true
		button.button_pressed = selected
		button.text = ("%s " % ("✓" if selected else "○")) + str(SKILL_NAMES.get(skill_id, skill_id))
		if already_from_origin:
			button.text += " · из происхождения"
		button.disabled = already_from_origin or (not selected and _selected_class_skill_ids.size() >= required)
		button.add_theme_font_size_override("font_size", 17)
		button.pressed.connect(_toggle_class_skill.bind(skill_id))
		options_grid.add_child(button)
	var validation: Dictionary = _class_skill_validation()
	var validation_label: Label = _make_label(
		str(validation.get("message", "")),
		16,
		Color(0.63, 0.88, 0.67, 1.0) if bool(validation.get("success", false)) else Color(1.0, 0.68, 0.38, 1.0)
	)
	validation_label.name = "ClassSkillValidation"
	box.add_child(validation_label)


func _toggle_class_skill(skill_id: String) -> void:
	if skill_id in _background_skill_ids():
		return
	if skill_id in _selected_class_skill_ids:
		_selected_class_skill_ids.erase(skill_id)
	else:
		var required: int = _class_proficiencies.get_skill_choice_count(_get_selected_class())
		if _selected_class_skill_ids.size() >= required:
			return
		_selected_class_skill_ids.append(skill_id)
	_show_step(5)


func _append_class_training_summary(container: VBoxContainer, selected_class: Dictionary) -> void:
	_ensure_class_skill_selection()
	container.add_child(_make_label("Навыки класса: %s" % _display_skill_ids(_selected_class_skill_ids), 18))
	container.add_child(_make_label("Владение оружием: %s" % _display_weapon_training(selected_class.get("weapon_proficiencies", [])), 18))
	container.add_child(_make_label("Обучение доспехам: %s" % _display_armor_training(selected_class.get("armor_training", [])), 18))


func _build_confirmation_step() -> void:
	var selected_class: Dictionary = _get_selected_class()
	var selected_race: Dictionary = _get_selected_race()
	var selected_background: Dictionary = _get_selected_background()
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
	summary.add_child(_make_label("Вид: %s" % str(selected_race.get("name", "Не выбран")), 21))
	summary.add_child(_make_label("Происхождение: %s" % str(selected_background.get("name", "Не выбрано")), 21))
	summary.add_child(_make_label("Класс: %s · уровень 1" % str(selected_class.get("name", "Не выбран")), 21))
	var health: int = _calculate_starting_health(selected_class) + int(selected_race.get("hp_bonus_per_level", 0))
	summary.add_child(_make_label("Здоровье: %d · скорость: %d футов · мастерство: +2" % [health, int(selected_race.get("speed_ft", 30))], 20))
	summary.add_child(_make_label("Черта происхождения: %s" % str(selected_background.get("origin_feat_name", "—")), 18))
	summary.add_child(_make_label("Навыки происхождения: %s" % _display_skill_ids(selected_background.get("skill_proficiencies", [])), 18))
	_append_class_training_summary(summary, selected_class)
	summary.add_child(_make_label("Языки: Общий, %s" % _display_language_ids(_selected_languages), 18))
	var abilities_grid: GridContainer = GridContainer.new()
	abilities_grid.columns = 3
	abilities_grid.add_theme_constant_override("h_separation", 18)
	abilities_grid.add_theme_constant_override("v_separation", 8)
	summary.add_child(abilities_grid)
	for ability_id: String in ABILITY_IDS:
		var score: int = _score_with_origin_bonus(ability_id)
		abilities_grid.add_child(_make_label(str(ABILITY_NAMES[ability_id]), 18))
		var score_label: Label = _make_label(str(score), 20)
		score_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		abilities_grid.add_child(score_label)
		var modifier_label: Label = _make_label(_format_modifier(PlayerCharacter.modifier_for_score(score)), 20, Color(0.72, 0.82, 1.0, 1.0))
		modifier_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		abilities_grid.add_child(modifier_label)
	_add_paragraph("После начала приключения имя, вид, происхождение, языки, характеристики, владения и класс будут записаны в сохранение.", Color(0.68, 0.73, 0.82, 1.0))


func _finish_creation() -> void:
	var selected_class: Dictionary = _get_selected_class()
	var selected_race: Dictionary = _get_selected_race()
	if selected_class.is_empty() or selected_race.is_empty() or not _is_origin_configuration_valid() or not _is_class_skill_configuration_valid():
		_message_label.text = "Заполните вид, происхождение, языки, характеристики, класс и классовые навыки персонажа."
		return
	var character: PlayerCharacter = PlayerCharacter.new()
	character.character_name = _character_name
	character.character_class_id = _selected_class_id
	character.character_class_name = str(selected_class.get("name", ""))
	for ability_id: String in ABILITY_IDS:
		var base_score: int = _score_for_ability(ability_id)
		character.base_abilities[ability_id] = base_score
		character.abilities[ability_id] = base_score
	var origin_result: Dictionary = _origin_data.apply_background(
		character,
		_selected_background_id,
		_background_ability_bonuses,
		_selected_languages
	)
	if not bool(origin_result.get("success", false)):
		_message_label.text = str(origin_result.get("message", "Не удалось применить происхождение."))
		return
	var class_result: Dictionary = _class_proficiencies.apply_class_proficiencies(
		character,
		selected_class,
		_selected_class_skill_ids,
		false
	)
	if not bool(class_result.get("success", false)):
		_message_label.text = str(class_result.get("message", "Не удалось применить владения класса."))
		return
	character.maximum_health = maxi(int(selected_class.get("hit_die", 8)) + character.get_ability_modifier("constitution"), 1)
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


func _select_background(background_id: String) -> void:
	_selected_background_id = background_id
	_background_ability_bonuses = _origin_data.default_ability_bonuses(background_id)
	if not _selected_class_id.is_empty():
		_selected_class_skill_ids.clear()
		_ensure_class_skill_selection()
	_show_step(4)


func _get_selected_background() -> Dictionary:
	return _origin_data.get_background(_selected_background_id)


func _cycle_background_bonus(ability_id: String) -> void:
	var current: int = int(_background_ability_bonuses.get(ability_id, 0))
	var updated: int = (current + 1) % 3
	if updated == 0:
		_background_ability_bonuses.erase(ability_id)
	else:
		_background_ability_bonuses[ability_id] = updated
	_show_step(4)


func _on_language_selected(item_index: int, slot_index: int) -> void:
	if item_index < 0 or item_index >= _languages.size():
		return
	while _selected_languages.size() < 2:
		_selected_languages.append("")
	_selected_languages[slot_index] = str(_languages[item_index].get("id", ""))
	_update_navigation()


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
	_selected_class_skill_ids.clear()
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
	if class_id != _selected_class_id:
		_selected_class_skill_ids.clear()
	_selected_class_id = class_id
	_ensure_class_skill_selection()
	_show_step(5)


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
		4: return _is_origin_configuration_valid()
		5: return not _selected_class_id.is_empty() and _is_class_skill_configuration_valid()
		6: return _is_name_valid() and not _selected_race_id.is_empty() and _assignments.size() == ABILITY_IDS.size() and _is_origin_configuration_valid() and not _selected_class_id.is_empty() and _is_class_skill_configuration_valid()
	return false


func _validation_message_for_step() -> String:
	match _current_step:
		0: return "Введите имя длиной от 2 до 20 символов."
		1: return "Выберите вид персонажа."
		2: return "Выполните все шесть бросков характеристик."
		3: return "Распределите все шесть значений."
		4:
			var bonus_validation: Dictionary = _origin_data.validate_ability_bonuses(_selected_background_id, _background_ability_bonuses, _base_abilities_dict())
			if not bool(bonus_validation.get("success", false)):
				return str(bonus_validation.get("message", "Распределите бонусы происхождения."))
			return str(_origin_data.validate_languages(_selected_languages).get("message", "Выберите два языка."))
		5:
			if _selected_class_id.is_empty():
				return "Выберите класс персонажа."
			return str(_class_skill_validation().get("message", "Выберите классовые навыки."))
	return "Не все данные заполнены."


func _is_origin_configuration_valid() -> bool:
	return bool(_origin_data.validate_ability_bonuses(_selected_background_id, _background_ability_bonuses, _base_abilities_dict()).get("success", false)) and bool(_origin_data.validate_languages(_selected_languages).get("success", false))


func _ensure_class_skill_selection() -> void:
	var selected_class: Dictionary = _get_selected_class()
	if selected_class.is_empty():
		_selected_class_skill_ids.clear()
		return
	if _selected_class_skill_ids.is_empty():
		_selected_class_skill_ids = _class_proficiencies.get_default_skill_choices(selected_class, _background_skill_ids())


func _class_skill_validation() -> Dictionary:
	return _class_proficiencies.validate_skill_choices(
		_get_selected_class(),
		_selected_class_skill_ids,
		_background_skill_ids()
	)


func _is_class_skill_configuration_valid() -> bool:
	return bool(_class_skill_validation().get("success", false))


func _background_skill_ids() -> Array[String]:
	var result: Array[String] = []
	var selected_background: Dictionary = _get_selected_background()
	var value: Variant = selected_background.get("skill_proficiencies", [])
	if value is Array:
		for skill_value: Variant in value:
			var skill_id: String = str(skill_value)
			if not skill_id.is_empty() and skill_id not in result:
				result.append(skill_id)
	return result


func _base_abilities_dict() -> Dictionary:
	var result: Dictionary = {}
	for ability_id: String in ABILITY_IDS:
		result[ability_id] = _score_for_ability(ability_id)
	return result


func _score_with_origin_bonus(ability_id: String) -> int:
	return _score_for_ability(ability_id) + int(_background_ability_bonuses.get(ability_id, 0))


func _calculate_starting_health(class_data: Dictionary) -> int:
	if class_data.is_empty():
		return 1
	return maxi(int(class_data.get("hit_die", 8)) + PlayerCharacter.modifier_for_score(_score_with_origin_bonus("constitution")), 1)


func _best_primary_score(class_data: Dictionary) -> int:
	var best_score: int = 0
	var primary_abilities: Variant = class_data.get("primary_abilities", [])
	if primary_abilities is Array:
		for ability_value: Variant in primary_abilities:
			best_score = maxi(best_score, _score_with_origin_bonus(str(ability_value)))
	return best_score


func _display_skill_ids(value: Variant) -> String:
	var names: Array[String] = []
	if value is Array:
		for item: Variant in value:
			var skill_id: String = str(item)
			names.append(str(SKILL_NAMES.get(skill_id, skill_id)))
	return ", ".join(names)


func _display_tool_ids(value: Variant) -> String:
	var names: Array[String] = []
	var tool_names: Dictionary = {
		"calligraphers_supplies": "принадлежности каллиграфа",
		"thieves_tools": "воровские инструменты",
		"gaming_set_choice": "один игровой набор"
	}
	if value is Array:
		for item: Variant in value:
			var tool_id: String = str(item)
			names.append(str(tool_names.get(tool_id, tool_id)))
	return ", ".join(names)


func _display_weapon_training(value: Variant) -> String:
	var names: Array[String] = []
	var training_names: Dictionary = {
		ClassProficiencySystem.SIMPLE_WEAPONS: "простое оружие",
		ClassProficiencySystem.MARTIAL_WEAPONS: "воинское оружие",
		ClassProficiencySystem.MARTIAL_LIGHT_WEAPONS: "лёгкое воинское оружие",
		ClassProficiencySystem.MARTIAL_FINESSE_OR_LIGHT_WEAPONS: "фехтовальное или лёгкое воинское оружие"
	}
	if value is Array:
		for item: Variant in value:
			var training_id: String = str(item)
			names.append(str(training_names.get(training_id, training_id)))
	return ", ".join(names) if not names.is_empty() else "нет"


func _display_armor_training(value: Variant) -> String:
	var names: Array[String] = []
	var training_names: Dictionary = {
		"light": "лёгкие доспехи",
		"medium": "средние доспехи",
		"heavy": "тяжёлые доспехи",
		"shield": "щиты"
	}
	if value is Array:
		for item: Variant in value:
			var training_id: String = str(item)
			names.append(str(training_names.get(training_id, training_id)))
	return ", ".join(names) if not names.is_empty() else "нет"


func _display_language_ids(language_ids: Array[String]) -> String:
	var names: Array[String] = []
	for language_id: String in language_ids:
		for language: Dictionary in _languages:
			if str(language.get("id", "")) == language_id:
				names.append(str(language.get("name", language_id)))
				break
	return ", ".join(names)


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
