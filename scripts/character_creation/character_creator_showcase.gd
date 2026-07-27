extends "res://scripts/character_creation/character_creator_customized.gd"

const CLASS_SELECTION_PATH: String = "res://data/ui/class_selection.json"
const ABILITY_SCORE_CAP: int = 20

var _class_selection_ui: Dictionary = {}


func _ready() -> void:
	_load_class_selection_ui()
	super._ready()


func _build_race_step() -> void:
	if _races.is_empty():
		_add_paragraph("Не удалось загрузить список рас.", Color(1.0, 0.4, 0.4, 1.0))
		return
	var selected_race: Dictionary = _get_selected_race()
	if selected_race.is_empty():
		return
	var accent: Color = Color.from_string(str(selected_race.get("color_hex", PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX)), Color.WHITE)
	var showcase: PanelContainer = PanelContainer.new()
	showcase.name = "RaceShowcase"
	showcase.custom_minimum_size = Vector2(0.0, 330.0)
	showcase.add_theme_stylebox_override("panel", _make_showcase_panel_style(accent))
	_content_container.add_child(showcase)
	var margin: MarginContainer = _make_margin(26, 22, 26, 22)
	showcase.add_child(margin)
	var row: HBoxContainer = HBoxContainer.new()
	row.add_theme_constant_override("separation", 24)
	margin.add_child(row)
	row.add_child(_make_emblem(str(selected_race.get("selection_symbol", "??")), accent))
	var details: VBoxContainer = VBoxContainer.new()
	details.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	details.add_theme_constant_override("separation", 10)
	row.add_child(details)
	details.add_child(_make_label(str(selected_race.get("name", "Раса")), 34, Color.WHITE))
	var description: Label = _make_label(str(selected_race.get("description", "")), 18, Color(0.84, 0.88, 0.94, 1.0))
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	details.add_child(description)
	details.add_child(_make_label("Расовые характеристики: %s" % str(selected_race.get("ability_bonus_description", "без бонусов")), 20, accent.lightened(0.28)))
	var trait_list: VBoxContainer = VBoxContainer.new()
	trait_list.add_theme_constant_override("separation", 5)
	details.add_child(trait_list)
	var traits_value: Variant = selected_race.get("traits", [])
	if traits_value is Array:
		var shown: int = 0
		for trait_value: Variant in traits_value:
			if trait_value is Dictionary and shown < 3:
				var trait_data: Dictionary = trait_value as Dictionary
				var line: Label = _make_label("• %s — %s" % [str(trait_data.get("name", "Особенность")), str(trait_data.get("description", ""))], 16, Color(0.78, 0.83, 0.9, 1.0))
				line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				trait_list.add_child(line)
				shown += 1
	var stats: VBoxContainer = VBoxContainer.new()
	stats.custom_minimum_size = Vector2(245.0, 0.0)
	stats.add_theme_constant_override("separation", 12)
	row.add_child(stats)
	stats.add_child(_make_stat_block("РАЗМЕР", "Маленький" if str(selected_race.get("size", "medium")) == "small" else "Средний"))
	stats.add_child(_make_stat_block("СКОРОСТЬ", "%d футов" % int(selected_race.get("speed_ft", 30))))
	stats.add_child(_make_stat_block("ТЁМНОЕ ЗРЕНИЕ", "Нет" if int(selected_race.get("darkvision_ft", 0)) <= 0 else "%d футов" % int(selected_race.get("darkvision_ft", 0))))
	stats.add_child(_make_stat_block("БОНУСЫ", str(selected_race.get("ability_bonus_description", "Нет"))))
	_add_showcase_caption("Выберите расу в ленте ниже. Бонусы применятся один раз к распределённым характеристикам и не будут повторно начисляться при загрузке.")
	var carousel: ScrollContainer = ScrollContainer.new()
	carousel.name = "RaceCarousel"
	carousel.custom_minimum_size = Vector2(0.0, 112.0)
	carousel.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	carousel.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_content_container.add_child(carousel)
	var strip: HBoxContainer = HBoxContainer.new()
	strip.add_theme_constant_override("separation", 12)
	carousel.add_child(strip)
	for race_data: Dictionary in _races:
		var race_id: String = str(race_data.get("id", "human"))
		var race_accent: Color = Color.from_string(str(race_data.get("color_hex", PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX)), Color.WHITE)
		strip.add_child(_make_selector_card(
			str(race_data.get("selection_symbol", "??")),
			str(race_data.get("name", race_id)),
			str(race_data.get("ability_bonus_description", "")),
			race_accent,
			race_id == _selected_race_id,
			_select_race.bind(race_id)
		))


