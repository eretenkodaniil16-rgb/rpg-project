class_name CharacterSheet
extends Control

signal closed
signal rest_completed(rest_type: String)

const ABILITY_ORDER: Array[String] = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
const ABILITY_NAMES: Dictionary = {
	"strength":"Сила", "dexterity":"Ловкость", "constitution":"Телосложение",
	"intelligence":"Интеллект", "wisdom":"Мудрость", "charisma":"Харизма"
}
const SKILL_NAMES: Dictionary = {
	"acrobatics":"Акробатика", "animal_handling":"Уход за животными", "arcana":"Магия",
	"athletics":"Атлетика", "deception":"Обман", "history":"История",
	"insight":"Проницательность", "intimidation":"Запугивание", "investigation":"Анализ",
	"medicine":"Медицина", "nature":"Природа", "perception":"Восприятие",
	"performance":"Выступление", "persuasion":"Убеждение", "religion":"Религия",
	"sleight_of_hand":"Ловкость рук", "stealth":"Скрытность", "survival":"Выживание"
}

var _class_data: ClassDataSystem = ClassDataSystem.new()
var _character: PlayerCharacter
var _identity: Label
var _summary: Label
var _swatch: ColorRect
var _grid: GridContainer
var _equipment_label: Label
var _features_box: VBoxContainer
var _rest_result: Label
var _short_rest_button: Button
var _long_rest_button: Button
var _grid_toggle_button: Button
var _close_button: Button


func _ready() -> void:
	_build_ui()
	hide()


func open_sheet(character: PlayerCharacter) -> void:
	_character = character
	_rest_result.text = "Короткий отдых длится 1 час; долгий — 8 часов."
	_refresh()
	_sync_grid_toggle()
	var state: Node = _game_state()
	if state != null:
		state.set("input_locked", true)
	show()
	_close_button.grab_focus()


func close_sheet() -> void:
	if not visible:
		return
	hide()
	var state: Node = _game_state()
	if state != null:
		state.set("input_locked", false)
	closed.emit()


func _unhandled_input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		close_sheet()
		get_viewport().set_input_as_handled()


