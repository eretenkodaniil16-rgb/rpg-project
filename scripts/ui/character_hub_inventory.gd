class_name CharacterHubInventory
extends CharacterHub

signal item_use_requested(item_id: String)

var _selected_inventory_entry: Dictionary = {}
var _inventory_details: Label
var _inventory_use: Button
var _inventory_equip: Button


func _refresh_character() -> void:
	_clear(_character_box)
	var summary := HBoxContainer.new()
	summary.name = "CharacterSummary"
	summary.add_theme_constant_override("separation", 16)
	_character_box.add_child(summary)
	summary.add_child(_build_character_portrait())

	var overview := VBoxContainer.new()
	overview.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	overview.add_theme_constant_override("separation", 5)
	summary.add_child(overview)
	overview.add_child(_label("%s — %s, уровень %d" % [_hero.character_name, _hero.character_class_name, _hero.level], 25))
	overview.add_child(_label("%s · КД %d" % [_hero.race_name, _class_data.get_armor_class(_hero)], 18))

	var health_progress := ProgressBar.new()
	health_progress.name = "CharacterHealthBar"
	health_progress.custom_minimum_size = Vector2(0.0, 28.0)
	health_progress.max_value = maxi(_hero.maximum_health, 1)
	health_progress.value = clampi(_hero.current_health, 0, _hero.maximum_health)
	health_progress.show_percentage = false
	overview.add_child(health_progress)
	overview.add_child(_label("Здоровье: %d/%d" % [_hero.current_health, _hero.maximum_health], 17))

	var experience_progress: int = ProgressionSystem.experience_progress_in_level(_hero)
	var experience_required: int = ProgressionSystem.experience_required_for_next_level(_hero)
	var experience_bar := ProgressBar.new()
	experience_bar.name = "CharacterExperienceBar"
	experience_bar.custom_minimum_size = Vector2(0.0, 24.0)
	experience_bar.max_value = maxi(experience_required, 1)
	experience_bar.value = clampi(experience_progress, 0, experience_required)
	experience_bar.show_percentage = false
	overview.add_child(experience_bar)
	overview.add_child(_label("Опыт: %d/%d · всего %d" % [experience_progress, experience_required, _hero.experience], 17))
	overview.add_child(_label("Время мира: %s" % _world_time.format_current(_game_state()), 16))

	var spell_profile: Dictionary = _spellcasting.get_spellcasting_profile(_hero.character_class_id)
	if not spell_profile.is_empty() or not _spellcasting.get_known_spell_ids(_hero).is_empty():
		var attack_bonus: int = _spellcasting.get_spell_attack_bonus(_hero)
		overview.add_child(_label("Магия: атака %s · Сл %d" % ["+%d" % attack_bonus if attack_bonus >= 0 else str(attack_bonus), _spellcasting.get_spell_save_dc(_hero)], 16))
	var concentration_id: String = _spellcasting.get_concentration_spell_id(_hero)
	if not concentration_id.is_empty():
		var concentration_spell: Dictionary = _class_data.get_ability_definition(concentration_id)
		overview.add_child(_label("Концентрация: %s" % str(concentration_spell.get("name", concentration_id)), 16))

	_character_box.add_child(HSeparator.new())
	var names: Dictionary = {
		"strength": "Сила",
		"dexterity": "Ловкость",
		"constitution": "Телосложение",
		"intelligence": "Интеллект",
		"wisdom": "Мудрость",
		"charisma": "Харизма"
	}
	for ability_id: String in names.keys():
		var modifier: int = _hero.get_ability_modifier(ability_id)
		_character_box.add_child(_label("%s: %d (%s)" % [str(names[ability_id]), _hero.get_ability_score(ability_id), "+%d" % modifier if modifier >= 0 else str(modifier)], 18))

	_character_box.add_child(HSeparator.new())
	var field_title := Label.new()
	field_title.text = "ПОЛЕ БОЯ"
	field_title.add_theme_font_size_override("font_size", 21)
	_character_box.add_child(field_title)
	_grid_toggle_button = Button.new()
	_grid_toggle_button.name = "GridToggleButton"
	_grid_toggle_button.custom_minimum_size = Vector2(430.0, 54.0)
	_grid_toggle_button.add_theme_font_size_override("font_size", 18)
	_grid_toggle_button.pressed.connect(_on_grid_toggle_pressed)
	_character_box.add_child(_grid_toggle_button)
	_sync_grid_toggle()

	var rest_row := HBoxContainer.new()
	rest_row.add_theme_constant_override("separation", 10)
	_character_box.add_child(rest_row)
	var short_rest := Button.new()
	short_rest.text = "КОРОТКИЙ ОТДЫХ"
	short_rest.custom_minimum_size = Vector2(230.0, 54.0)
	short_rest.pressed.connect(_rest.bind(false))
	rest_row.add_child(short_rest)
	var long_rest := Button.new()
	long_rest.text = "ДОЛГИЙ ОТДЫХ"
	long_rest.custom_minimum_size = Vector2(230.0, 54.0)
	long_rest.pressed.connect(_rest.bind(true))
	rest_row.add_child(long_rest)