func _build_class_step() -> void:
	if _classes.is_empty():
		_add_paragraph("Не удалось загрузить список классов.", Color(1.0, 0.4, 0.4, 1.0))
		return
	if _selected_class_id.is_empty():
		_selected_class_id = "fighter" if not _find_class("fighter").is_empty() else str(_classes[0].get("id", ""))
	var selected_class: Dictionary = _get_selected_class()
	if selected_class.is_empty():
		return
	var ui_data: Dictionary = _class_ui(_selected_class_id)
	var accent: Color = Color.from_string(str(ui_data.get("accent", "#66778B")), Color.WHITE)
	var showcase: PanelContainer = PanelContainer.new()
	showcase.name = "ClassShowcase"
	showcase.custom_minimum_size = Vector2(0.0, 330.0)
	showcase.add_theme_stylebox_override("panel", _make_showcase_panel_style(accent))
	_content_container.add_child(showcase)
	var margin: MarginContainer = _make_margin(26, 22, 26, 22)
	showcase.add_child(margin)
	var row: HBoxContainer = HBoxContainer.new()
	row.add_theme_constant_override("separation", 24)
	margin.add_child(row)
	row.add_child(_make_emblem(str(ui_data.get("symbol", "??")), accent))
	var details: VBoxContainer = VBoxContainer.new()
	details.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	details.add_theme_constant_override("separation", 10)
	row.add_child(details)
	details.add_child(_make_label(str(selected_class.get("name", "Класс")), 34, Color.WHITE))
	details.add_child(_make_label(str(selected_class.get("role", "")), 20, accent.lightened(0.30)))
	var description: Label = _make_label(str(selected_class.get("description", "")), 18, Color(0.84, 0.88, 0.94, 1.0))
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	details.add_child(description)
	var tags: HBoxContainer = HBoxContainer.new()
	tags.add_theme_constant_override("separation", 8)
	details.add_child(tags)
	var tags_value: Variant = ui_data.get("tags", [])
	if tags_value is Array:
		for tag_value: Variant in tags_value:
			tags.add_child(_make_tag(str(tag_value), accent))
	var primary_names: Array[String] = []
	var primary_value: Variant = selected_class.get("primary_abilities", [])
	if primary_value is Array:
		for ability_value: Variant in primary_value:
			primary_names.append(str(ABILITY_NAMES.get(str(ability_value), ability_value)))
	details.add_child(_make_label("Ключевые характеристики: %s" % ", ".join(primary_names), 18, Color(0.78, 0.83, 0.9, 1.0)))
	var stats: VBoxContainer = VBoxContainer.new()
	stats.custom_minimum_size = Vector2(245.0, 0.0)
	stats.add_theme_constant_override("separation", 12)
	row.add_child(stats)
	stats.add_child(_make_stat_block("КОСТЬ ЗДОРОВЬЯ", "d%d" % int(selected_class.get("hit_die", 8))))
	stats.add_child(_make_stat_block("ЗДОРОВЬЕ НА СТАРТЕ", str(_calculate_starting_health(selected_class) + int(_get_selected_race().get("hp_bonus_per_level", 0)))))
	stats.add_child(_make_stat_block("СЛОЖНОСТЬ", _difficulty_text(int(ui_data.get("difficulty", 2)))))
	stats.add_child(_make_stat_block("ЛУЧШАЯ ОСНОВНАЯ", str(_best_primary_score(selected_class))))
	_add_showcase_caption("Лента классов использует единый стиль с выбором расы. Итоговые значения уже включают бонусы происхождения.")
	var carousel: ScrollContainer = ScrollContainer.new()
	carousel.name = "ClassCarousel"
	carousel.custom_minimum_size = Vector2(0.0, 112.0)
	carousel.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	carousel.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_content_container.add_child(carousel)
	var strip: HBoxContainer = HBoxContainer.new()
	strip.add_theme_constant_override("separation", 12)
	carousel.add_child(strip)
	for class_data: Dictionary in _classes:
		var class_id: String = str(class_data.get("id", ""))
		var class_ui: Dictionary = _class_ui(class_id)
		var class_accent: Color = Color.from_string(str(class_ui.get("accent", "#66778B")), Color.WHITE)
		strip.add_child(_make_selector_card(
			str(class_ui.get("symbol", "??")),
			str(class_data.get("name", class_id)),
			str(class_data.get("role", "")),
			class_accent,
			class_id == _selected_class_id,
			_select_class.bind(class_id)
		))
	_append_class_proficiency_controls()