func _build_ui() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var dimmer := ColorRect.new()
	dimmer.color = Color(0, 0, 0, 0.72)
	dimmer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dimmer)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side: String in ["left", "right"]:
		margin.add_theme_constant_override("margin_" + side, 70)
	for side: String in ["top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 42)
	add_child(margin)
	var panel := PanelContainer.new()
	margin.add_child(panel)
	var pad := MarginContainer.new()
	for side: String in ["left", "right", "top", "bottom"]:
		pad.add_theme_constant_override("margin_" + side, 28)
	panel.add_child(pad)
	var page := VBoxContainer.new()
	page.add_theme_constant_override("separation", 14)
	pad.add_child(page)
	var header := HBoxContainer.new()
	page.add_child(header)
	var title := Label.new()
	title.text = "ЛИСТ ПЕРСОНАЖА"
	title.add_theme_font_size_override("font_size", 30)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	_close_button = Button.new()
	_close_button.text = "ЗАКРЫТЬ"
	_close_button.custom_minimum_size = Vector2(170, 56)
	_close_button.pressed.connect(close_sheet)
	header.add_child(_close_button)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	page.add_child(scroll)
	var content := VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 14)
	scroll.add_child(content)
	_identity = Label.new()
	_identity.name = "IdentityLabel"
	_identity.add_theme_font_size_override("font_size", 26)
	content.add_child(_identity)
	var summary_row := HBoxContainer.new()
	content.add_child(summary_row)
	_summary = Label.new()
	_summary.name = "SummaryLabel"
	_summary.add_theme_font_size_override("font_size", 20)
	_summary.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	summary_row.add_child(_summary)
	var color_caption := Label.new()
	color_caption.text = "Цвет:"
	summary_row.add_child(color_caption)
	_swatch = ColorRect.new()
	_swatch.name = "ColorSwatch"
	_swatch.custom_minimum_size = Vector2(54, 36)
	summary_row.add_child(_swatch)

	var rest_title := Label.new()
	rest_title.text = "ОТДЫХ"
	rest_title.add_theme_font_size_override("font_size", 23)
	content.add_child(rest_title)
	var rest_row := HBoxContainer.new()
	rest_row.add_theme_constant_override("separation", 12)
	content.add_child(rest_row)
	_short_rest_button = Button.new()
	_short_rest_button.text = "КОРОТКИЙ ОТДЫХ · ДО 1 КОСТИ ХИТОВ"
	_short_rest_button.custom_minimum_size = Vector2(390, 54)
	_short_rest_button.pressed.connect(_on_short_rest_pressed)
	rest_row.add_child(_short_rest_button)
	_long_rest_button = Button.new()
	_long_rest_button.text = "ДОЛГИЙ ОТДЫХ · 8 ЧАСОВ"
	_long_rest_button.custom_minimum_size = Vector2(330, 54)
	_long_rest_button.pressed.connect(_on_long_rest_pressed)
	rest_row.add_child(_long_rest_button)
	_rest_result = Label.new()
	_rest_result.name = "RestResultLabel"
	_rest_result.add_theme_font_size_override("font_size", 18)
	_rest_result.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content.add_child(_rest_result)

	var field_title := Label.new()
	field_title.text = "ПОЛЕ БОЯ"
	field_title.add_theme_font_size_override("font_size", 23)
	content.add_child(field_title)
	_grid_toggle_button = Button.new()
	_grid_toggle_button.name = "GridToggleButton"
	_grid_toggle_button.custom_minimum_size = Vector2(430, 54)
	_grid_toggle_button.add_theme_font_size_override("font_size", 18)
	_grid_toggle_button.pressed.connect(_on_grid_toggle_pressed)
	content.add_child(_grid_toggle_button)

	var abilities_title := Label.new()
	abilities_title.text = "ХАРАКТЕРИСТИКИ"
	abilities_title.add_theme_font_size_override("font_size", 23)
	content.add_child(abilities_title)
	_grid = GridContainer.new()
	_grid.name = "AbilitiesGrid"
	_grid.columns = 3
	content.add_child(_grid)
	var equipment_title := Label.new()
	equipment_title.text = "ЭКИПИРОВКА"
	equipment_title.add_theme_font_size_override("font_size", 23)
	content.add_child(equipment_title)
	_equipment_label = Label.new()
	_equipment_label.name = "EquipmentLabel"
	_equipment_label.add_theme_font_size_override("font_size", 19)
	_equipment_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content.add_child(_equipment_label)
	var features_title := Label.new()
	features_title.text = "КЛАССОВЫЕ ОСОБЕННОСТИ"
	features_title.add_theme_font_size_override("font_size", 23)
	content.add_child(features_title)
	_features_box = VBoxContainer.new()
	_features_box.name = "FeaturesBox"
	_features_box.add_theme_constant_override("separation", 8)
	content.add_child(_features_box)


func _refresh() -> void:
	if _character == null:
		return
	_identity.text = "%s — %s, уровень %d" % [_character.character_name, _character.character_class_name, _character.level]
	_summary.text = "Здоровье: %d / %d     КД: %d     Кости Хитов: %d / %d (d%d)     Опыт: %d" % [
		_character.current_health, _character.maximum_health, _class_data.get_armor_class(_character),
		_character.hit_dice_current, _character.hit_dice_maximum, _character.hit_die_size, _character.experience
	]
	_short_rest_button.disabled = _character.current_health <= 0
	_long_rest_button.disabled = _character.current_health <= 0
	_swatch.color = Color.from_string(_character.appearance_color_hex, Color(0.3, 0.64, 0.91, 1))
	for child: Node in _grid.get_children():
		child.queue_free()
	for ability_id: String in ABILITY_ORDER:
		_add_cell(str(ABILITY_NAMES[ability_id]), HORIZONTAL_ALIGNMENT_LEFT)
		_add_cell(str(_character.get_ability_score(ability_id)), HORIZONTAL_ALIGNMENT_CENTER)
		_add_cell(_format_modifier(_character.get_ability_modifier(ability_id)), HORIZONTAL_ALIGNMENT_CENTER)
	var state: Node = _game_state()
	var weapon: Dictionary = state.call("get_item_definition", _character.equipped_weapon_id) as Dictionary if state != null else {}
	var armor: Dictionary = state.call("get_item_definition", _character.equipped_armor_id) as Dictionary if state != null else {}
	var shield: Dictionary = state.call("get_item_definition", _character.equipped_shield_id) as Dictionary if state != null else {}
	var equipment_lines: Array[String] = [
		"Оружие: %s" % str(weapon.get("name", "Без оружия")),
		"Доспех: %s" % str(armor.get("name", "Нет")),
		"Щит: %s" % str(shield.get("name", "Нет")),
		"Навыки класса: %s" % _display_skill_ids(_character.class_skill_proficiencies)
	]
	if not weapon.is_empty() and not _character.is_proficient_with_weapon_definition(weapon):
		equipment_lines.append("⚠ Нет владения оружием: бонус мастерства к атаке не действует.")
	var training_state: Dictionary = _class_data.get_equipment_training_state(_character)
	if bool(training_state.get("untrained_armor", false)):
		equipment_lines.append("⚠ Нет обучения доспеху: помеха тестам Силы/Ловкости и запрет колдовства.")
	if bool(training_state.get("untrained_shield", false)):
		equipment_lines.append("⚠ Нет обучения щиту: его бонус КД не действует.")
	_equipment_label.text = "\n".join(equipment_lines)
	for child: Node in _features_box.get_children():
		child.queue_free()
	for feature_value: Variant in _class_data.get_feature_views(_character):
		if not feature_value is Dictionary:
			continue
		var feature: Dictionary = feature_value as Dictionary
		var label := Label.new()
		var resource_text: String = ""
		if str(feature.get("id", "")) == _character.signature_ability_id:
			resource_text = " [%s]" % _class_data.get_resource_text(_character, feature)
		label.text = "• %s%s — %s" % [str(feature.get("name", "Особенность")), resource_text, str(feature.get("description", ""))]
		label.add_theme_font_size_override("font_size", 18)
		label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_features_box.add_child(label)
	_sync_grid_toggle()


