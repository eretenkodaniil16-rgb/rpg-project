class_name CharacterHubLevelUp
extends CharacterHubInventory

signal level_up_requested

var _level_up_system: LevelUpChoiceSystem = LevelUpChoiceSystem.new()


func _ready() -> void:
	super._ready()
	var state: Node = _game_state()
	if state != null and state.has_signal("experience_gained"):
		var callback := Callable(self, "_on_experience_gained")
		if not state.is_connected("experience_gained", callback):
			state.connect("experience_gained", callback)


func _refresh_character() -> void:
	var state: Node = _game_state()
	if state != null:
		_level_up_system.ensure_migrated(_hero, state)
	super._refresh_character()
	if _hero == null or state == null:
		return
	if not _hero.subclass_name.is_empty():
		_character_box.add_child(_level_choice_label("Подкласс: %s" % _hero.subclass_name))
	if not _hero.level_feat_ids.is_empty():
		var feat_names: Array[String] = []
		for feat_id: String in _hero.level_feat_ids:
			feat_names.append(
				_level_up_system.get_level_choice_option_name("feat", feat_id)
			)
		_character_box.add_child(
			_level_choice_label("Черты, полученные за уровни: %s" % ", ".join(feat_names))
		)
	var pending: bool = _level_up_system.has_pending_transaction(_hero, state)
	if not pending and not ProgressionSystem.can_level_up(_hero):
		return
	_character_box.add_child(HSeparator.new())
	var available_levels: int = ProgressionSystem.pending_level_count(_hero)
	var caption := Label.new()
	caption.text = (
		"Незавершённое повышение сохранено."
		if pending
		else "Доступно уровней: %d. Они применяются последовательно." % available_levels
	)
	caption.add_theme_font_size_override("font_size", 18)
	caption.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_character_box.add_child(caption)
	var button := Button.new()
	button.name = "LevelUpButton"
	button.text = "ПРОДОЛЖИТЬ ПОВЫШЕНИЕ" if pending else "ПОВЫСИТЬ УРОВЕНЬ"
	button.custom_minimum_size = Vector2(0.0, 60.0)
	button.add_theme_font_size_override("font_size", 20)
	button.pressed.connect(_request_level_up)
	_character_box.add_child(button)


func _request_level_up() -> void:
	level_up_requested.emit()


func _on_experience_gained(
	_reward_id: String,
	_amount: int,
	_total_experience: int,
	_label: String
) -> void:
	if visible and _hero != null:
		_refresh_all()


func _level_choice_label(text_value: String) -> Label:
	var label := Label.new()
	label.text = text_value
	label.add_theme_font_size_override("font_size", 18)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return label
