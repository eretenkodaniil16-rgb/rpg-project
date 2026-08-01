class_name SaveSlotsPanel
extends Control

signal load_completed(success: bool, kind: String, slot_id: int)
signal save_completed(success: bool, slot_id: int)
signal closed

const MODE_LOAD: String = "load"
const MODE_SAVE: String = "save"

var _mode: String = MODE_LOAD
var _title_label: Label
var _status_label: Label
var _slots_container: VBoxContainer
var _close_button: Button


func _ready() -> void:
	add_to_group("game_overlay")
	_build_ui()
	hide()


func open_for_load() -> void:
	_mode = MODE_LOAD
	_title_label.text = "ВЫБОР СОХРАНЕНИЯ"
	_status_label.text = "Выберите файл, с которого нужно продолжить."
	_refresh_slots()
	show()


func open_for_save() -> void:
	_mode = MODE_SAVE
	_title_label.text = "СОХРАНИТЬ ИГРУ"
	_status_label.text = "Выберите ячейку. Существующий файл будет перезаписан."
	_refresh_slots()
	show()


func close_panel() -> void:
	hide()
	closed.emit()


func _build_ui() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP

	var dimmer := ColorRect.new()
	dimmer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dimmer.color = Color(0.0, 0.0, 0.0, 0.72)
	dimmer.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dimmer)

	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)

	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(720.0, 590.0)
	center.add_child(panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 34)
	margin.add_theme_constant_override("margin_top", 28)
	margin.add_theme_constant_override("margin_right", 34)
	margin.add_theme_constant_override("margin_bottom", 28)
	panel.add_child(margin)

	var root_vbox := VBoxContainer.new()
	root_vbox.add_theme_constant_override("separation", 12)
	margin.add_child(root_vbox)

	_title_label = Label.new()
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_label.add_theme_font_size_override("font_size", 28)
	root_vbox.add_child(_title_label)

	_status_label = Label.new()
	_status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status_label.add_theme_color_override("font_color", Color(0.76, 0.80, 0.86, 1.0))
	_status_label.add_theme_font_size_override("font_size", 17)
	root_vbox.add_child(_status_label)

	root_vbox.add_child(HSeparator.new())

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0.0, 400.0)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root_vbox.add_child(scroll)

	_slots_container = VBoxContainer.new()
	_slots_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_slots_container.add_theme_constant_override("separation", 10)
	scroll.add_child(_slots_container)

	_close_button = Button.new()
	_close_button.custom_minimum_size = Vector2(0.0, 54.0)
	_close_button.text = "НАЗАД"
	_close_button.add_theme_font_size_override("font_size", 18)
	_close_button.pressed.connect(close_panel)
	root_vbox.add_child(_close_button)


func _refresh_slots() -> void:
	for child: Node in _slots_container.get_children():
		child.queue_free()

	if _mode == MODE_LOAD:
		var autosave_entry: Dictionary = GameState.get_autosave_entry()
		if bool(autosave_entry.get("exists", false)):
			_add_slot_button(autosave_entry, true)

	for entry: Dictionary in GameState.list_manual_save_slots():
		_add_slot_button(entry, false)


func _add_slot_button(entry: Dictionary, is_autosave: bool) -> void:
	var button := Button.new()
	button.custom_minimum_size = Vector2(0.0, 70.0)
	button.alignment = HORIZONTAL_ALIGNMENT_LEFT
	button.add_theme_font_size_override("font_size", 17)
	button.text = _entry_label(entry, is_autosave)
	var exists: bool = bool(entry.get("exists", false))
	button.disabled = _mode == MODE_LOAD and not exists
	var kind: String = str(entry.get("kind", SaveSlotSystem.AUTOSAVE_ID))
	var slot_id: int = int(entry.get("slot_id", 0))
	button.pressed.connect(_on_slot_pressed.bind(kind, slot_id))
	_slots_container.add_child(button)


func _on_slot_pressed(kind: String, slot_id: int) -> void:
	if _mode == MODE_LOAD:
		var loaded: bool = GameState.load_autosave() if kind == SaveSlotSystem.AUTOSAVE_ID else GameState.load_manual_slot(slot_id)
		_status_label.text = "Сохранение загружено." if loaded else "Не удалось загрузить выбранный файл."
		load_completed.emit(loaded, kind, slot_id)
		return

	var saved: bool = GameState.save_manual_slot(slot_id)
	_status_label.text = "Игра сохранена в ячейку %d." % slot_id if saved else "Не удалось сохранить игру."
	_refresh_slots()
	save_completed.emit(saved, slot_id)


func _entry_label(entry: Dictionary, is_autosave: bool) -> String:
	var exists: bool = bool(entry.get("exists", false))
	var heading: String = "АВТОСОХРАНЕНИЕ" if is_autosave else "ЯЧЕЙКА %d" % int(entry.get("slot_id", 0))
	if not exists:
		return "%s\n    Пустая ячейка" % heading
	var character_name: String = str(entry.get("character_name", "Герой"))
	var class_name: String = str(entry.get("character_class_name", ""))
	var level: int = int(entry.get("level", 1))
	var current_health: int = int(entry.get("current_health", 0))
	var maximum_health: int = int(entry.get("maximum_health", 0))
	var location_label: String = str(entry.get("location_label", "Караульный пост"))
	var timestamp: String = _format_timestamp(int(entry.get("saved_at_unix", 0)))
	return "%s\n    %s · %s · ур. %d · HP %d/%d\n    %s · %s" % [
		heading,
		character_name,
		class_name,
		level,
		current_health,
		maximum_health,
		location_label,
		timestamp
	]


func _format_timestamp(unix_time: int) -> String:
	if unix_time <= 0:
		return "время не указано"
	var value: Dictionary = Time.get_datetime_dict_from_unix_time(unix_time)
	return "%02d.%02d.%04d %02d:%02d" % [
		int(value.get("day", 1)),
		int(value.get("month", 1)),
		int(value.get("year", 1970)),
		int(value.get("hour", 0)),
		int(value.get("minute", 0))
	]
