extends "res://scripts/ui/dialogue_ui_base.gd"

const CHECK_POPUP_SCENE: PackedScene = preload("res://scenes/ui/skill_check_popup.tscn")
const VISUAL_CONTROLLER_SCRIPT: Script = preload("res://scripts/ui/dialogue_visual_controller.gd")

var _check_system: SkillCheckSystem = SkillCheckSystem.new()
var _check_popup: SkillCheckPopup
var _pending_checked_choice: Dictionary = {}
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
	if _check_popup != null:
		_check_popup.hide()
	super.start_dialogue(dialogue_data, dialogue_target)

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
		var check_data := check_value as Dictionary
		var result := _check_system.perform_check(GameState.player_character, str(check_data.get("ability", "")), int(check_data.get("difficulty", 10)), int(check_data.get("bonus", 0)))
		get_tree().call_group("dice_presenter", "show_d20_roll", GameState.player_character.character_name, "Проверка: %s" % result.ability_name, result.natural_roll, result.total, result.success, result.natural_roll, 0)
		_pending_checked_choice = choice_data.duplicate(true)
		_clear_choices()
		_check_popup.show_result(result)
		return
	super._on_choice_pressed(choice_data)

func _on_check_dismissed(result: SkillCheckResult) -> void:
	var branch_key: String = "success" if result.success else "failure"
	var branch_value: Variant = _pending_checked_choice.get(branch_key, {})
	var branch: Dictionary = branch_value as Dictionary if branch_value is Dictionary else {}
	_pending_checked_choice.clear()
	if branch.is_empty():
		branch = {"response": "Проверка завершена."}
	super._on_choice_pressed(branch)

func _close_dialogue() -> void:
	_pending_checked_choice.clear()
	if _check_popup != null:
		_check_popup.hide()
	super._close_dialogue()

func get_visual_controller_for_testing() -> DialogueVisualController:
	return _visual_controller
