extends SceneTree

const SYSTEM_SCRIPT: Script = preload("res://scripts/systems/save_slot_system.gd")


func _init() -> void:
	var suffix: String = str(Time.get_ticks_usec())
	var directory: String = "user://save_slot_system_test_%s" % suffix
	var legacy_path: String = "user://save_slot_system_legacy_%s.json" % suffix
	var system: SaveSlotSystem = SYSTEM_SCRIPT.new(directory, legacy_path) as SaveSlotSystem
	var manual_data: Dictionary = _sample_save("Ручной герой", 111, 3)
	var autosave_data: Dictionary = _sample_save("Автогерой", 222, 4)

	if not system.write_manual_slot(2, manual_data):
		_fail("Manual slot could not be written.")
		return
	if not system.has_manual_slot(2):
		_fail("Written manual slot was not detected.")
		return
	var manual_entry: Dictionary = system.list_manual_slots()[1]
	if not bool(manual_entry.get("exists", false)) or str(manual_entry.get("character_name", "")) != "Ручной герой":
		_fail("Manual slot metadata was not restored.")
		return
	if system.newest_manual_slot_id() != 2:
		_fail("Newest manual slot selection is incorrect.")
		return

	if not system.write_autosave(autosave_data):
		_fail("Autosave could not be written.")
		return
	var autosave_entry: Dictionary = system.get_autosave_entry()
	if not bool(autosave_entry.get("exists", false)) or int(autosave_entry.get("saved_at_unix", 0)) != 222:
		_fail("Autosave metadata was not restored.")
		return
	if not system.has_any_save():
		_fail("Save system did not report existing saves.")
		return

	var legacy_file: FileAccess = FileAccess.open(legacy_path, FileAccess.WRITE)
	if legacy_file == null:
		_fail("Legacy test file could not be created.")
		return
	legacy_file.store_string(JSON.stringify(_sample_save("Старый герой", 333, 5)))
	var legacy_directory: String = "user://save_slot_legacy_import_%s" % suffix
	var legacy_system: SaveSlotSystem = SYSTEM_SCRIPT.new(legacy_directory, legacy_path) as SaveSlotSystem
	if legacy_system.import_legacy_to_manual_slot() != 1:
		_fail("Legacy save was not imported into slot 1.")
		return
	if str(legacy_system.read_manual_slot(1).get("metadata", {}).get("character_name", "")) != "Старый герой":
		_fail("Imported legacy save content is incorrect.")
		return

	_cleanup_system(system)
	_cleanup_system(legacy_system)
	if FileAccess.file_exists(legacy_path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(legacy_path))
	print("Manual save slots, autosave metadata, deletion and legacy import passed.")
	quit(0)


func _sample_save(character_name: String, timestamp: int, level: int) -> Dictionary:
	return {
		"version": 6,
		"metadata": {
			"saved_at_unix": timestamp,
			"character_name": character_name,
			"character_class_name": "Воин",
			"level": level,
			"current_health": 21,
			"maximum_health": 30,
			"location_label": "Тестовая комната"
		},
		"player_character": {
			"character_name": character_name,
			"character_class_name": "Воин",
			"level": level
		}
	}


func _cleanup_system(system: SaveSlotSystem) -> void:
	for slot_id: int in range(1, SaveSlotSystem.MANUAL_SLOT_COUNT + 1):
		system.delete_manual_slot(slot_id)
	system.delete_autosave()
	var directory_path: String = ProjectSettings.globalize_path(system.save_directory)
	if DirAccess.dir_exists_absolute(directory_path):
		DirAccess.remove_absolute(directory_path)


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
