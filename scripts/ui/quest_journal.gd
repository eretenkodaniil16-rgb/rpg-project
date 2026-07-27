class_name QuestJournal
extends Control

var _current_status: String = "active"
var _active_tab: Button
var _completed_tab: Button
var _quest_list: VBoxContainer
var _details_label: Label


func _ready() -> void:
	_build_layout()
	hide()


func open_journal() -> void:
	GameState.input_locked = true
	show()
	_set_status("active")


func close_journal() -> void:
	hide()
	GameState.input_locked = false


func _unhandled_input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		close_journal()
		get_viewport().set_input_as_handled()


func _build_layout() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP

	var dimmer := ColorRect.new()
	dimmer.color = Color(0.0, 0.0, 0.0, 0.72)
	dimmer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dimmer.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dimmer)

	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)

	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(1040.0, 600.0)
	center.add_child(panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 30)
	margin.add_theme_constant_override("margin_top", 24)
	margin.add_theme_constant_override("margin_right", 30)
	margin.add_theme_constant_override("margin_bottom", 24)
	panel.add_child(margin)

	var root_column := VBoxContainer.new()
	root_column.add_theme_constant_override("separation", 16)
	margin.add_child(root_column)

	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 12)
	root_column.add_child(header)

	var title := Label.new()
	title.text = "ЖУРНАЛ ЗАДАНИЙ"
	title.add_theme_font_size_override("font_size", 27)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)

	_active_tab = Button.new()
	_active_tab.text = "Активные"
	_active_tab.custom_minimum_size = Vector2(140.0, 48.0)
	_active_tab.pressed.connect(_set_status.bind("active"))
	header.add_child(_active_tab)

	_completed_tab = Button.new()
	_completed_tab.text = "Завершённые"
	_completed_tab.custom_minimum_size = Vector2(170.0, 48.0)
	_completed_tab.pressed.connect(_set_status.bind("completed"))
	header.add_child(_completed_tab)

	var close_button := Button.new()
	close_button.text = "Закрыть"
	close_button.custom_minimum_size = Vector2(130.0, 48.0)
	close_button.pressed.connect(close_journal)
	header.add_child(close_button)

	var separator := HSeparator.new()
	root_column.add_child(separator)

	var body := HSplitContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.split_offset = 360
	root_column.add_child(body)

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(340.0, 0.0)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(scroll)

	_quest_list = VBoxContainer.new()
	_quest_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_quest_list.add_theme_constant_override("separation", 8)
	scroll.add_child(_quest_list)

	_details_label = Label.new()
	_details_label.custom_minimum_size = Vector2(560.0, 0.0)
	_details_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_details_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_details_label.add_theme_font_size_override("font_size", 20)
	_details_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_details_label.text = "Выберите задание слева."
	body.add_child(_details_label)


func _set_status(status: String) -> void:
	_current_status = status
	_active_tab.disabled = status == "active"
	_completed_tab.disabled = status == "completed"
	_refresh()


func _refresh() -> void:
	_clear_container(_quest_list)
	var quests: Array = GameState.get_quests_by_status(_current_status)
	if quests.is_empty():
		var empty_label := Label.new()
		empty_label.text = "Нет заданий в этом разделе."
		empty_label.add_theme_font_size_override("font_size", 19)
		_quest_list.add_child(empty_label)
		_details_label.text = "Здесь появятся задания по мере прохождения игры."
		return

	for quest_value: Variant in quests:
		if not quest_value is Dictionary:
			continue
		var quest := quest_value as Dictionary
		var button := Button.new()
		button.text = str(quest.get("title", "Неизвестное задание"))
		button.custom_minimum_size = Vector2(0.0, 58.0)
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.pressed.connect(_show_details.bind(quest))
		_quest_list.add_child(button)

	var first_quest: Variant = quests[0]
	if first_quest is Dictionary:
		_show_details(first_quest as Dictionary)


func _show_details(quest: Dictionary) -> void:
	var status: String = str(quest.get("status", "active"))
	var stage_index: int = int(quest.get("stage_index", 0))
	var stages_value: Variant = quest.get("stages", [])
	var stages: Array = stages_value as Array if stages_value is Array else []
	var lines: Array[String] = []
	lines.append(str(quest.get("title", "Задание")))
	lines.append("Статус: %s" % ("Завершено" if status == "completed" else "Активно"))
	lines.append("")
	lines.append(str(quest.get("description", "")))
	lines.append("")
	lines.append("Этапы:")

	for index: int in range(stages.size()):
		var stage_value: Variant = stages[index]
		if not stage_value is Dictionary:
			continue
		var marker: String = "○"
		if status == "completed" or index < stage_index:
			marker = "✓"
		elif index == stage_index:
			marker = "→"
		lines.append("%s %s" % [marker, str((stage_value as Dictionary).get("text", "Этап"))])

	var rewards_value: Variant = quest.get("rewards", [])
	var rewards: Array = rewards_value as Array if rewards_value is Array else []
	if not rewards.is_empty():
		lines.append("")
		lines.append("Награды:")
		for reward_value: Variant in rewards:
			if not reward_value is Dictionary:
				continue
			var reward := reward_value as Dictionary
			var item_id: String = str(reward.get("item_id", ""))
			var item: Dictionary = GameState.get_item_definition(item_id)
			lines.append("• %s ×%d" % [str(item.get("name", item_id)), int(reward.get("quantity", 1))])

	_details_label.text = "\n".join(lines)


func _clear_container(container: Container) -> void:
	for child: Node in container.get_children():
		child.queue_free()
