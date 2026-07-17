extends Control

const MAIN_MENU_SCENE: String = "res://scenes/menus/main_menu.tscn"
const GAME_SCENE: String = "res://scenes/game/game.tscn"
const CLASSES_PATH: String = "res://data/classes/classes.json"

const ABILITY_IDS: Array[String] = [
	"strength",
	"dexterity",
	"constitution",
	"intelligence",
	"charisma",
	"wisdom"
]
const ABILITY_NAMES: Dictionary = {
	"strength": "Сила",
	"dexterity": "Ловкость",
	"constitution": "Телосложение",
	"intelligence": "Интеллект",
	"charisma": "Харизма",
	"wisdom": "Мудрость"
}
const STEP_TITLES: Array[String] = [
	"Имя героя",
	"Броски характеристик",
	"Распределение значений",
	"Выбор класса",
	"Подтверждение"
]

var _dice_roller: DiceRoller = DiceRoller.new()
var _current_step: int = 0
var _character_name: String = ""
var _rolls: Array[Dictionary] = []
var _scores: Array[int] = []
var _assignments: Dictionary = {}
var _selected_score_index: int = -1
var _classes: Array[Dictionary] = []
var _selected_class_id: String = ""

var _title_label: Label
var _progress_label: Label
var _message_label: Label
var _content_container: VBoxContainer
var _back_button: Button
var _next_button: Button


func _ready() -> void:
	_load_classes()
	_build_layout()
	_show_step(0)


func _build_layout() -> void:
	var background: ColorRect = ColorRect.new()
	background.color = Color(0.035, 0.045, 0.065, 1.0)
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)

	var page_margin: MarginContainer = MarginContainer.new()
	page_margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	page_margin.add_theme_constant_override("margin_left", 48)
	page_margin.add_theme_constant_override("margin_top", 28)
	page_margin.add_theme_constant_override("margin_right", 48)
	page_margin.add_theme_constant_override("margin_bottom", 28)
	add_child(page_margin)

	var page: VBoxContainer = VBoxContainer.new()
	page.add_theme_constant_override("separation", 14)
	page_margin.add_child(page)

	var header: HBoxContainer = HBoxContainer.new()
	header.add_theme_constant_override("separation", 16)
	page.add_child(header)

	var heading_box: VBoxContainer = VBoxContainer.new()
	heading_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(heading_box)

	_title_label = _make_label("", 30)
	heading_box.add_child(_title_label)

	_progress_label = _make_label("", 16, Color(0.67, 0.72, 0.82, 1.0))
	heading_box.add_child(_progress_label)

	var cancel_button: Button = _make_button("В главное меню", 180.0)
	cancel_button.pressed.connect(_return_to_menu)
	header.add_child(cancel_button)

	var separator: HSeparator = HSeparator.new()
	page.add_child(separator)

	var scroll: ScrollContainer = ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	page.add_child(scroll)

	_content_container = VBoxContainer.new()
	_content_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_content_container.add_theme_constant_override("separation", 14)
	scroll.add_child(_content_container)

	_message_label = _make_label("", 16, Color(1.0, 0.72, 0.45, 1.0))
	_message_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	page.add_child(_message_label)

	var footer: HBoxContainer = HBoxContainer.new()
	footer.alignment = BoxContainer.ALIGNMENT_END
	footer.add_theme_constant_override("separation", 12)
	page.add_child(footer)

	_back_button = _make_button("Назад", 160.0)
	_back_button.pressed.connect(_on_back_pressed)
	footer.add_child(_back_button)

	_next_button = _make_button("Продолжить", 220.0)
	_next_button.pressed.connect(_on_next_pressed)
	footer.add_child(_next_button)


func _show_step(step_index: int) -> void:
	_current_step = clampi(step_index, 0, STEP_TITLES.size() - 1)
	_clear_content()
	_message_label.text = ""
	_title_label.text = STEP_TITLES[_current_step]
	_progress_label.text = "Шаг %d из %d" % [_current_step + 1, STEP_TITLES.size()]

	match _current_step:
		0:
			_build_name_step()
		1:
			_build_roll_step()
		2:
			_build_assignment_step()
		3:
			_build_class_step()
		4:
			_build_confirmation_step()

	_update_navigation()


