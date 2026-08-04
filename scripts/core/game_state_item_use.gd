extends "res://scripts/core/game_state_world_snapshot.gd"

const ITEM_USE_DEFINITIONS_PATH: String = "res://data/items/item_use_definitions.json"

var _item_use_definitions_loaded: bool = false


func _ready() -> void:
	super._ready()
	_merge_item_use_definitions()


func new_game() -> void:
	_merge_item_use_definitions()
	super.new_game()


func get_item_definition(item_id: String) -> Dictionary:
	_merge_item_use_definitions()
	return super.get_item_definition(item_id)


func add_item(item_id: String, quantity: int = 1, save_after: bool = true) -> int:
	_merge_item_use_definitions()
	return super.add_item(item_id, quantity, save_after)


func reload_item_use_definitions_for_testing() -> void:
	_item_use_definitions_loaded = false
	_merge_item_use_definitions()


func _merge_item_use_definitions() -> void:
	if _item_use_definitions_loaded:
		return
	_ensure_databases_loaded()
	var file: FileAccess = FileAccess.open(ITEM_USE_DEFINITIONS_PATH, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть каталог использования предметов: %s" % ITEM_USE_DEFINITIONS_PATH)
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Каталог использования предметов должен содержать JSON-объект.")
		return
	for key_value: Variant in (parsed as Dictionary).keys():
		var item_id: String = str(key_value)
		var extension_value: Variant = (parsed as Dictionary).get(item_id, {})
		if item_id.is_empty() or not extension_value is Dictionary:
			continue
		var merged: Dictionary = {}
		var base_value: Variant = _item_definitions.get(item_id, {})
		if base_value is Dictionary:
			merged = (base_value as Dictionary).duplicate(true)
		merged.merge((extension_value as Dictionary).duplicate(true), true)
		_item_definitions[item_id] = merged
	_item_use_definitions_loaded = true
