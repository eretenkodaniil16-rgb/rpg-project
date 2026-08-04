extends "res://scripts/ui/dialogue_ui_base.gd"

const CHECK_POPUP_SCENE: PackedScene = preload("res://scenes/ui/skill_check_popup.tscn")
const VISUAL_CONTROLLER_SCRIPT: Script = preload("res://scripts/ui/dialogue_visual_controller.gd")
const CHECK_ATTEMPTS_FLAG: String = "dialogue_check_attempts_v1"

var _check_system: SkillCheckSystem = SkillCheckSystem.new()
var _class_data: ClassDataSystem = ClassDataSystem.new()
var _check_popup: SkillCheckPopup
var _pending_checked_choice: Dictionary = {}
var _pending_check_attempt_key: String = ""
var _visual_controller: DialogueVisualController


func _ready() -> void:
	_check_popup = CHECK_POPUP_SCENE.instantiate() as SkillCheckPopup
	_check_popup.name = "SkillCheckPopup"
	_check_popup.dismissed.connect(_on_check_dismissed)
	add_child(_check_popup)
	_visual_controller = VISUAL_CONTROLLER_SCRIPT.new() as DialogueVisualController
	_visual_controller.name = "DialogueVisualController"
	add_child(_visual_controller)
	_visual_controller.setup(self)


func start_dialogue(dialogue_data: Dictionary, dialogue_target: Node = null) -> void:
	_pending_checked_choice.clear()
	_pending_check_attempt_key = ""
	if _check_popup != null:
		_check_popup.hide()
	var filtered_data: Dictionary = _without_attempted_checks(dialogue_data)
	super.start_dialogue(filtered_data, dialogue_target)


func _unhandled_input(event: InputEvent) -> void:
	if _check_popup != null and _check_popup.visible:
		return
	super._unhandled_input(event)


func _on_choice_pressed(choice_data: Dictionary) -> void:
	var runtime_action: String = str(choice_data.get("runtime_action", ""))
	if not runtime_action.is_empty():
		super._on_choice_pressed(choice_data)
		return
	var check_value: Variant = choice_data.get("check", {})
	if check_value is Dictionary and not (check_value as Dictionary).is_empty():
		var attempt_key: String = _check_attempt_key(_dialogue_id, choice_data)
		if _check_was_attempted(attempt_key):
			text_label.text = "Эта проверка уже была предпринята. Повторный бросок в этом прохождении невозможен."
			_clear_choices()
			if _has_attack_target():
				_add_attack_button()
			_add_close_button()
			return
		_mark_check_attempt(attempt_key, choice_data, "pending")
		var check_data := check_value as Dictionary
		var skill_id: String = str(check_data.get("skill", ""))
		var ability_id: String = str(check_data.get("ability", ""))
		if not skill_id.is_empty():
			ability_id = GameState.player_character.get_skill_ability(skill_id)
		var armor_disadvantage: bool = _class_data.has_untrained_armor_d20_disadvantage(GameState.player_character, ability_id)
		var result: SkillCheckResult
		if skill_id.is_empty():
			result = _check_system.perform_check(
				GameState.player_character,
				ability_id,
				int(check_data.get("difficulty", 10)),
				int(check_data.get("bonus", 0)),
				0,
				0,
				0,
				armor_disadvantage
			)
		else:
			result = _check_system.perform_skill_check(
				GameState.player_character,
				skill_id,
				int(check_data.get("difficulty", 10)),
				int(check_data.get("bonus", 0)),
				0,
				0,
				0,
				armor_disadvantage
			)
		get_tree().call_group("dice_presenter", "show_d20_roll", GameState.player_character.character_name, "Проверка: %s" % result.ability_name, result.natural_roll, result.total, result.success, result.natural_roll, 0)
		_pending_checked_choice = choice_data.duplicate(true)
		_pending_check_attempt_key = attempt_key
		_clear_choices()
		_check_popup.show_result(result)
		return
	super._on_choice_pressed(choice_data)