func _on_short_rest_pressed() -> void:
	var result: Dictionary = _class_data.short_rest(_character)
	_rest_result.text = str(result.get("message", "Короткий отдых завершён."))
	_rest_result.add_theme_color_override("font_color", Color(0.64, 0.94, 0.68, 1.0) if bool(result.get("success", false)) else Color(1.0, 0.55, 0.48, 1.0))
	_refresh()
	if bool(result.get("success", false)):
		rest_completed.emit("short")


func _on_long_rest_pressed() -> void:
	var result: Dictionary = _class_data.long_rest(_character)
	_rest_result.text = str(result.get("message", "Долгий отдых завершён."))
	_rest_result.add_theme_color_override("font_color", Color(0.64, 0.94, 0.68, 1.0) if bool(result.get("success", false)) else Color(1.0, 0.55, 0.48, 1.0))
	_refresh()
	if bool(result.get("success", false)):
		rest_completed.emit("long")


func _on_grid_toggle_pressed() -> void:
	var battle_grid: Node = get_tree().get_first_node_in_group("battle_grid")
	if battle_grid == null or not battle_grid.has_method("set_grid_enabled") or not battle_grid.has_method("is_grid_enabled"):
		_sync_grid_toggle()
		return
	var next_value: bool = not bool(battle_grid.call("is_grid_enabled"))
	battle_grid.call("set_grid_enabled", next_value)
	_sync_grid_toggle()


func _sync_grid_toggle() -> void:
	if _grid_toggle_button == null:
		return
	var battle_grid: Node = get_tree().get_first_node_in_group("battle_grid")
	var available: bool = battle_grid != null and battle_grid.has_method("is_grid_enabled")
	_grid_toggle_button.disabled = not available
	if not available:
		_grid_toggle_button.text = "СЕТКА НЕДОСТУПНА"
		return
	var enabled: bool = bool(battle_grid.call("is_grid_enabled"))
	_grid_toggle_button.text = "СЕТКА: %s · 1 КЛЕТКА = 5 ФУТОВ" % ("ВКЛ" if enabled else "ВЫКЛ")


func _game_state() -> Node:
	var tree: SceneTree = get_tree()
	return tree.root.get_node_or_null("GameState") if tree != null else null


func _add_cell(text_value: String, alignment: HorizontalAlignment) -> void:
	var label := Label.new()
	label.text = text_value
	label.horizontal_alignment = alignment
	label.custom_minimum_size = Vector2(180 if alignment == HORIZONTAL_ALIGNMENT_LEFT else 100, 44)
	label.add_theme_font_size_override("font_size", 20)
	_grid.add_child(label)


func _display_skill_ids(skill_ids: Array[String]) -> String:
	var names: Array[String] = []
	for skill_id: String in skill_ids:
		names.append(str(SKILL_NAMES.get(skill_id, skill_id)))
	return ", ".join(names) if not names.is_empty() else "нет"


func _format_modifier(value: int) -> String:
	return "+%d" % value if value >= 0 else str(value)
