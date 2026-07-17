extends "res://scripts/game/game_base.gd"

const CHARACTER_SHEET_SCENE: PackedScene = preload("res://scenes/ui/character_sheet.tscn")
const QUEST_JOURNAL_SCENE: PackedScene = preload("res://scenes/ui/quest_journal.tscn")
const INVENTORY_PANEL_SCENE: PackedScene = preload("res://scenes/ui/inventory_panel.tscn")
const ATTACK_RESULT_SCENE: PackedScene = preload("res://scenes/ui/attack_result_popup.tscn")
const TRAINING_DUMMY_SCENE: PackedScene = preload("res://scenes/game/training_dummy.tscn")
const ABILITY_PANEL_SCENE: PackedScene = preload("res://scenes/ui/ability_panel.tscn")

var _character_button: Button
var _quest_button: Button
var _inventory_button: Button
var _character_sheet: CharacterSheet
var _quest_journal: QuestJournal
var _inventory_panel: InventoryPanel
var _attack_popup: AttackResultPopup
var _training_dummy: TrainingDummy
var _ability_panel: AbilityPanel
var _class_data: ClassDataSystem = ClassDataSystem.new()
var _ability_system: ClassAbilitySystem = ClassAbilitySystem.new()


func _ready() -> void:
	_class_data.ensure_starting_loadout(GameState.player_character)
	super._ready()
	_build_player_menus()
	_build_combat_training()
	_build_ability_ui()
	_connect_progress_signals()
	_update_status()


func _unhandled_input(event: InputEvent) -> void:
	if _any_overlay_visible():
		return
	if event is InputEventKey:
		var key_event := event as InputEventKey
		if key_event.pressed and not key_event.echo:
			match key_event.keycode:
				KEY_C:
					_open_character_sheet()
				KEY_J:
					_open_quest_journal()
				KEY_I:
					_open_inventory()
				_:
					super._unhandled_input(event)
					return
			get_viewport().set_input_as_handled()
			return
	super._unhandled_input(event)


func _build_player_menus() -> void:
	var interface: CanvasLayer = $Interface
	help_label.offset_right = 580.0
	status_label.offset_right = 580.0
	_character_button = _create_top_button("CharacterButton", "ПЕРСОНАЖ", -690.0, -520.0)
	_character_button.pressed.connect(_open_character_sheet)
	interface.add_child(_character_button)
	_quest_button = _create_top_button("QuestButton", "ЗАДАНИЯ", -510.0, -350.0)
	_quest_button.pressed.connect(_open_quest_journal)
	interface.add_child(_quest_button)
	_inventory_button = _create_top_button("InventoryButton", "ИНВЕНТАРЬ", -340.0, -190.0)
	_inventory_button.pressed.connect(_open_inventory)
	interface.add_child(_inventory_button)
	_character_sheet = CHARACTER_SHEET_SCENE.instantiate() as CharacterSheet
	_character_sheet.name = "CharacterSheet"
	interface.add_child(_character_sheet)
	_quest_journal = QUEST_JOURNAL_SCENE.instantiate() as QuestJournal
	_quest_journal.name = "QuestJournal"
	interface.add_child(_quest_journal)
	_inventory_panel = INVENTORY_PANEL_SCENE.instantiate() as InventoryPanel
	_inventory_panel.name = "InventoryPanel"
	interface.add_child(_inventory_panel)


func _create_top_button(node_name: String, label: String, left: float, right: float) -> Button:
	var button := Button.new()
	button.name = node_name
	button.text = label
	button.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	button.offset_left = left
	button.offset_top = 20.0
	button.offset_right = right
	button.offset_bottom = 78.0
	button.add_theme_font_size_override("font_size", 16)
	return button


func _build_combat_training() -> void:
	var interface: CanvasLayer = $Interface
	_attack_popup = ATTACK_RESULT_SCENE.instantiate() as AttackResultPopup
	_attack_popup.name = "AttackResultPopup"
	interface.add_child(_attack_popup)
	_training_dummy = TRAINING_DUMMY_SCENE.instantiate() as TrainingDummy
	_training_dummy.name = "TrainingDummy"
	_training_dummy.position = Vector2(1080.0, 470.0)
	add_child(_training_dummy)


func _build_ability_ui() -> void:
	var interface: CanvasLayer = $Interface
	_ability_panel = ABILITY_PANEL_SCENE.instantiate() as AbilityPanel
	_ability_panel.name = "AbilityPanel"
	_ability_panel.ability_requested.connect(_on_ability_requested)
	_ability_panel.rest_requested.connect(_on_rest_requested)
	interface.add_child(_ability_panel)
	_ability_panel.bind_character(GameState.player_character)


func _connect_progress_signals() -> void:
	if not GameState.quest_updated.is_connected(_on_quest_updated):
		GameState.quest_updated.connect(_on_quest_updated)
	if not GameState.inventory_changed.is_connected(_on_inventory_changed):
		GameState.inventory_changed.connect(_on_inventory_changed)


func _open_character_sheet() -> void:
	if GameState.input_locked or _character_sheet == null:
		return
	_character_sheet.open_sheet(GameState.player_character)


func _open_quest_journal() -> void:
	if GameState.input_locked or _quest_journal == null:
		return
	_quest_journal.open_journal()


func _open_inventory() -> void:
	if GameState.input_locked or _inventory_panel == null:
		return
	_inventory_panel.open_inventory()


func _any_overlay_visible() -> bool:
	return (
		(_character_sheet != null and _character_sheet.visible)
		or (_quest_journal != null and _quest_journal.visible)
		or (_inventory_panel != null and _inventory_panel.visible)
		or (_attack_popup != null and _attack_popup.visible)
	)


func _on_ability_requested(ability_id: String) -> void:
	if GameState.input_locked:
		return
	var ability: Dictionary = _class_data.get_ability_definition(ability_id)
	if ability.is_empty():
		_ability_panel.set_message("Способность не найдена.", false)
		return
	var target_type: String = str(ability.get("target", "self"))
	var response: Dictionary
	if target_type == "self":
		response = _ability_system.use_self_ability(GameState.player_character, ability)
	else:
		var target: Node = player.interactable
		if not is_instance_valid(target) or not target.has_method("receive_signature_ability"):
			_ability_panel.set_message("Подойдите к тренировочной цели.", false)
			return
		response = target.call("receive_signature_ability", ability, true) as Dictionary
	_ability_panel.set_message(str(response.get("message", "Способность применена.")), bool(response.get("success", false)))
	GameState.save_game()
	_update_status()


func _on_rest_requested() -> void:
	_class_data.long_rest(GameState.player_character)
	_ability_panel.set_message("Долгий отдых восстановил здоровье и ресурсы.", true)
	_update_status()


func _update_status() -> void:
	var identity: String = "%s · %s · ур. %d" % [
		GameState.player_character.character_name,
		GameState.player_character.character_class_name,
		GameState.player_character.level
	]
	status_label.text = "%s\n%s" % [identity, GameState.get_current_objective_text()]
	if _ability_panel != null:
		_ability_panel.refresh()


func _on_quest_updated(_quest_id: String) -> void:
	_update_status()


func _on_inventory_changed(_item_id: String) -> void:
	_update_status()