func _build_character_portrait() -> Control:
	var portrait := PanelContainer.new()
	portrait.name = "CharacterPortrait"
	portrait.custom_minimum_size = Vector2(142.0, 142.0)
	var style := StyleBoxFlat.new()
	style.bg_color = Color.from_string(
		_hero.appearance_color_hex,
		Color.from_string(PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX, Color(0.3, 0.64, 0.91, 1.0))
	)
	style.border_width_left = 4
	style.border_width_top = 4
	style.border_width_right = 4
	style.border_width_bottom = 4
	style.border_color = Color(0.9, 0.95, 1.0, 0.92)
	style.corner_radius_top_left = 18
	style.corner_radius_top_right = 18
	style.corner_radius_bottom_left = 18
	style.corner_radius_bottom_right = 18
	portrait.add_theme_stylebox_override("panel", style)

	var portrait_content := VBoxContainer.new()
	portrait_content.alignment = BoxContainer.ALIGNMENT_CENTER
	portrait.add_child(portrait_content)
	var initials := Label.new()
	initials.text = _character_initials(_hero.character_name)
	initials.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	initials.add_theme_font_size_override("font_size", 46)
	initials.add_theme_color_override("font_color", Color.WHITE)
	initials.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.85))
	initials.add_theme_constant_override("shadow_offset_x", 2)
	initials.add_theme_constant_override("shadow_offset_y", 2)
	portrait_content.add_child(initials)
	var race_label := Label.new()
	race_label.text = _hero.race_name.to_upper()
	race_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	race_label.add_theme_font_size_override("font_size", 14)
	race_label.add_theme_color_override("font_color", Color(0.97, 0.98, 1.0, 0.94))
	portrait_content.add_child(race_label)
	return portrait


func _character_initials(value: String) -> String:
	var words: PackedStringArray = value.strip_edges().split(" ", false)
	if words.is_empty():
		return "?"
	var result: String = words[0].left(1).to_upper()
	if words.size() > 1:
		result += words[1].left(1).to_upper()
	return result


func _refresh_inventory() -> void:
	_clear(_inventory_box)
	_selected_inventory_entry.clear()
	var state: Node = _game_state()
	var entries: Array = state.call("get_inventory_entries") as Array if state != null else []
	if entries.is_empty():
		_inventory_box.add_child(_label("Инвентарь пуст.", 19))
		return
	entries.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return str(a.get("type", "")) < str(b.get("type", "")))
	for value: Variant in entries:
		if not value is Dictionary:
			continue
		var entry: Dictionary = value as Dictionary
		var equipped: bool = _class_data.is_equipped(_hero, str(entry.get("id", "")))
		var button := Button.new()
		button.text = "%s%s ×%d" % ["★ " if equipped else "", str(entry.get("name", "Предмет")), int(entry.get("quantity", 0))]
		button.custom_minimum_size = Vector2(0.0, 52.0)
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.pressed.connect(_select_inventory_entry.bind(entry))
		_inventory_box.add_child(button)
	_inventory_box.add_child(HSeparator.new())
	_inventory_details = _label("Выберите предмет.", 18)
	_inventory_box.add_child(_inventory_details)
	_inventory_use = Button.new()
	_inventory_use.name = "InventoryUseButton"
	_inventory_use.text = "ИСПОЛЬЗОВАТЬ"
	_inventory_use.custom_minimum_size = Vector2(0.0, 54.0)
	_inventory_use.pressed.connect(_use_inventory_entry)
	_inventory_use.hide()
	_inventory_box.add_child(_inventory_use)
	_inventory_equip = Button.new()
	_inventory_equip.text = "ЭКИПИРОВАТЬ"
	_inventory_equip.custom_minimum_size = Vector2(0.0, 54.0)
	_inventory_equip.pressed.connect(_equip_inventory_entry)
	_inventory_equip.hide()
	_inventory_box.add_child(_inventory_equip)
	if entries[0] is Dictionary:
		_select_inventory_entry(entries[0] as Dictionary)


func _select_inventory_entry(entry: Dictionary) -> void:
	_selected_inventory_entry = entry.duplicate(true)
	var item_type: String = str(entry.get("type", "misc"))
	var item_id: String = str(entry.get("id", ""))
	var equipped: bool = _class_data.is_equipped(_hero, item_id)
	var state_text: String = "\nСостояние: ЭКИПИРОВАНО" if equipped else ""
	_inventory_details.text = "%s\n\nКоличество: %d%s%s\n\n%s" % [str(entry.get("name", "Предмет")), int(entry.get("quantity", 0)), state_text, _inventory_stats(entry), str(entry.get("description", "Описание отсутствует."))]
	var use_action_value: Variant = entry.get("use_action", {})
	var use_action: Dictionary = use_action_value as Dictionary if use_action_value is Dictionary else {}
	_inventory_use.visible = not use_action.is_empty()
	_inventory_use.disabled = int(entry.get("quantity", 0)) <= 0
	_inventory_use.text = str(use_action.get("inventory_label", "ИСПОЛЬЗОВАТЬ"))
	_inventory_equip.visible = item_type in ["weapon", "armor", "shield"]
	_inventory_equip.disabled = equipped
	_inventory_equip.text = "ЭКИПИРОВАНО" if equipped else "ЭКИПИРОВАТЬ"


func _use_inventory_entry() -> void:
	var item_id: String = str(_selected_inventory_entry.get("id", ""))
	if item_id.is_empty():
		return
	item_use_requested.emit(item_id)


func _equip_inventory_entry() -> void:
	var item_id: String = str(_selected_inventory_entry.get("id", ""))
	if item_id.is_empty():
		return
	if _class_data.equip_item(_hero, item_id):
		_refresh_all()


func _inventory_stats(entry: Dictionary) -> String:
	match str(entry.get("type", "")):
		"weapon":
			var dice: Array = entry.get("damage_dice", [1, 1]) as Array
			return "\nУрон: %dк%d %s" % [int(dice[0]), int(dice[1]), str(entry.get("damage_type", "физический"))]
		"armor":
			return "\nБазовый КД: %d" % int(entry.get("base_ac", 10))
		"shield":
			return "\nБонус КД: +%d" % int(entry.get("ac_bonus", 2))
	return ""