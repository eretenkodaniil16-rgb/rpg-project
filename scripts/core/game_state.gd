extends Node

signal quest_updated(quest_id: String)
signal inventory_changed(item_id: String)

const SAVE_PATH: String = "user://savegame.json"
const SAVE_VERSION: int = 5
const DEFAULT_PLAYER_POSITION: Vector2 = Vector2(320.0, 360.0)
const QUESTS_PATH: String = "res://data/quests/quests.json"
const ITEMS_PATH: String = "res://data/items/items.json"
const STARTING_QUEST_ID: String = "first_steps"

var story_flags: Dictionary = {}
var player_position: Vector2 = DEFAULT_PLAYER_POSITION
var player_character: PlayerCharacter = PlayerCharacter.new()
var quest_states: Dictionary = {}
var inventory: Dictionary = {}
var input_locked: bool = false

var _quest_definitions: Dictionary = {}
var _item_definitions: Dictionary = {}


func _ready() -> void:
	_ensure_databases_loaded()


func new_game() -> void:
	_ensure_databases_loaded()
	story_flags.clear()
	player_position = DEFAULT_PLAYER_POSITION
	player_character = PlayerCharacter.new()
	quest_states.clear()
	inventory.clear()
	input_locked = false
	start_quest(STARTING_QUEST_ID, false)


func begin_new_game(character: PlayerCharacter) -> void:
	new_game()
	player_character = character


func has_character() -> bool:
	return not player_character.character_name.is_empty() and not player_character.character_class_id.is_empty()


func set_flag(flag_name: String, value: Variant = true) -> void:
	story_flags[flag_name] = value


func get_flag(flag_name: String, default_value: Variant = false) -> Variant:
	return story_flags.get(flag_name, default_value)


func start_quest(quest_id: String, save_after: bool = true) -> bool:
	_ensure_databases_loaded()
	if not _quest_definitions.has(quest_id) or quest_states.has(quest_id):
		return false
	quest_states[quest_id] = {
		"status": "active",
		"stage_index": 0
	}
	quest_updated.emit(quest_id)
	if save_after:
		save_game()
	return true


func report_quest_event(event_id: String) -> Array[String]:
	_ensure_databases_loaded()
	var updated_quests: Array[String] = []
	for quest_id_value: Variant in quest_states.keys():
		var quest_id: String = str(quest_id_value)
		var state_value: Variant = quest_states.get(quest_id, {})
		if not state_value is Dictionary:
			continue
		var state := state_value as Dictionary
		if str(state.get("status", "")) != "active":
			continue
		var definition: Dictionary = get_quest_definition(quest_id)
		var stages_value: Variant = definition.get("stages", [])
		if not stages_value is Array:
			continue
		var stages := stages_value as Array
		var stage_index: int = int(state.get("stage_index", 0))
		if stage_index < 0 or stage_index >= stages.size():
			continue
		var stage_value: Variant = stages[stage_index]
		if not stage_value is Dictionary:
			continue
		if str((stage_value as Dictionary).get("event", "")) != event_id:
			continue

		stage_index += 1
		if stage_index >= stages.size():
			state["status"] = "completed"
			state["stage_index"] = stages.size()
			_grant_quest_rewards(definition)
			set_flag("quest_completed_%s" % quest_id, true)
		else:
			state["stage_index"] = stage_index
		quest_states[quest_id] = state
		updated_quests.append(quest_id)
		quest_updated.emit(quest_id)

	if not updated_quests.is_empty():
		save_game()
	return updated_quests


