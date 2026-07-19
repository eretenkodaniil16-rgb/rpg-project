extends "res://scripts/character_creation/character_creator_showcase.gd"

const CAROUSEL_COPY_COUNT: int = 5
const CAROUSEL_MIDDLE_COPY: int = 2
const SELECTOR_CARD_WIDTH: float = 180.0
const SELECTOR_CARD_SEPARATION: float = 12.0
const SELECTOR_STEP_WIDTH: float = SELECTOR_CARD_WIDTH + SELECTOR_CARD_SEPARATION

var _carousel_recentering: Dictionary = {}
var _carousel_touch_active: Dictionary = {}


func _build_race_step() -> void:
	super._build_race_step()
	if _races.is_empty():
		return
	_install_cycle_navigation(
		"RacePreviousButton",
		"RaceNextButton",
		"РАСА %d ИЗ %d" % [maxi(_race_index(_selected_race_id), 0) + 1, _races.size()],
		"Предыдущая раса",
		"Следующая раса",
		_select_adjacent_race.bind(-1),
		_select_adjacent_race.bind(1)
	)
	_rebuild_race_carousel()


func _build_class_step() -> void:
	super._build_class_step()
	if _classes.is_empty():
		return
	_install_cycle_navigation(
		"ClassPreviousButton",
		"ClassNextButton",
		"КЛАСС %d ИЗ %d" % [maxi(_class_index(_selected_class_id), 0) + 1, _classes.size()],
		"Предыдущий класс",
		"Следующий класс",
		_select_adjacent_class.bind(-1),
		_select_adjacent_class.bind(1)
	)
	_rebuild_class_carousel()


func _install_cycle_navigation(previous_name: String, next_name: String, caption: String, previous_tooltip: String, next_tooltip: String, previous_callback: Callable, next_callback: Callable) -> void:
	var navigation: HBoxContainer = HBoxContainer.new()
	navigation.name = "%sNavigation" % caption.get_slice(" ", 0).capitalize()
	navigation.add_theme_constant_override("separation", 12)
	_content_container.add_child(navigation)
	_content_container.move_child(navigation, 0)
	var previous_button: Button = _make_cycle_arrow(previous_name, "◀", previous_tooltip, previous_callback)
	navigation.add_child(previous_button)
	var caption_label: Label = _make_label(caption, 18, Color(0.78, 0.83, 0.9, 1.0))
	caption_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	caption_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	caption_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	navigation.add_child(caption_label)
	var next_button: Button = _make_cycle_arrow(next_name, "▶", next_tooltip, next_callback)
	navigation.add_child(next_button)


func _make_cycle_arrow(node_name: String, symbol: String, tooltip: String, callback: Callable) -> Button:
	var button: Button = Button.new()
	button.name = node_name
	button.text = symbol
	button.tooltip_text = tooltip
	button.custom_minimum_size = Vector2(76.0, 54.0)
	button.add_theme_font_size_override("font_size", 25)
	button.pressed.connect(callback)
	return button


func _select_adjacent_race(offset: int) -> void:
	if _races.is_empty():
		return
	var current_index: int = _race_index(_selected_race_id)
	if current_index < 0:
		current_index = 0
	var next_index: int = (current_index + offset) % _races.size()
	if next_index < 0:
		next_index += _races.size()
	_select_race(str(_races[next_index].get("id", "human")))


func _select_adjacent_class(offset: int) -> void:
	if _classes.is_empty():
		return
	var current_index: int = _class_index(_selected_class_id)
	if current_index < 0:
		current_index = 0
	var next_index: int = (current_index + offset) % _classes.size()
	if next_index < 0:
		next_index += _classes.size()
	_select_class(str(_classes[next_index].get("id", "")))


func _race_index(race_id: String) -> int:
	for index: int in range(_races.size()):
		if str(_races[index].get("id", "")) == race_id:
			return index
	return -1


func _class_index(class_id: String) -> int:
	for index: int in range(_classes.size()):
		if str(_classes[index].get("id", "")) == class_id:
			return index
	return -1