func _build_confirmation_step() -> void:
	var selected_class: Dictionary = _get_selected_class()
	var selected_race: Dictionary = _get_selected_race()
	var selected_background: Dictionary = _get_selected_background()
	_ensure_class_skill_selection()
	var accent: Color = Color.from_string(str(selected_race.get("color_hex", PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX)), Color.WHITE)
	var summary_panel: PanelContainer = PanelContainer.new()
	summary_panel.add_theme_stylebox_override("panel", _make_showcase_panel_style(accent))
	_content_container.add_child(summary_panel)
	var margin: MarginContainer = _make_margin(26, 22, 26, 22)
	summary_panel.add_child(margin)
	var summary: VBoxContainer = VBoxContainer.new()
	summary.add_theme_constant_override("separation", 10)
	margin.add_child(summary)
	summary.add_child(_make_label(_character_name, 32, Color.WHITE))
	summary.add_child(_make_label("%s · %s · уровень 1" % [str(selected_race.get("name", "Раса")), str(selected_class.get("name", "Класс"))], 21, accent.lightened(0.28)))
	summary.add_child(_make_label("Происхождение: %s · черта: %s" % [
		str(selected_background.get("name", "Не выбрано")),
		str(selected_background.get("origin_feat_name", "—"))
	], 18))
	var health: int = _calculate_starting_health(selected_class) + int(selected_race.get("hp_bonus_per_level", 0))
	summary.add_child(_make_label("Здоровье: %d · скорость: %d футов" % [health, int(selected_race.get("speed_ft", 30))], 20))
	summary.add_child(_make_label("Навыки происхождения: %s" % _display_skill_ids(selected_background.get("skill_proficiencies", [])), 18))
	_append_class_training_summary(summary, selected_class)
	summary.add_child(_make_label("Языки: Общий, %s" % _display_language_ids(_selected_languages), 18))
	var abilities_grid: GridContainer = GridContainer.new()
	abilities_grid.columns = 4
	abilities_grid.add_theme_constant_override("h_separation", 16)
	abilities_grid.add_theme_constant_override("v_separation", 9)
	summary.add_child(abilities_grid)
	for ability_id: String in ABILITY_IDS:
		var base_score: int = _score_for_ability(ability_id)
		var bonus: int = int(_background_ability_bonuses.get(ability_id, 0))
		var final_score: int = _final_score_for_ability(ability_id)
		abilities_grid.add_child(_make_label(str(ABILITY_NAMES[ability_id]), 17))
		abilities_grid.add_child(_make_label(str(base_score), 18, Color(0.72, 0.77, 0.84, 1.0)))
		abilities_grid.add_child(_make_label(("+%d" % bonus) if bonus > 0 else "—", 18, accent.lightened(0.25)))
		abilities_grid.add_child(_make_label("%d (%s)" % [final_score, _format_modifier(PlayerCharacter.modifier_for_score(final_score))], 19, Color.WHITE))
	_add_paragraph("В таблице показаны: базовое распределённое значение, бонус происхождения и итоговая характеристика. Максимум при создании — 20.", Color(0.68, 0.73, 0.82, 1.0))


func _finish_creation() -> void:
	super._finish_creation()


func _calculate_starting_health(class_data: Dictionary) -> int:
	if class_data.is_empty():
		return 1
	var hit_die: int = int(class_data.get("hit_die", 8))
	var constitution_modifier: int = PlayerCharacter.modifier_for_score(_final_score_for_ability("constitution"))
	return maxi(hit_die + constitution_modifier, 1)


func _best_primary_score(class_data: Dictionary) -> int:
	var best_score: int = 0
	var primary_value: Variant = class_data.get("primary_abilities", [])
	if primary_value is Array:
		for ability_value: Variant in primary_value:
			best_score = maxi(best_score, _final_score_for_ability(str(ability_value)))
	return best_score


func _final_score_for_ability(ability_id: String) -> int:
	return clampi(_score_with_origin_bonus(ability_id), 1, ABILITY_SCORE_CAP)


func _find_class(class_id: String) -> Dictionary:
	for class_data: Dictionary in _classes:
		if str(class_data.get("id", "")) == class_id:
			return class_data
	return {}


