extends SceneTree

const MAIN_MENU_SCENE: String = "res://scenes/menus/main_menu.tscn"
const DISPLAY_DATA_PATHS: Array[String] = [
	"res://data/items/items.json",
	"res://data/classes/classes.json",
	"res://data/races/races.json",
	"res://data/abilities/abilities.json",
	"res://data/abilities/racial_abilities.json",
	"res://data/combat/social_actions.json",
	"res://data/quests/quests.json",
	"res://data/ui/class_selection.json"
]
const DISPLAY_KEYS: Array[String] = [
	"name", "title", "label", "button", "role", "description", "text",
	"speaker_text", "healthy", "wounded", "ability_bonus_description"
]
const NO_ENGLISH_UI_PATHS: Array[String] = [
	"res://scripts/game/game_combat.gd",
	"res://scripts/game/game_racial_planned.gd",
	"res://data/races/races.json"
]

var _latin_regex: RegEx = RegEx.new()
var _dice_regex: RegEx = RegEx.new()
var _errors: Array[String] = []


func _init() -> void:
	_latin_regex.compile("[A-Za-z]")
	_dice_regex.compile("[0-9]+[dD][0-9]+|[dD][0-9]+")
	call_deferred("_run")


func _run() -> void:
	for path: String in DISPLAY_DATA_PATHS:
		_scan_display_data(path)
	_check_main_menu()
	_check_application_names()
	_check_removed_english_ui_terms()
	if not _errors.is_empty():
		for error_text: String in _errors:
			push_error(error_text)
		quit(1)
		return
	print("Russian visible text validation passed.")
	quit(0)


func _scan_display_data(path: String) -> void:
	if not FileAccess.file_exists(path):
		_errors.append("Missing display data file: %s" % path)
		return
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		_errors.append("Cannot open display data file: %s" % path)
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed == null:
		_errors.append("Invalid JSON in display data file: %s" % path)
		return
	_scan_value(parsed, path)


func _scan_value(value: Variant, context: String) -> void:
	if value is Dictionary:
		var dictionary: Dictionary = value as Dictionary
		for key_value: Variant in dictionary.keys():
			var key: String = str(key_value)
			var child: Variant = dictionary[key_value]
			var child_context: String = "%s.%s" % [context, key]
			if key in DISPLAY_KEYS and child is String:
				_check_visible_text(str(child), child_context)
			else:
				_scan_value(child, child_context)
	elif value is Array:
		var values: Array = value as Array
		for index: int in range(values.size()):
			_scan_value(values[index], "%s[%d]" % [context, index])


func _check_visible_text(text_value: String, context: String) -> void:
	var without_dice: String = _dice_regex.sub(text_value, "", true)
	if _latin_regex.search(without_dice) != null:
		_errors.append("Latin letters remain in visible text at %s: %s" % [context, text_value])


func _check_main_menu() -> void:
	var packed: PackedScene = load(MAIN_MENU_SCENE) as PackedScene
	if packed == null:
		_errors.append("Main menu scene failed to load.")
		return
	var menu: Node = packed.instantiate()
	var title: Label = menu.get_node_or_null("CenterContainer/MenuPanel/MarginContainer/VBoxContainer/Title") as Label
	var subtitle: Label = menu.get_node_or_null("CenterContainer/MenuPanel/MarginContainer/VBoxContainer/Subtitle") as Label
	if title == null or subtitle == null:
		_errors.append("Main menu title labels are missing.")
	else:
		_check_visible_text(title.text, "main_menu.title")
		_check_visible_text(subtitle.text, "main_menu.subtitle")
	menu.free()


func _check_application_names() -> void:
	var project_text: String = _read_text("res://project.godot")
	if 'config/name="Хроники странника"' not in project_text:
		_errors.append("Godot application name is not Russian.")
	var export_text: String = _read_text("res://export_presets.cfg")
	if 'package/name="Хроники странника"' not in export_text:
		_errors.append("Android application name is not Russian.")


func _check_removed_english_ui_terms() -> void:
	for path: String in NO_ENGLISH_UI_PATHS:
		var text_value: String = _read_text(path)
		if "RPG PROJECT" in text_value or " HP" in text_value or "HP:" in text_value:
			_errors.append("English visible UI term remains in %s" % path)


func _read_text(path: String) -> String:
	if not FileAccess.file_exists(path):
		_errors.append("Missing text file: %s" % path)
		return ""
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		_errors.append("Cannot open text file: %s" % path)
		return ""
	return file.get_as_text()
