class_name CharacterSheet
extends Control

signal closed

const ABILITY_ORDER: Array[String] = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
const ABILITY_NAMES: Dictionary = {
	"strength":"Сила", "dexterity":"Ловкость", "constitution":"Телосложение",
	"intelligence":"Интеллект", "wisdom":"Мудрость", "charisma":"Харизма"
}

var _class_data: ClassDataSystem = ClassDataSystem.new()
var _character: PlayerCharacter
var _identity: Label
var _summary: Label
var _swatch: ColorRect
var _grid: GridContainer
var _equipment_label: Label
var _features_box: VBoxContainer
var _close_button: Button


func _ready() -> void:
	_build_ui()
	hide()


func open_sheet(character: PlayerCharacter) -> void:
	_character = character
	_refresh()
	GameState.input_locked = true
	show()
	_close_button.grab_focus()


func close_sheet() -> void:
	if not visible:
		return
	hide()
	GameState.input_locked = false
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
	_identity.text = "%s — %s, уровень %d" % [_character.character_name, _character.character_class_name, _character.level]
	_summary.text = "Здоровье: %d / %d     КД: %d     Опыт: %d" % [
		_character.current_health, _character.maximum_health, _class_data.get_armor_class(_character), _character.experience
	]
	_swatch.color = Color.from_string(_character.appearance_color_hex, Color(0.3, 0.64, 0.91, 1))
	for child: Node in _grid.get_children():
		child.queue_free()
	for ability_id: String in ABILITY_ORDER:
		_add_cell(str(ABILITY_NAMES[ability_id]), HORIZONTAL_ALIGNMENT_LEFT)
		_add_cell(str(_character.get_ability_score(ability_id)), HORIZONTAL_ALIGNMENT_CENTER)
		_add_cell(_format_modifier(_character.get_ability_modifier(ability_id)), HORIZONTAL_ALIGNMENT_CENTER)
	var weapon: Dictionary = GameState.get_item_definition(_character.equipped_weapon_id)
	var armor: Dictionary = GameState.get_item_definition(_character.equipped_armor_id)
	var shield: Dictionary = GameState.get_item_definition(_character.equipped_shield_id)
	_equipment_label.text = "Оружие: %s\nДоспех: %s\nЩит: %s" % [
		str(weapon.get("name", "Без оружия")), str(armor.get("name", "Нет")), str(shield.get("name", "Нет"))
	]
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


func _add_cell(text_value: String, alignment: HorizontalAlignment) -> void:
	var label := Label.new()
	label.text = text_value
	label.horizontal_alignment = alignment
	label.custom_minimum_size = Vector2(180 if alignment == HORIZONTAL_ALIGNMENT_LEFT else 100, 44)
	label.add_theme_font_size_override("font_size", 20)
	_grid.add_child(label)


func _format_modifier(value: int) -> String:
	return "+%d" % value if value >= 0 else str(value)
