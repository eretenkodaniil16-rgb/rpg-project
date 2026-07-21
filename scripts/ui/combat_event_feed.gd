class_name CombatEventFeed
extends Control

const MAX_CARDS: int = 2
var _cards: VBoxContainer


func _ready() -> void:
	add_to_group("combat_ui")
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	z_index = 320
	_cards = VBoxContainer.new()
	_cards.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_cards.offset_left = -190.0
	_cards.offset_top = 162.0
	_cards.offset_right = 190.0
	_cards.offset_bottom = 310.0
	_cards.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_cards.add_theme_constant_override("separation", 6)
	add_child(_cards)


func show_result(result: AttackResult) -> void:
	if result == null:
		return
	if not result.automatic_hit and result.natural_roll > 0:
		get_tree().call_group("dice_presenter", "show_d20_roll", result.attacker_name, result.attack_name, result.natural_roll, result.total, result.hit, result.first_roll, result.second_roll)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(380.0, 58.0)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.modulate = Color(1.0, 1.0, 1.0, 0.90)
	_cards.add_child(panel)
	_cards.move_child(panel, 0)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 10)
	margin.add_theme_constant_override("margin_top", 6)
	margin.add_theme_constant_override("margin_right", 10)
	margin.add_theme_constant_override("margin_bottom", 6)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(margin)
	var column := VBoxContainer.new()
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(column)
	var title := Label.new()
	title.text = "%s → %s%s" % [result.attacker_name, result.target_name, " · РЕАКЦИЯ" if result.is_reaction else ""]
	title.add_theme_font_size_override("font_size", 14)
	title.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	column.add_child(title)
	var outcome := Label.new()
	if result.automatic_hit:
		outcome.text = "%s · %d урона" % [result.attack_name, result.damage]
	elif result.hit:
		outcome.text = "%s · %d против КД %d · %s%d урона" % [result.attack_name, result.total, result.target_armor_class, "КРИТ · " if result.critical else "", result.damage]
	else:
		outcome.text = "%s · %d против КД %d · ПРОМАХ" % [result.attack_name, result.total, result.target_armor_class]
	outcome.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	outcome.add_theme_font_size_override("font_size", 13)
	outcome.add_theme_color_override("font_color", Color(0.72, 1.0, 0.74, 1.0) if result.hit else Color(1.0, 0.66, 0.58, 1.0))
	column.add_child(outcome)
	while _cards.get_child_count() > MAX_CARDS:
		_cards.get_child(_cards.get_child_count() - 1).queue_free()
	_fade_card(panel)


func card_count() -> int:
	return _cards.get_child_count() if _cards != null else 0


func _fade_card(panel: Control) -> void:
	await get_tree().create_timer(1.8).timeout
	if not is_instance_valid(panel):
		return
	var tween := create_tween()
	tween.tween_property(panel, "modulate:a", 0.0, 0.24)
	await tween.finished
	if is_instance_valid(panel):
		panel.queue_free()
