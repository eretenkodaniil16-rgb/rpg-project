class_name LootContainerPanel
extends Control

signal take_item_requested(source_id: String, item_id: String)
signal take_all_requested(source_id: String)
signal close_requested

var _source_id: String = ""
var _record: Dictionary = {}
var _definitions: Dictionary = {}
var _title_label: Label = null
var _status_label: Label = null
var _items_box: VBoxContainer = null
var _take_all_button: Button = null
var _close_button: Button = null
var _item_action_labels: Array[String] = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	z_index = 4300
	_build_ui()
	visible = false


func open_source(source_id: String, record: Dictionary, definitions: Dictionary) -> void:
	_source_id = source_id
	_record = record.duplicate(true)
	_definitions = definitions.duplicate(true)
	visible = true
	_rebuild_contents()


func refresh_source(record: Dictionary, definitions: Dictionary) -> void:
	_record = record.duplicate(true)
	_definitions = definitions.duplicate(true)
	if visible:
		_rebuild_contents()


func close_panel() -> void:
	if not visible:
		return
	visible = false
	_source_id = ""
	_record.clear()
	_definitions.clear()
	close_requested.emit()


func is_open() -> bool:
	return visible


func get_source_id() -> String:
	return _source_id


func get_item_action_labels_for_testing() -> Array[String]:
	return _item_action_labels.duplicate()


func press_item_for_testing(item_id: String) -> void:
	if visible and not _source_id.is_empty():
		take_item_requested.emit(_source_id, item_id)


func press_take_all_for_testing() -> void:
	if visible and not _source_id.is_empty():
		take_all_requested.emit(_source_id)


func _build_ui() -> void:
	var dimmer := ColorRect.new()
	dimmer.name = "Dimmer"
	dimmer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dimmer.color = Color(0.02, 0.025, 0.035, 0.78)
	dimmer.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dimmer)

	var panel := PanelContainer.new()
	panel.name = "LootPanel"
	panel.anchor_left = 0.08
	panel.anchor_top = 0.08
	panel.anchor_right = 0.92
	panel.anchor_bottom = 0.92
	panel.offset_left = 0.0
	panel.offset_top = 0.0
	panel.offset_right = 0.0
	panel.offset_bottom = 0.0
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 18)
	margin.add_theme_constant_override("margin_top", 16)
	margin.add_theme_constant_override("margin_right", 18)
	margin.add_theme_constant_override("margin_bottom", 16)
	panel.add_child(margin)

	var root_box := VBoxContainer.new()
	root_box.add_theme_constant_override("separation", 12)
	margin.add_child(root_box)

	_title_label = Label.new()
	_title_label.name = "LootTitle"
	_title_label.text = "Добыча"
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_label.add_theme_font_size_override("font_size", 24)
	root_box.add_child(_title_label)

	_status_label = Label.new()
	_status_label.name = "LootStatus"
	_status_label.text = "Выберите предмет."
	_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status_label.add_theme_font_size_override("font_size", 15)
	root_box.add_child(_status_label)

	var scroll := ScrollContainer.new()
	scroll.name = "LootScroll"
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root_box.add_child(scroll)

	_items_box = VBoxContainer.new()
	_items_box.name = "LootItems"
	_items_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_items_box.add_theme_constant_override("separation", 8)
	scroll.add_child(_items_box)

	var footer := HBoxContainer.new()
	footer.name = "LootFooter"
	footer.add_theme_constant_override("separation", 10)
	root_box.add_child(footer)

	_take_all_button = Button.new()
	_take_all_button.name = "TakeAllButton"
	_take_all_button.text = "ЗАБРАТЬ ВСЁ"
	_take_all_button.custom_minimum_size = Vector2(0.0, 58.0)
	_take_all_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_take_all_button.pressed.connect(_on_take_all_pressed)
	footer.add_child(_take_all_button)

	_close_button = Button.new()
	_close_button.name = "CloseButton"
	_close_button.text = "ЗАКРЫТЬ"
	_close_button.custom_minimum_size = Vector2(0.0, 58.0)
	_close_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_close_button.pressed.connect(close_panel)
	footer.add_child(_close_button)


func _rebuild_contents() -> void:
	if _title_label == null or _items_box == null:
		return
	for child: Node in _items_box.get_children():
		child.queue_free()
	_item_action_labels.clear()
	_title_label.text = str(_record.get("label", "Добыча"))
	var items: Array = _record.get("items", []) as Array if _record.get("items", []) is Array else []
	if items.is_empty():
		_status_label.text = "Контейнер пуст."
		_take_all_button.disabled = true
		var empty_label := Label.new()
		empty_label.text = "Здесь больше ничего нет."
		empty_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		empty_label.add_theme_font_size_override("font_size", 17)
		_items_box.add_child(empty_label)
		return
	_status_label.text = "Выберите предмет для переноса в инвентарь."
	_take_all_button.disabled = false
	for value: Variant in items:
		if not value is Dictionary:
			continue
		var entry: Dictionary = value as Dictionary
		var item_id: String = str(entry.get("item_id", ""))
		var quantity: int = maxi(int(entry.get("quantity", 0)), 0)
		if item_id.is_empty() or quantity <= 0:
			continue
		var definition_value: Variant = _definitions.get(item_id, {})
		var definition: Dictionary = definition_value as Dictionary if definition_value is Dictionary else {}
		var item_name: String = str(definition.get("name", "Неизвестный предмет"))
		var action_label: String = "ПОДОБРАТЬ: %s%s" % [
			item_name.to_upper(),
			" ×%d" % quantity if quantity > 1 else ""
		]
		_item_action_labels.append(action_label)
		var button := Button.new()
		button.name = "Take_%s" % item_id
		button.text = action_label
		button.tooltip_text = str(definition.get("description", ""))
		button.custom_minimum_size = Vector2(0.0, 62.0)
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.pressed.connect(_on_item_pressed.bind(item_id))
		_items_box.add_child(button)


func _on_item_pressed(item_id: String) -> void:
	if _source_id.is_empty() or item_id.is_empty():
		return
	take_item_requested.emit(_source_id, item_id)


func _on_take_all_pressed() -> void:
	if _source_id.is_empty():
		return
	take_all_requested.emit(_source_id)