func _rebuild_race_carousel() -> void:
	var entries: Array[Dictionary] = []
	for race_data: Dictionary in _races:
		entries.append({"id": str(race_data.get("id", "human")), "symbol": str(race_data.get("selection_symbol", "??")), "title": str(race_data.get("name", "Раса")), "subtitle": str(race_data.get("ability_bonus_description", "")), "accent": str(race_data.get("color_hex", PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX))})
	_rebuild_cyclic_carousel("RaceCarousel", entries, _selected_race_id, "race")


func _rebuild_class_carousel() -> void:
	var entries: Array[Dictionary] = []
	for class_data: Dictionary in _classes:
		var class_id: String = str(class_data.get("id", ""))
		var class_ui: Dictionary = _class_ui(class_id)
		entries.append({"id": class_id, "symbol": str(class_ui.get("symbol", "??")), "title": str(class_data.get("name", "Класс")), "subtitle": str(class_data.get("role", "")), "accent": str(class_ui.get("accent", "#66778B"))})
	_rebuild_cyclic_carousel("ClassCarousel", entries, _selected_class_id, "class")


func _rebuild_cyclic_carousel(carousel_name: String, entries: Array[Dictionary], selected_id: String, selector_kind: String) -> void:
	var carousel: ScrollContainer = _content_container.get_node_or_null(carousel_name) as ScrollContainer
	if carousel == null or entries.is_empty() or carousel.get_child_count() == 0:
		return
	var strip: HBoxContainer = carousel.get_child(0) as HBoxContainer
	if strip == null:
		return
	for child: Node in strip.get_children():
		strip.remove_child(child)
		child.queue_free()
	var ids: Array[String] = []
	for entry: Dictionary in entries:
		ids.append(str(entry.get("id", "")))
	for copy_index: int in range(CAROUSEL_COPY_COUNT):
		for entry: Dictionary in entries:
			var entry_id: String = str(entry.get("id", ""))
			var accent: Color = Color.from_string(str(entry.get("accent", "#66778B")), Color.WHITE)
			var card: Button = _make_selector_card(str(entry.get("symbol", "??")), str(entry.get("title", "Вариант")), str(entry.get("subtitle", "")), accent, entry_id == selected_id, _select_carousel_entry.bind(selector_kind, entry_id))
			card.set_meta("selector_id", entry_id)
			card.set_meta("carousel_copy", copy_index)
			strip.add_child(card)
	call_deferred("_configure_cyclic_carousel", carousel, ids, selected_id, selector_kind)


func _configure_cyclic_carousel(carousel: ScrollContainer, ids: Array[String], selected_id: String, selector_kind: String) -> void:
	await get_tree().process_frame
	if not is_instance_valid(carousel) or ids.is_empty():
		return
	var cycle_width: float = SELECTOR_STEP_WIDTH * float(ids.size())
	var selected_index: int = ids.find(selected_id)
	if selected_index < 0:
		selected_index = 0
	var centered_offset: float = maxf((carousel.size.x - SELECTOR_CARD_WIDTH) * 0.5, 0.0)
	carousel.scroll_horizontal = roundi(float(CAROUSEL_MIDDLE_COPY) * cycle_width + float(selected_index) * SELECTOR_STEP_WIDTH - centered_offset)
	carousel.scroll_horizontal_by_default = true
	carousel.set_meta("cyclic_ids", ids)
	carousel.set_meta("cyclic_selector_kind", selector_kind)
	carousel.set_meta("cyclic_cycle_width", cycle_width)
	if not bool(carousel.get_meta("cyclic_signals_connected", false)):
		var scroll_bar: HScrollBar = carousel.get_h_scroll_bar()
		if scroll_bar != null:
			scroll_bar.value_changed.connect(_on_cyclic_scroll_changed.bind(carousel))
		carousel.scroll_started.connect(_on_cyclic_carousel_scroll_started.bind(carousel))
		carousel.scroll_ended.connect(_on_cyclic_carousel_scroll_ended.bind(carousel))
		carousel.set_meta("cyclic_signals_connected", true)