func _build_name_step() -> void:
	_add_paragraph("Введите имя персонажа. Раса пока не выбирается и не влияет на характеристики.")

	var name_label: Label = _make_label("Имя", 20)
	_content_container.add_child(name_label)

	var name_input: LineEdit = LineEdit.new()
	name_input.custom_minimum_size = Vector2(0.0, 58.0)
	name_input.placeholder_text = "От 2 до 20 символов"
	name_input.max_length = 20
	name_input.text = _character_name
	name_input.add_theme_font_size_override("font_size", 22)
	name_input.text_changed.connect(_on_name_changed)
	_content_container.add_child(name_input)
	name_input.grab_focus()

	_add_paragraph("Имя будет отображаться в сохранении, интерфейсе и диалогах.", Color(0.68, 0.73, 0.82, 1.0))


func _build_roll_step() -> void:
	_add_paragraph("Для каждого значения бросаются четыре шестигранных кубика. Минимальный кубик отбрасывается, остальные три складываются.")

	var counter: Label = _make_label("Получено значений: %d из 6" % _rolls.size(), 21)
	_content_container.add_child(counter)

	for index: int in range(_rolls.size()):
		var roll_data: Dictionary = _rolls[index]
		var roll_panel: PanelContainer = PanelContainer.new()
		_content_container.add_child(roll_panel)

		var row: HBoxContainer = HBoxContainer.new()
		row.add_theme_constant_override("separation", 16)
		roll_panel.add_child(row)

		var number_label: Label = _make_label("%d." % (index + 1), 20)
		number_label.custom_minimum_size = Vector2(42.0, 0.0)
		row.add_child(number_label)

		var dice_label: Label = _make_label(_format_roll(roll_data), 19)
		dice_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(dice_label)

		var total_label: Label = _make_label(str(int(roll_data.get("total", 0))), 26, Color(1.0, 0.82, 0.38, 1.0))
		total_label.custom_minimum_size = Vector2(70.0, 0.0)
		total_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		row.add_child(total_label)

	if _rolls.size() < 6:
		var roll_button: Button = _make_button("Бросить 4d6 — значение %d" % (_rolls.size() + 1), 330.0)
		roll_button.pressed.connect(_roll_next_ability_score)
		_content_container.add_child(roll_button)
	else:
		_add_paragraph("Набор готов: %s" % _join_ints(_scores), Color(0.63, 0.88, 0.67, 1.0))
		var reroll_button: Button = _make_button("Перебросить весь набор", 300.0)
		reroll_button.pressed.connect(_reset_rolls)
		_content_container.add_child(reroll_button)


func _build_assignment_step() -> void:
	_add_paragraph("Сначала нажмите на свободное значение, затем на характеристику. Уже назначенное значение можно нажать ещё раз, чтобы заменить или вернуть.")

	var values_title: Label = _make_label("Свободные значения", 20)
	_content_container.add_child(values_title)

	var score_row: HBoxContainer = HBoxContainer.new()
	score_row.add_theme_constant_override("separation", 10)
	_content_container.add_child(score_row)

	for index: int in range(_scores.size()):
		var score_button: Button = _make_button(str(_scores[index]), 90.0)
		score_button.toggle_mode = true
		score_button.button_pressed = index == _selected_score_index
		score_button.disabled = _is_score_assigned(index)
		score_button.pressed.connect(_on_score_pressed.bind(index))
		score_row.add_child(score_button)

	var assignment_panel: PanelContainer = PanelContainer.new()
	_content_container.add_child(assignment_panel)

	var grid: GridContainer = GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 16)
	grid.add_theme_constant_override("v_separation", 10)
	assignment_panel.add_child(grid)

	for ability_id: String in ABILITY_IDS:
		var ability_label: Label = _make_label(str(ABILITY_NAMES[ability_id]), 19)
		ability_label.custom_minimum_size = Vector2(210.0, 48.0)
		grid.add_child(ability_label)

		var value_text: String = "Назначить"
		var modifier_text: String = "—"
		if _assignments.has(ability_id):
			var score_index: int = int(_assignments[ability_id])
			var score: int = _scores[score_index]
			value_text = str(score)
			modifier_text = _format_modifier(PlayerCharacter.modifier_for_score(score))

		var assign_button: Button = _make_button(value_text, 155.0)
		assign_button.pressed.connect(_on_ability_pressed.bind(ability_id))
		grid.add_child(assign_button)

		var modifier_label: Label = _make_label(modifier_text, 20, Color(0.72, 0.82, 1.0, 1.0))
		modifier_label.custom_minimum_size = Vector2(90.0, 0.0)
		modifier_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		grid.add_child(modifier_label)

	_add_paragraph("Назначено: %d из 6" % _assignments.size(), Color(0.68, 0.73, 0.82, 1.0))


