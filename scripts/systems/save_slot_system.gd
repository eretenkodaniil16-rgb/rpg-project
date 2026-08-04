class_name SaveSlotSystem
extends RefCounted

const DEFAULT_DIRECTORY: String = "user://save_slots"
const DEFAULT_LEGACY_PATH: String = "user://savegame.json"
const MANUAL_SLOT_COUNT: int = 5
const AUTOSAVE_ID: String = "autosave"

var save_directory: String = DEFAULT_DIRECTORY
var legacy_path: String = DEFAULT_LEGACY_PATH


func _init(directory: String = DEFAULT_DIRECTORY, legacy_save_path: String = DEFAULT_LEGACY_PATH) -> void:
	save_directory = directory.trim_suffix("/")
	legacy_path = legacy_save_path


func ensure_directory() -> bool:
	var absolute_directory: String = ProjectSettings.globalize_path(save_directory)
	var error: Error = DirAccess.make_dir_recursive_absolute(absolute_directory)
	return error == OK or error == ERR_ALREADY_EXISTS


func manual_slot_path(slot_id: int) -> String:
	return "%s/manual_%02d.json" % [save_directory, clampi(slot_id, 1, MANUAL_SLOT_COUNT)]


func autosave_path() -> String:
	return "%s/autosave.json" % save_directory


func write_manual_slot(slot_id: int, save_data: Dictionary) -> bool:
	if slot_id < 1 or slot_id > MANUAL_SLOT_COUNT:
		return false
	return _write_dictionary(manual_slot_path(slot_id), save_data)


func write_autosave(save_data: Dictionary) -> bool:
	return _write_dictionary(autosave_path(), save_data)


func read_manual_slot(slot_id: int) -> Dictionary:
	if slot_id < 1 or slot_id > MANUAL_SLOT_COUNT:
		return {}
	return _read_dictionary(manual_slot_path(slot_id))


func read_autosave() -> Dictionary:
	return _read_dictionary(autosave_path())


func has_manual_slot(slot_id: int) -> bool:
	return slot_id >= 1 and slot_id <= MANUAL_SLOT_COUNT and FileAccess.file_exists(manual_slot_path(slot_id))


func has_autosave() -> bool:
	return FileAccess.file_exists(autosave_path())


func has_any_save() -> bool:
	if has_autosave():
		return true
	for slot_id: int in range(1, MANUAL_SLOT_COUNT + 1):
		if has_manual_slot(slot_id):
			return true
	return FileAccess.file_exists(legacy_path)


func list_manual_slots() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for slot_id: int in range(1, MANUAL_SLOT_COUNT + 1):
		var data: Dictionary = read_manual_slot(slot_id)
		result.append(_entry_from_data("manual", slot_id, data, has_manual_slot(slot_id)))
	return result


func get_autosave_entry() -> Dictionary:
	var data: Dictionary = read_autosave()
	return _entry_from_data(AUTOSAVE_ID, 0, data, has_autosave())


func newest_manual_slot_id() -> int:
	var newest_slot_id: int = -1
	var newest_timestamp: int = -1
	for entry: Dictionary in list_manual_slots():
		if not bool(entry.get("exists", false)):
			continue
		var timestamp: int = int(entry.get("saved_at_unix", 0))
		if timestamp >= newest_timestamp:
			newest_timestamp = timestamp
			newest_slot_id = int(entry.get("slot_id", -1))
	return newest_slot_id


func delete_manual_slot(slot_id: int) -> bool:
	if not has_manual_slot(slot_id):
		return false
	return DirAccess.remove_absolute(ProjectSettings.globalize_path(manual_slot_path(slot_id))) == OK


func delete_autosave() -> bool:
	if not has_autosave():
		return true
	return DirAccess.remove_absolute(ProjectSettings.globalize_path(autosave_path())) == OK


func import_legacy_to_manual_slot(save_data_transform: Callable = Callable()) -> int:
	if not FileAccess.file_exists(legacy_path):
		return -1
	if newest_manual_slot_id() > 0 or has_autosave():
		return -1
	var legacy_data: Dictionary = _read_dictionary(legacy_path)
	if legacy_data.is_empty():
		return -1
	if save_data_transform.is_valid():
		var transformed: Variant = save_data_transform.call(legacy_data)
		if transformed is Dictionary:
			legacy_data = transformed as Dictionary
	if not write_manual_slot(1, legacy_data):
		return -1
	return 1


func _write_dictionary(path: String, value: Dictionary) -> bool:
	if not ensure_directory():
		push_error("Не удалось создать каталог сохранений: %s" % save_directory)
		return false
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("Не удалось открыть файл сохранения: %s" % path)
		return false
	file.store_string(JSON.stringify(value, "\t"))
	return true


func _read_dictionary(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	return (parsed as Dictionary).duplicate(true) if parsed is Dictionary else {}


func _entry_from_data(kind: String, slot_id: int, data: Dictionary, exists: bool) -> Dictionary:
	var metadata_value: Variant = data.get("metadata", {})
	var metadata: Dictionary = metadata_value as Dictionary if metadata_value is Dictionary else {}
	var character_value: Variant = data.get("player_character", {})
	var character: Dictionary = character_value as Dictionary if character_value is Dictionary else {}
	return {
		"kind": kind,
		"slot_id": slot_id,
		"exists": exists and not data.is_empty(),
		"saved_at_unix": int(metadata.get("saved_at_unix", 0)),
		"character_name": str(metadata.get("character_name", character.get("character_name", ""))),
		"character_class_name": str(metadata.get("character_class_name", character.get("character_class_name", ""))),
		"level": int(metadata.get("level", character.get("level", 1))),
		"current_health": int(metadata.get("current_health", character.get("current_health", 0))),
		"maximum_health": int(metadata.get("maximum_health", character.get("maximum_health", 0))),
		"location_label": str(metadata.get("location_label", "Караульный пост")),
		"source_manual_slot_id": int(metadata.get("source_manual_slot_id", -1))
	}
