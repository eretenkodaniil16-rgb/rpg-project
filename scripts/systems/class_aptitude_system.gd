class_name ClassAptitudeSystem
extends RefCounted

const CLASSES_PATH: String = "res://data/classes/classes.json"
const ABILITY_SCORE_CAP: int = 20
const ABILITY_IDS: Array[String] = [
	"strength",
	"dexterity",
	"constitution",
	"intelligence",
	"wisdom",
	"charisma"
]

var _classes: Dictionary = {}


func _init() -> void:
	_load_classes()


func get_bonus_options(class_id: String) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var class_data: Dictionary = get_class_definition(class_id)
	var options_value: Variant = class_data.get("ability_bonus_options", [])
	if not options_value is Array:
		return result
	for option_value: Variant in options_value:
		if option_value is Dictionary:
			result.append((option_value as Dictionary).duplicate(true))
	return result


func get_default_option_id(class_id: String) -> String:
	var options: Array[Dictionary] = get_bonus_options(class_id)
	if options.is_empty():
		return ""
	return str(options[0].get("id", ""))


func get_option(class_id: String, option_id: String) -> Dictionary:
	for option_data: Dictionary in get_bonus_options(class_id):
		if str(option_data.get("id", "")) == option_id:
			return option_data
	return {}


func get_bonuses(class_id: String, option_id: String = "") -> Dictionary:
	var resolved_id: String = option_id
	if resolved_id.is_empty():
		resolved_id = get_default_option_id(class_id)
	var option_data: Dictionary = get_option(class_id, resolved_id)
	var bonuses_value: Variant = option_data.get("bonuses", {})
	return (bonuses_value as Dictionary).duplicate(true) if bonuses_value is Dictionary else {}


func get_bonus_for_ability(class_id: String, option_id: String, ability_id: String) -> int:
	return maxi(int(get_bonuses(class_id, option_id).get(ability_id, 0)), 0)


func get_final_score(base_score: int, class_id: String, option_id: String, ability_id: String) -> int:
	return clampi(base_score + get_bonus_for_ability(class_id, option_id, ability_id), 1, ABILITY_SCORE_CAP)


func apply_bonuses(base_scores: Dictionary, class_id: String, option_id: String = "") -> Dictionary:
	var result: Dictionary = {}
	for ability_id: String in ABILITY_IDS:
		var base_score: int = clampi(int(base_scores.get(ability_id, 10)), 1, 30)
		result[ability_id] = get_final_score(base_score, class_id, option_id, ability_id)
	return result


func is_valid_option(class_id: String, option_id: String) -> bool:
	return not get_option(class_id, option_id).is_empty()


func get_class_definition(class_id: String) -> Dictionary:
	var value: Variant = _classes.get(class_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func _load_classes() -> void:
	_classes.clear()
	if not FileAccess.file_exists(CLASSES_PATH):
		push_error("Файл классов не найден: %s" % CLASSES_PATH)
		return
	var file: FileAccess = FileAccess.open(CLASSES_PATH, FileAccess.READ)
	if file == null:
		push_error("Не удалось открыть файл классов для бонусов характеристик.")
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("Файл классов содержит некорректный JSON.")
		return
	var classes_value: Variant = (parsed as Dictionary).get("classes", [])
	if not classes_value is Array:
		return
	for class_value: Variant in classes_value:
		if class_value is Dictionary:
			var class_data: Dictionary = class_value as Dictionary
			_classes[str(class_data.get("id", ""))] = class_data