func _build_class_step() -> void:
	_add_paragraph("Выберите один класс. Низкая основная характеристика не блокирует выбор, но уменьшит эффективность будущих способностей.")

	if _classes.is_empty():
		_add_paragraph("Не удалось загрузить список классов.", Color(1.0, 0.4, 0.4, 1.0))
		return

	var class_grid: GridContainer = GridContainer.new()
	class_grid.columns = 2
	class_grid.add_theme_constant_override("h_separation", 12)
	class_grid.add_theme_constant_override("v_separation", 12)
	_content_container.add_child(class_grid)

	for class_data: Dictionary in _classes:
		var class_id: String = str(class_data.get("id", ""))
		var class_name_text: String = str(class_data.get("name", class_id))
		var role: String = str(class_data.get("role", ""))
		var hit_die: int = int(class_data.get("hit_die", 8))
		var card: Button = Button.new()
		card.custom_minimum_size = Vector2(0.0, 94.0)
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.toggle_mode = true
		card.button_pressed = class_id == _selected_class_id
		card.text = "%s\n%s · кость здоровья d%d" % [class_name_text, role, hit_die]
		card.add_theme_font_size_override("font_size", 17)
		card.pressed.connect(_select_class.bind(class_id))
		class_grid.add_child(card)

	var selected_class: Dictionary = _get_selected_class()
	if not selected_class.is_empty():
		var details: PanelContainer = PanelContainer.new()
		_content_container.add_child(details)

		var details_margin: MarginContainer = MarginContainer.new()
		details_margin.add_theme_constant_override("margin_left", 20)
		details_margin.add_theme_constant_override("margin_top", 16)
		details_margin.add_theme_constant_override("margin_right", 20)
		details_margin.add_theme_constant_override("margin_bottom", 16)
		details.add_child(details_margin)

		var details_box: VBoxContainer = VBoxContainer.new()
		details_box.add_theme_constant_override("separation", 8)
		details_margin.add_child(details_box)

		details_box.add_child(_make_label(str(selected_class.get("name", "")), 25, Color(1.0, 0.82, 0.38, 1.0)))
		var description_label: Label = _make_label(str(selected_class.get("description", "")), 17)
		description_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		details_box.add_child(description_label)

		var primary_names: Array[String] = []
		var primary_abilities: Variant = selected_class.get("primary_abilities", [])
		if primary_abilities is Array:
			for ability_value: Variant in primary_abilities:
				primary_names.append(str(ABILITY_NAMES.get(str(ability_value), ability_value)))
		details_box.add_child(_make_label("Основные характеристики: %s" % ", ".join(primary_names), 18))

		var starting_health: int = _calculate_starting_health(selected_class)
		details_box.add_child(_make_label("Начальное здоровье: %d" % starting_health, 18))

		var best_primary_score: int = _best_primary_score(selected_class)
		var recommendation_color: Color = Color(0.63, 0.88, 0.67, 1.0) if best_primary_score >= 14 else Color(1.0, 0.68, 0.38, 1.0)
		var recommendation: String = "Характеристики хорошо подходят классу." if best_primary_score >= 14 else "Основная характеристика ниже 14 — класс будет сложнее в развитии."
		details_box.add_child(_make_label(recommendation, 17, recommendation_color))


