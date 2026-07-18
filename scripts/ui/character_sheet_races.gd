extends "res://scripts/ui/character_sheet.gd"


func _refresh() -> void:
	super._refresh()
	if _character == null:
		return
	_identity.text = "%s — %s, %s, уровень %d" % [
		_character.character_name,
		_character.race_name,
		_character.character_class_name,
		_character.level
	]
	var vision_text: String = "нет" if _character.darkvision_feet <= 0 else "%d футов" % _character.darkvision_feet
	_summary.text += "\nРазмер: %s     Скорость: %d футов     Тёмное зрение: %s" % [
		"маленький" if _character.size_category == "small" else "средний",
		_character.base_speed_feet,
		vision_text
	]
