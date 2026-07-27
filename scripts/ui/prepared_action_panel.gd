class_name PreparedActionPanel
extends AbilityPanel

const PREPARED_ABILITY_FLAG: String = "prepared_ability_id"

var _prepared_ability_id: String = ""
var _spellcasting: SpellcastingSystem = SpellcastingSystem.new()


func refresh() -> void:
	if _character == null:
		return
	_spellcasting.ensure_character(_character, false)
	_prepared_ability_id = _resolve_prepared_ability_id()
	var ability: Dictionary = _class_data.get_ability_definition(_prepared_ability_id)
	if ability.is_empty():
		_ability_button.text = "НЕТ ПОДГОТОВЛЕННОГО ДЕЙСТВИЯ"
		_ability_button.disabled = true
		_resource_label.text = "Откройте: Персонаж → Заклинания и способности"
		_message_label.text = "Назначьте активное заклинание или способность"
		return
	_ability_button.text = str(ability.get("button", ability.get("name", "ПРИМЕНИТЬ"))).to_upper()
	_ability_button.disabled = str(ability.get("kind", "")) != "active" or not _is_preparable(_prepared_ability_id)
	_resource_label.text = "%s · %s" % [
		str(ability.get("name", "Подготовленное действие")),
		_resource_text(ability)
	]
	_ability_button.tooltip_text = str(ability.get("description", ""))
	_message_label.text = "Быстрая кнопка заклинания или способности"


func get_prepared_ability_id() -> String:
	return _prepared_ability_id


func _on_ability_pressed() -> void:
	var state: Node = _game_state()
	if _character == null or (state != null and bool(state.get("input_locked"))):
		return
	_prepared_ability_id = _resolve_prepared_ability_id()
	if _prepared_ability_id.is_empty():
		set_message("Сначала назначьте заклинание или способность на быструю кнопку.", false)
		return
	ability_requested.emit(_prepared_ability_id)


func _resolve_prepared_ability_id() -> String:
	var state: Node = _game_state()
	var saved_id: String = str(state.call("get_flag", PREPARED_ABILITY_FLAG, "")) if state != null else ""
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
	if ability.is_empty() or str(ability.get("kind", "")) != "active":
		return false
	if _spellcasting.is_spell_definition(ability):
		return _spellcasting.is_prepared(_character, ability_id)
	return true


func _resource_text(ability: Dictionary) -> String:
	if not _spellcasting.is_spell_definition(ability):
		return _class_data.get_resource_text(_character, ability)
	var level: int = maxi(int(ability.get("spell_level", 0)), 0)
	if level == 0:
		return "Без ячейки"
	var resource_key: String = _spellcasting.active_resource_key(_character, ability)
	return "%d / %d" % [_character.get_resource(resource_key), _character.get_resource_maximum(resource_key)]


func _store_prepared_id(ability_id: String) -> void:
	var state: Node = _game_state()
	if state == null or str(state.call("get_flag", PREPARED_ABILITY_FLAG, "")) == ability_id:
		return
	state.call("set_flag", PREPARED_ABILITY_FLAG, ability_id)
	state.call("save_game")


func _game_state() -> Node:
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	return tree.root.get_node_or_null("GameState") if tree != null else null