func _build_confirmation_step() -> void:
	var selected_class: Dictionary = _get_selected_class()
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
	summary.add_child(_make_label("Класс: %s · уровень 1" % str(selected_class.get("name", "Не выбран")), 21))
	summary.add_child(_make_label("Здоровье: %d" % _calculate_starting_health(selected_class), 20))

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

	_add_paragraph("После начала приключения персонаж будет записан в сохранение. Изменение имени, характеристик и класса в первой версии не предусмотрено.", Color(0.68, 0.73, 0.82, 1.0))


func _on_name_changed(new_text: String) -> void:
	_character_name = new_text.strip_edges()
	_message_label.text = "" if _is_name_valid() else "Имя должно содержать от 2 до 20 символов."
	_update_navigation()


func _roll_next_ability_score() -> void:
	if _rolls.size() >= 6:
		return
	var roll_data: Dictionary = _dice_roller.roll_ability_score()
	_rolls.append(roll_data)
	_scores.append(int(roll_data.get("total", 0)))
	_show_step(1)


func _reset_rolls() -> void:
	_rolls.clear()
	_scores.clear()
	_assignments.clear()
	_selected_score_index = -1
	_selected_class_id = ""
	_show_step(1)


func _on_score_pressed(score_index: int) -> void:
	if _is_score_assigned(score_index):
		return
	_selected_score_index = -1 if _selected_score_index == score_index else score_index
	_show_step(2)


func _on_ability_pressed(ability_id: String) -> void:
	if _selected_score_index >= 0:
		var previously_assigned_index: int = -1
		if _assignments.has(ability_id):
			previously_assigned_index = int(_assignments[ability_id])
		_assignments[ability_id] = _selected_score_index
		_selected_score_index = previously_assigned_index
	else:
		if _assignments.has(ability_id):
			_selected_score_index = int(_assignments[ability_id])
			_assignments.erase(ability_id)
	_show_step(2)


func _select_class(class_id: String) -> void:
	_selected_class_id = class_id
	_show_step(3)


func _on_back_pressed() -> void:
	if _current_step <= 0:
		_return_to_menu()
	else:
		_show_step(_current_step - 1)


func _on_next_pressed() -> void:
	if not _can_continue_current_step():
		_message_label.text = _validation_message_for_step()
		return

	if _current_step < STEP_TITLES.size() - 1:
		_show_step(_current_step + 1)
	else:
		_finish_creation()


func _finish_creation() -> void:
	var selected_class: Dictionary = _get_selected_class()
	if selected_class.is_empty():
		_message_label.text = "Выберите класс персонажа."
		return

	var character: PlayerCharacter = PlayerCharacter.new()
	character.character_name = _character_name
	character.character_class_id = _selected_class_id
	character.character_class_name = str(selected_class.get("name", ""))
	for ability_id: String in ABILITY_IDS:
		character.abilities[ability_id] = _score_for_ability(ability_id)
	character.maximum_health = _calculate_starting_health(selected_class)
	character.current_health = character.maximum_health

	GameState.begin_new_game(character)
	if not GameState.save_game():
		_message_label.text = "Не удалось сохранить созданного персонажа."
		return
	get_tree().change_scene_to_file(GAME_SCENE)


func _return_to_menu() -> void:
	get_tree().change_scene_to_file(MAIN_MENU_SCENE)


func _update_navigation() -> void:
	_back_button.text = "В меню" if _current_step == 0 else "Назад"
	_next_button.text = "Начать приключение" if _current_step == STEP_TITLES.size() - 1 else "Продолжить"
	_next_button.disabled = not _can_continue_current_step()


func _can_continue_current_step() -> bool:
	match _current_step:
		0:
			return _is_name_valid()
		1:
			return _rolls.size() == 6
		2:
			return _assignments.size() == ABILITY_IDS.size()
		3:
			return not _selected_class_id.is_empty()
		4:
			return _is_name_valid() and _assignments.size() == ABILITY_IDS.size() and not _selected_class_id.is_empty()
	return false


