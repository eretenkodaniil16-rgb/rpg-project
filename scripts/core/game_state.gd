extends Node

const SAVE_PATH: String = "user://savegame.json"
const SAVE_VERSION: int = 1
const DEFAULT_PLAYER_POSITION: Vector2 = Vector2(320.0, 360.0)

var story_flags: Dictionary = {}
var player_position: Vector2 = DEFAULT_PLAYER_POSITION
var input_locked: bool = false


func new_game() -> void:
	story_flags.clear()
	player_position = DEFAULT_PLAYER_POSITION
	input_locked = false


func set_flag(flag_name: String, value: Variant = true) -> void:
	story_flags[flag_name] = value


func get_flag(flag_name: String, default_value: Variant = false) -> Variant:
	return story_flags.get(flag_name, default_value)


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
		"player_position": [player_position.x, player_position.y]
	}
	file.store_string(JSON.stringify(save_data, "\t"))
	return true


func load_game() -> bool:
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

	input_locked = false
	return true
