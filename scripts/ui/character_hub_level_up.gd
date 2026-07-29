class_name CharacterHubLevelUp
extends CharacterHubInventory

signal level_up_requested

var _level_up_system: LevelUpSystem = LevelUpSystem.new()


func _refresh_character() -> void:
	var state: Node = _game_state()
	if state != null:
		_level_up_system.ensure_migrated(_hero, state)
	super._refresh_character()
	if _hero == null or state == null:
		return
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