func _on_check_dismissed(result: SkillCheckResult) -> void:
	if not _pending_check_attempt_key.is_empty():
		_update_check_attempt_result(_pending_check_attempt_key, result)
	var branch_key: String = "success" if result.success else "failure"
	var branch_value: Variant = _pending_checked_choice.get(branch_key, {})
	var branch: Dictionary = branch_value as Dictionary if branch_value is Dictionary else {}
	_pending_checked_choice.clear()
	_pending_check_attempt_key = ""
	if branch.is_empty():
		branch = {"response": "Проверка завершена."}
	super._on_choice_pressed(branch)


func _close_dialogue() -> void:
	_pending_checked_choice.clear()
	_pending_check_attempt_key = ""
	if _check_popup != null:
		_check_popup.hide()
	super._close_dialogue()


func get_visual_controller_for_testing() -> DialogueVisualController:
	return _visual_controller


func get_available_checked_choice_count_for_testing() -> int:
	var count: int = 0
	for child: Node in choices_container.get_children():
		if child is Button and "[" in (child as Button).text:
			count += 1
	return count


func has_check_attempt_for_testing(dialogue_id: String, check_id: String) -> bool:
	return _check_was_attempted("%s:%s" % [dialogue_id, check_id])


func _without_attempted_checks(dialogue_data: Dictionary) -> Dictionary:
	var result: Dictionary = dialogue_data.duplicate(true)
	var dialogue_id: String = str(result.get("id", ""))
	var filtered_choices: Array = []
	var choices_value: Variant = result.get("choices", [])
	if choices_value is Array:
		for choice_value: Variant in choices_value as Array:
			if not choice_value is Dictionary:
				continue
			var choice: Dictionary = choice_value as Dictionary
			var check_value: Variant = choice.get("check", {})
			if check_value is Dictionary and not (check_value as Dictionary).is_empty():
				var key: String = _check_attempt_key(dialogue_id, choice)
				if _check_was_attempted(key):
					continue
			filtered_choices.append(choice.duplicate(true))
	result["choices"] = filtered_choices
	return result


func _check_attempt_key(dialogue_id: String, choice_data: Dictionary) -> String:
	var check_id: String = str(choice_data.get("check_id", "")).strip_edges()
	if not check_id.is_empty():
		return "%s:%s" % [dialogue_id, check_id]
	var check_value: Variant = choice_data.get("check", {})
	var check: Dictionary = check_value as Dictionary if check_value is Dictionary else {}
	return "%s:%s:%s:%d:%s" % [
		dialogue_id,
		str(check.get("skill", "")),
		str(check.get("ability", "")),
		int(check.get("difficulty", 10)),
		str(choice_data.get("text", ""))
	]


func _check_was_attempted(attempt_key: String) -> bool:
	if attempt_key.is_empty():
		return false
	var registry_value: Variant = GameState.get_flag(CHECK_ATTEMPTS_FLAG, {})
	return registry_value is Dictionary and (registry_value as Dictionary).has(attempt_key)


func _mark_check_attempt(attempt_key: String, choice_data: Dictionary, outcome: String) -> void:
	if attempt_key.is_empty():
		return
	var registry_value: Variant = GameState.get_flag(CHECK_ATTEMPTS_FLAG, {})
	var registry: Dictionary = registry_value as Dictionary if registry_value is Dictionary else {}
	registry[attempt_key] = {
		"attempted": true,
		"outcome": outcome,
		"choice_text": str(choice_data.get("text", "")),
		"attempted_at_unix": int(Time.get_unix_time_from_system())
	}
	GameState.set_flag(CHECK_ATTEMPTS_FLAG, registry)
	GameState.save_game()


func _update_check_attempt_result(attempt_key: String, result: SkillCheckResult) -> void:
	var registry_value: Variant = GameState.get_flag(CHECK_ATTEMPTS_FLAG, {})
	if not registry_value is Dictionary:
		return
	var registry: Dictionary = registry_value as Dictionary
	var record_value: Variant = registry.get(attempt_key, {})
	var record: Dictionary = record_value as Dictionary if record_value is Dictionary else {}
	record["outcome"] = "success" if result.success else "failure"
	record["natural_roll"] = result.natural_roll
	record["total"] = result.total
	registry[attempt_key] = record
	GameState.set_flag(CHECK_ATTEMPTS_FLAG, registry)