func _on_cyclic_carousel_scroll_started(carousel: ScrollContainer) -> void:
	if is_instance_valid(carousel):
		_carousel_touch_active[carousel.get_instance_id()] = true


func _on_cyclic_scroll_changed(value: float, carousel: ScrollContainer) -> void:
	if not is_instance_valid(carousel):
		return
	var cycle_width: float = float(carousel.get_meta("cyclic_cycle_width", 0.0))
	if cycle_width <= 0.0:
		return
	var key: int = carousel.get_instance_id()
	if bool(_carousel_touch_active.get(key, false)) or bool(_carousel_recentering.get(key, false)):
		return
	var scroll_bar: HScrollBar = carousel.get_h_scroll_bar()
	if scroll_bar == null:
		return
	var shifted_value: float = value
	var edge_zone: float = cycle_width * 0.12
	if value < edge_zone:
		shifted_value = value + cycle_width * float(CAROUSEL_MIDDLE_COPY)
	elif value > scroll_bar.max_value - scroll_bar.page - edge_zone:
		shifted_value = value - cycle_width * float(CAROUSEL_MIDDLE_COPY)
	if not is_equal_approx(shifted_value, value):
		_set_carousel_scroll(carousel, shifted_value)


func _on_cyclic_carousel_scroll_ended(carousel: ScrollContainer) -> void:
	if not is_instance_valid(carousel):
		return
	_carousel_touch_active.erase(carousel.get_instance_id())
	var ids: Array[String] = _carousel_ids(carousel)
	if ids.is_empty():
		return
	var center_position: float = float(carousel.scroll_horizontal) + carousel.size.x * 0.5
	var raw_index: int = roundi((center_position - SELECTOR_CARD_WIDTH * 0.5) / SELECTOR_STEP_WIDTH)
	var logical_index: int = raw_index % ids.size()
	if logical_index < 0:
		logical_index += ids.size()
	var selector_kind: String = str(carousel.get_meta("cyclic_selector_kind", ""))
	var entry_id: String = ids[logical_index]
	var selection_changed: bool = (selector_kind == "race" and entry_id != _selected_race_id) or (selector_kind == "class" and entry_id != _selected_class_id)
	if selection_changed:
		_select_carousel_entry(selector_kind, entry_id)
	else:
		_recenter_cyclic_carousel(carousel)


func _recenter_cyclic_carousel(carousel: ScrollContainer) -> void:
	if not is_instance_valid(carousel):
		return
	var cycle_width: float = float(carousel.get_meta("cyclic_cycle_width", 0.0))
	if cycle_width <= 0.0:
		return
	var local_value: float = fposmod(float(carousel.scroll_horizontal), cycle_width)
	_set_carousel_scroll(carousel, float(CAROUSEL_MIDDLE_COPY) * cycle_width + local_value)


func _set_carousel_scroll(carousel: ScrollContainer, value: float) -> void:
	var scroll_bar: HScrollBar = carousel.get_h_scroll_bar()
	if scroll_bar == null:
		return
	var limit: int = maxi(roundi(scroll_bar.max_value - scroll_bar.page), 0)
	var key: int = carousel.get_instance_id()
	_carousel_recentering[key] = true
	carousel.scroll_horizontal = clampi(roundi(value), 0, limit)
	call_deferred("_release_carousel_recentering", key)


func _release_carousel_recentering(key: int) -> void:
	_carousel_recentering.erase(key)


func _carousel_ids(carousel: ScrollContainer) -> Array[String]:
	var result: Array[String] = []
	var value: Variant = carousel.get_meta("cyclic_ids", [])
	if value is Array:
		for entry: Variant in value:
			result.append(str(entry))
	return result


func _select_carousel_entry(selector_kind: String, entry_id: String) -> void:
	if selector_kind == "race":
		if entry_id != _selected_race_id:
			_select_race(entry_id)
	elif selector_kind == "class" and entry_id != _selected_class_id:
		_select_class(entry_id)