func get_quest_definition(quest_id: String) -> Dictionary:
	_ensure_databases_loaded()
	var value: Variant = _quest_definitions.get(quest_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_quest_view(quest_id: String) -> Dictionary:
	var definition: Dictionary = get_quest_definition(quest_id)
	if definition.is_empty():
		return {}
	var state_value: Variant = quest_states.get(quest_id, {})
	var state: Dictionary = state_value as Dictionary if state_value is Dictionary else {}
	definition["status"] = str(state.get("status", "inactive"))
	definition["stage_index"] = int(state.get("stage_index", 0))
	return definition


func get_quests_by_status(status: String) -> Array:
	var result: Array = []
	for quest_id_value: Variant in quest_states.keys():
		var quest_id: String = str(quest_id_value)
		var view: Dictionary = get_quest_view(quest_id)
		if str(view.get("status", "")) == status:
			result.append(view)
	return result


func get_current_objective_text() -> String:
	var active_quests: Array = get_quests_by_status("active")
	if active_quests.is_empty():
		return "Свободное исследование."
	var quest_value: Variant = active_quests[0]
	if not quest_value is Dictionary:
		return "Свободное исследование."
	var quest := quest_value as Dictionary
	var stages_value: Variant = quest.get("stages", [])
	if not stages_value is Array:
		return str(quest.get("title", "Активное задание"))
	var stages := stages_value as Array
	var stage_index: int = int(quest.get("stage_index", 0))
	if stage_index < 0 or stage_index >= stages.size() or not stages[stage_index] is Dictionary:
		return str(quest.get("title", "Активное задание"))
	return "Задание: %s — %s" % [
		str(quest.get("title", "Задание")),
		str((stages[stage_index] as Dictionary).get("text", "Продолжить выполнение"))
	]


func add_item(item_id: String, quantity: int = 1, save_after: bool = true) -> int:
	_ensure_databases_loaded()
	if quantity <= 0 or not _item_definitions.has(item_id):
		return get_item_count(item_id)
	var item: Dictionary = get_item_definition(item_id)
	var current: int = get_item_count(item_id)
	var maximum: int = int(item.get("max_stack", 99)) if bool(item.get("stackable", true)) else 1
	var updated: int = clampi(current + quantity, 0, maxi(maximum, 1))
	inventory[item_id] = updated
	inventory_changed.emit(item_id)
	if save_after:
		save_game()
	return updated


func remove_item(item_id: String, quantity: int = 1, save_after: bool = true) -> bool:
	if quantity <= 0 or get_item_count(item_id) < quantity:
		return false
	var updated: int = get_item_count(item_id) - quantity
	if updated <= 0:
		inventory.erase(item_id)
	else:
		inventory[item_id] = updated
	inventory_changed.emit(item_id)
	if save_after:
		save_game()
	return true


func get_item_count(item_id: String) -> int:
	return maxi(int(inventory.get(item_id, 0)), 0)


func has_item(item_id: String, quantity: int = 1) -> bool:
	return get_item_count(item_id) >= maxi(quantity, 1)


func get_item_definition(item_id: String) -> Dictionary:
	_ensure_databases_loaded()
	var value: Variant = _item_definitions.get(item_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_inventory_entries() -> Array:
	var result: Array = []
	for item_id_value: Variant in inventory.keys():
		var item_id: String = str(item_id_value)
		var quantity: int = get_item_count(item_id)
		if quantity <= 0:
			continue
		var item: Dictionary = get_item_definition(item_id)
		if item.is_empty():
			continue
		item["quantity"] = quantity
		result.append(item)
	return result


func has_save() -> bool:
	return FileAccess.file_exists(SAVE_PATH)


func save_game() -> bool:
	var file: FileAccess = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file == null:
		push_error("Не удалось открыть файл сохранения: %s" % SAVE_PATH)
		return false

	var save_data: Dictionary = {
		"version": SAVE_VERSION,
		"story_flags": story_flags,
		"player_position": [player_position.x, player_position.y],
		"player_character": player_character.to_dict(),
		"quest_states": quest_states,
		"inventory": inventory
	}
	file.store_string(JSON.stringify(save_data, "\t"))
	return true


func load_game() -> bool:
	_ensure_databases_loaded()
	if not has_save():
		return false

	var file: FileAccess = FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		push_error("Не удалось прочитать файл сохранения: %s" % SAVE_PATH)
		return false

	var parsed_data: Variant = JSON.parse_string(file.get_as_text())
	if not parsed_data is Dictionary:
		push_error("Файл сохранения повреждён или имеет неверный формат.")
		return false

	var save_data: Dictionary = parsed_data as Dictionary
	var version: int = int(save_data.get("version", 0))
	if version == 1:
		save_data = _migrate_version_1_to_2(save_data)
		version = 2
	if version == 2:
		save_data = _migrate_version_2_to_3(save_data)
		version = 3
	if version == 3:
		save_data = _migrate_version_3_to_4(save_data)
		version = 4
	if version == 4:
		save_data = _migrate_version_4_to_5(save_data)
		version = 5
	if version != SAVE_VERSION:
		push_error("Неподдерживаемая версия сохранения: %d" % version)
		return false

	var loaded_flags: Variant = save_data.get("story_flags", {})
	story_flags = loaded_flags as Dictionary if loaded_flags is Dictionary else {}

	var loaded_position: Variant = save_data.get("player_position", [])
	if loaded_position is Array and loaded_position.size() >= 2:
		player_position = Vector2(float(loaded_position[0]), float(loaded_position[1]))
	else:
		player_position = DEFAULT_PLAYER_POSITION

	var loaded_character: Variant = save_data.get("player_character", {})
	player_character = PlayerCharacter.from_dict(loaded_character as Dictionary) if loaded_character is Dictionary else PlayerCharacter.create_legacy_default()

	var loaded_quests: Variant = save_data.get("quest_states", {})
	quest_states = loaded_quests as Dictionary if loaded_quests is Dictionary else {}
	if quest_states.is_empty():
		start_quest(STARTING_QUEST_ID, false)

	var loaded_inventory: Variant = save_data.get("inventory", {})
	inventory = loaded_inventory as Dictionary if loaded_inventory is Dictionary else {}
	input_locked = false
	return true


func _grant_quest_rewards(definition: Dictionary) -> void:
	var rewards_value: Variant = definition.get("rewards", [])
	if not rewards_value is Array:
		return
	for reward_value: Variant in rewards_value:
		if not reward_value is Dictionary:
			continue
		var reward := reward_value as Dictionary
		add_item(str(reward.get("item_id", "")), int(reward.get("quantity", 1)), false)


func _ensure_databases_loaded() -> void:
	if _quest_definitions.is_empty():
		_quest_definitions = _load_json_dictionary(QUESTS_PATH)
	if _item_definitions.is_empty():
		_item_definitions = _load_json_dictionary(ITEMS_PATH)


func _load_json_dictionary(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Файл игровых данных не найден: %s" % path)
		return {}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть игровые данные: %s" % path)
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Игровые данные имеют неверный формат: %s" % path)
		return {}
	return parsed as Dictionary


func _migrate_version_1_to_2(old_data: Dictionary) -> Dictionary:
	var migrated_data: Dictionary = old_data.duplicate(true)
	migrated_data["version"] = 2
	migrated_data["player_character"] = PlayerCharacter.create_legacy_default().to_dict()
	return migrated_data


func _migrate_version_2_to_3(old_data: Dictionary) -> Dictionary:
	var migrated_data: Dictionary = old_data.duplicate(true)
	migrated_data["version"] = 3
	var character_value: Variant = migrated_data.get("player_character", {})
	var character_data: Dictionary = character_value as Dictionary if character_value is Dictionary else PlayerCharacter.create_legacy_default().to_dict()
	if not character_data.has("appearance_color_hex"):
		character_data["appearance_color_hex"] = PlayerCharacter.DEFAULT_APPEARANCE_COLOR_HEX
	migrated_data["player_character"] = character_data
	return migrated_data


func _migrate_version_3_to_4(old_data: Dictionary) -> Dictionary:
	var migrated_data: Dictionary = old_data.duplicate(true)
	migrated_data["version"] = 4
	migrated_data["quest_states"] = {
		STARTING_QUEST_ID: {
			"status": "active",
			"stage_index": 0
		}
	}
	migrated_data["inventory"] = {}
	return migrated_data


func _migrate_version_4_to_5(old_data: Dictionary) -> Dictionary:
	var migrated_data: Dictionary = old_data.duplicate(true)
	migrated_data["version"] = 5
	var character_value: Variant = migrated_data.get("player_character", {})
	var character_data: Dictionary = character_value as Dictionary if character_value is Dictionary else PlayerCharacter.create_legacy_default().to_dict()
	if not character_data.has("spellbook_spell_ids"):
		character_data["spellbook_spell_ids"] = []
	if not character_data.has("spellbook_initialized"):
		character_data["spellbook_initialized"] = false
	migrated_data["player_character"] = character_data
	return migrated_data
