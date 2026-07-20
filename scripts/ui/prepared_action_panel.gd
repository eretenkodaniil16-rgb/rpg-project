class_name PreparedActionPanel
extends AbilityPanel

const PREPARED_ABILITY_FLAG: String = "prepared_ability_id"

var _prepared_ability_id: String = ""


func refresh() -> void:
	if _character == null:
		return
	_prepared_ability_id = _resolve_prepared_ability_id()
	var ability: Dictionary = _class_data.get_ability_definition(_prepared_ability_id)
	if ability.is_empty():
		_ability_button.text = "НЕТ ПОДГОТОВЛЕННОГО ДЕЙСТВИЯ"
		_ability_button.disabled = true
		_resource_label.text = "Откройте: Персонаж → Заклинания и способности"
		_message_label.text = "Подготовьте активное заклинание или способность"
		return
	_ability_button.text = str(ability.get("button", ability.get("name", "ПРИМЕНИТЬ"))).to_upper()
	_ability_button.disabled = str(ability.get("kind", "")) != "active"
	_resource_label.text = "%s · %s" % [
		str(ability.get("name", "Подготовленное действие")),
		_class_data.get_resource_text(_character, ability)
	]
	_ability_button.tooltip_text = str(ability.get("description", ""))
	_message_label.text = "Подготовленное заклинание или способность"


func get_prepared_ability_id() -> String:
	return _prepared_ability_id


func _on_ability_pressed() -> void:
	if _character == null or GameState.input_locked:
		return
	_prepared_ability_id = _resolve_prepared_ability_id()
	if _prepared_ability_id.is_empty():
		set_message("Сначала подготовьте заклинание или способность.", false)
		return
	ability_requested.emit(_prepared_ability_id)


func _resolve_prepared_ability_id() -> String:
	var saved_id: String = str(GameState.get_flag(PREPARED_ABILITY_FLAG, ""))
	if _is_preparable(saved_id):
		return saved_id
	var signature_id: String = _character.signature_ability_id
	if _is_preparable(signature_id):
		_store_prepared_id(signature_id)
		return signature_id
	for ability_id: String in _candidate_ability_ids():
		if _is_preparable(ability_id):
			_store_prepared_id(ability_id)
			return ability_id
	return ""


func _candidate_ability_ids() -> Array[String]:
	var result: Array[String] = []
	for ability_id: String in _character.known_features:
		if ability_id not in result:
			result.append(ability_id)
	if not _character.racial_ability_id.is_empty() and _character.racial_ability_id not in result:
		result.append(_character.racial_ability_id)
	if not _character.signature_ability_id.is_empty() and _character.signature_ability_id not in result:
		result.append(_character.signature_ability_id)
	return result


func _is_preparable(ability_id: String) -> bool:
	if ability_id.is_empty():
		return false
	var ability: Dictionary = _class_data.get_ability_definition(ability_id)
	return not ability.is_empty() and str(ability.get("kind", "")) == "active"


func _store_prepared_id(ability_id: String) -> void:
	if str(GameState.get_flag(PREPARED_ABILITY_FLAG, "")) == ability_id:
		return
	GameState.set_flag(PREPARED_ABILITY_FLAG, ability_id)
	GameState.save_game()