func _validation_message_for_step() -> String:
	match _current_step:
		0:
			return "Введите имя длиной от 2 до 20 символов."
		1:
			return "Выполните все шесть бросков характеристик."
		2:
			return "Распределите все шесть значений."
		3:
			return "Выберите класс персонажа."
	return "Не все данные заполнены."


func _is_name_valid() -> bool:
	return _character_name.length() >= 2 and _character_name.length() <= 20


func _load_classes() -> void:
	_classes.clear()
	if not FileAccess.file_exists(CLASSES_PATH):
		push_error("Файл классов не найден: %s" % CLASSES_PATH)
		return

	var file: FileAccess = FileAccess.open(CLASSES_PATH, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть файл классов.")
		return

	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Файл классов содержит некорректный JSON.")
		return

	var class_values: Variant = (parsed as Dictionary).get("classes", [])
	if class_values is Array:
		for class_value: Variant in class_values:
			if class_value is Dictionary:
				_classes.append(class_value as Dictionary)


func _get_selected_class() -> Dictionary:
	for class_data: Dictionary in _classes:
		if str(class_data.get("id", "")) == _selected_class_id:
			return class_data
	return {}


func _score_for_ability(ability_id: String) -> int:
	if not _assignments.has(ability_id):
		return 10
	var score_index: int = int(_assignments[ability_id])
	if score_index < 0 or score_index >= _scores.size():
		return 10
	return _scores[score_index]


func _calculate_starting_health(class_data: Dictionary) -> int:
	if class_data.is_empty():
		return 1
	var hit_die: int = int(class_data.get("hit_die", 8))
	var constitution_modifier: int = PlayerCharacter.modifier_for_score(_score_for_ability("constitution"))
	return maxi(hit_die + constitution_modifier, 1)


func _best_primary_score(class_data: Dictionary) -> int:
	var best_score: int = 0
	var primary_abilities: Variant = class_data.get("primary_abilities", [])
	if primary_abilities is Array:
		for ability_value: Variant in primary_abilities:
			best_score = maxi(best_score, _score_for_ability(str(ability_value)))
	return best_score


func _is_score_assigned(score_index: int) -> bool:
	for assigned_value: Variant in _assignments.values():
		if int(assigned_value) == score_index:
			return true
	return false


func _format_roll(roll_data: Dictionary) -> String:
	var dice_value: Variant = roll_data.get("dice", [])
	if not dice_value is Array:
		return "Нет данных"
	var dice: Array = dice_value as Array
	var discarded_index: int = int(roll_data.get("discarded_index", -1))
	var parts: Array[String] = []
	for index: int in range(dice.size()):
		var value_text: String = str(int(dice[index]))
		if index == discarded_index:
			value_text = "[%s отброшен]" % value_text
		parts.append(value_text)
	return " + ".join(parts)


func _format_modifier(modifier: int) -> String:
	return "+%d" % modifier if modifier >= 0 else str(modifier)


func _join_ints(values: Array[int]) -> String:
	var parts: Array[String] = []
	for value: int in values:
		parts.append(str(value))
	return ", ".join(parts)


func _clear_content() -> void:
	for child: Node in _content_container.get_children():
		_content_container.remove_child(child)
		child.queue_free()


func _add_paragraph(text_value: String, color: Color = Color.WHITE) -> void:
	var paragraph: Label = _make_label(text_value, 18, color)
	paragraph.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_content_container.add_child(paragraph)


func _make_label(text_value: String, font_size: int, color: Color = Color.WHITE) -> Label:
	var label: Label = Label.new()
	label.text = text_value
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	return label


func _make_button(text_value: String, minimum_width: float = 0.0) -> Button:
	var button: Button = Button.new()
	button.text = text_value
	button.custom_minimum_size = Vector2(minimum_width, 54.0)
	button.add_theme_font_size_override("font_size", 18)
	return button