func _class_ui(class_id: String) -> Dictionary:
	var value: Variant = _class_selection_ui.get(class_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func _load_class_selection_ui() -> void:
	_class_selection_ui.clear()
	if not FileAccess.file_exists(CLASS_SELECTION_PATH):
		push_error("Файл оформления классов не найден: %s" % CLASS_SELECTION_PATH)
		return
	var file: FileAccess = FileAccess.open(CLASS_SELECTION_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed is Dictionary:
		var classes_value: Variant = (parsed as Dictionary).get("classes", {})
		if classes_value is Dictionary:
			_class_selection_ui = (classes_value as Dictionary).duplicate(true)


func _make_emblem(symbol: String, accent: Color) -> Control:
	var panel: PanelContainer = PanelContainer.new()
	panel.custom_minimum_size = Vector2(220.0, 245.0)
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = accent.darkened(0.45)
	style.set_corner_radius_all(18)
	style.set_border_width_all(3)
	style.border_color = accent.lightened(0.2)
	panel.add_theme_stylebox_override("panel", style)
	var center: CenterContainer = CenterContainer.new()
	panel.add_child(center)
	var label: Label = _make_label(symbol, 58, Color.WHITE)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	center.add_child(label)
	return panel


func _make_selector_card(symbol: String, title: String, subtitle: String, accent: Color, selected: bool, callback: Callable) -> Button:
	var card: Button = Button.new()
	card.custom_minimum_size = Vector2(180.0, 96.0)
	card.toggle_mode = true
	card.button_pressed = selected
	card.text = "%s\n%s\n%s" % [symbol, title, subtitle]
	card.add_theme_font_size_override("font_size", 15)
	card.add_theme_color_override("font_color", Color.WHITE)
	card.add_theme_color_override("font_hover_color", Color.WHITE)
	card.add_theme_stylebox_override("normal", _make_selector_style(accent, selected, false))
	card.add_theme_stylebox_override("hover", _make_selector_style(accent, selected, true))
	card.add_theme_stylebox_override("pressed", _make_selector_style(accent, true, true))
	card.add_theme_stylebox_override("focus", _make_selector_style(accent, true, true))
	card.pressed.connect(callback)
	return card


func _make_selector_style(accent: Color, selected: bool, hover: bool) -> StyleBoxFlat:
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = accent.darkened(0.42 if not hover else 0.30)
	style.set_corner_radius_all(10)
	style.set_border_width_all(3 if selected else 1)
	style.border_color = accent.lightened(0.28) if selected else Color(1.0, 1.0, 1.0, 0.22)
	style.content_margin_left = 10.0
	style.content_margin_right = 10.0
	style.content_margin_top = 8.0
	style.content_margin_bottom = 8.0
	return style


func _make_showcase_panel_style(accent: Color) -> StyleBoxFlat:
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = Color(0.045, 0.055, 0.078, 0.98)
	style.set_corner_radius_all(16)
	style.set_border_width_all(2)
	style.border_color = accent.darkened(0.05)
	return style


func _make_stat_block(title: String, value: String) -> Control:
	var box: VBoxContainer = VBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	box.add_child(_make_label(title, 13, Color(0.59, 0.65, 0.74, 1.0)))
	var value_label: Label = _make_label(value, 18, Color.WHITE)
	value_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(value_label)
	return box


func _make_tag(text_value: String, accent: Color) -> Control:
	var panel: PanelContainer = PanelContainer.new()
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = accent.darkened(0.48)
	style.set_corner_radius_all(8)
	style.content_margin_left = 9.0
	style.content_margin_right = 9.0
	style.content_margin_top = 5.0
	style.content_margin_bottom = 5.0
	panel.add_theme_stylebox_override("panel", style)
	panel.add_child(_make_label(text_value, 14, Color.WHITE))
	return panel


func _make_margin(left: int, top: int, right: int, bottom: int) -> MarginContainer:
	var margin: MarginContainer = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", left)
	margin.add_theme_constant_override("margin_top", top)
	margin.add_theme_constant_override("margin_right", right)
	margin.add_theme_constant_override("margin_bottom", bottom)
	return margin


func _add_showcase_caption(text_value: String) -> void:
	var label: Label = _make_label(text_value, 16, Color(0.67, 0.72, 0.82, 1.0))
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_content_container.add_child(label)


func _difficulty_text(value: int) -> String:
	match clampi(value, 1, 3):
		1: return "Низкая"
		2: return "Средняя"
		3: return "Высокая"
	return "Средняя"
