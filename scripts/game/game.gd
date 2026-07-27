extends "res://scripts/game/game_base.gd"

const CHARACTER_SHEET_SCENE: PackedScene = preload("res://scenes/ui/character_sheet.tscn")
const QUEST_JOURNAL_SCENE: PackedScene = preload("res://scenes/ui/quest_journal.tscn")
const INVENTORY_PANEL_SCENE: PackedScene = preload("res://scenes/ui/inventory_panel.tscn")
const ATTACK_RESULT_SCENE: PackedScene = preload("res://scenes/ui/attack_result_popup.tscn")
const TRAINING_DUMMY_SCENE: PackedScene = preload("res://scenes/game/training_dummy.tscn")
const ABILITY_PANEL_SCENE: PackedScene = preload("res://scenes/ui/ability_panel.tscn")
const RANGED_PROJECTILE_SCRIPT: Script = preload("res://scripts/game/ranged_projectile.gd")

var _character_button: Button
var _quest_button: Button
var _inventory_button: Button
var _attack_button: Button
var _target_button: Button
var _target_label: Label
var _combat_message: Label
var _character_sheet: CharacterSheet
var _quest_journal: QuestJournal
var _inventory_panel: InventoryPanel
var _attack_popup: AttackResultPopup
var _training_dummy: TrainingDummy
var _ability_panel: AbilityPanel
var _selected_target: Node = null
var _class_data: ClassDataSystem = ClassDataSystem.new()
var _ability_system: ClassAbilitySystem = ClassAbilitySystem.new()
var _combat_system: CombatSystem = CombatSystem.new()
var _attack_in_progress: bool = false
var _hud_overlay_active: bool = false
var _exploration_hud_nodes: Array[CanvasItem] = []
var _hud_saved_visibility: Dictionary = {}


func _ready() -> void:
	_class_data.ensure_starting_loadout(GameState.player_character)
	super._ready()
	_build_player_menus()
	_build_combat_training()
	_build_ability_ui()
	_build_combat_controls()
	_register_exploration_hud()
	_connect_progress_signals()
	_update_status()
	_sync_exploration_hud_visibility()
	call_deferred("_select_nearest_target")


func _process(_delta: float) -> void:
	_update_target_label()
	_sync_exploration_hud_visibility()


func _unhandled_input(event: InputEvent) -> void:
	if _any_overlay_visible() or _attack_in_progress:
		return
	if event is InputEventKey:
		var key_event := event as InputEventKey
		if key_event.pressed and not key_event.echo:
			match key_event.keycode:
				KEY_C: _open_character_sheet()
				KEY_J: _open_quest_journal()
				KEY_I: _open_inventory()
				KEY_TAB: _cycle_target()
				KEY_F: _request_attack()
				_:
					super._unhandled_input(event)
					return
			get_viewport().set_input_as_handled()
			return
	super._unhandled_input(event)


func _build_player_menus() -> void:
	var interface: CanvasLayer = $Interface
	help_label.offset_right = 580.0
	status_label.offset_right = 620.0
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
	_character_sheet.rest_completed.connect(_on_rest_completed)
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
	interface.add_child(_ability_panel)
	_ability_panel.bind_character(GameState.player_character)


func _build_combat_controls() -> void:
	var interface: CanvasLayer = $Interface
	_target_label = Label.new()
	_target_label.name = "TargetLabel"
	_target_label.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_target_label.offset_left = -600.0
	_target_label.offset_top = 94.0
	_target_label.offset_right = -20.0
	_target_label.offset_bottom = 132.0
	_target_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_target_label.add_theme_color_override("font_color", Color(1.0, 0.72, 0.38, 1.0))
	_target_label.add_theme_font_size_override("font_size", 18)
	interface.add_child(_target_label)

	_target_button = Button.new()
	_target_button.name = "TargetButton"
	_target_button.text = "ЦЕЛЬ"
	_target_button.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_target_button.offset_left = -232.0
	_target_button.offset_top = -318.0
	_target_button.offset_right = -28.0
	_target_button.offset_bottom = -258.0
	_target_button.add_theme_font_size_override("font_size", 18)
	_target_button.pressed.connect(_cycle_target)
	_target_button.visible = _uses_touch_controls()
	interface.add_child(_target_button)

	_attack_button = Button.new()
	_attack_button.name = "AttackButton"
	_attack_button.text = "АТАКА"
	_attack_button.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_attack_button.offset_left = -232.0
	_attack_button.offset_top = -248.0
	_attack_button.offset_right = -28.0
	_attack_button.offset_bottom = -158.0
	_attack_button.add_theme_font_size_override("font_size", 22)
	_attack_button.pressed.connect(_request_attack)
	_attack_button.visible = _uses_touch_controls()
	interface.add_child(_attack_button)

	_combat_message = Label.new()
	_combat_message.name = "CombatMessageLabel"
	_combat_message.offset_left = 330.0
	_combat_message.offset_top = 570.0
	_combat_message.offset_right = 950.0
	_combat_message.offset_bottom = 616.0
	_combat_message.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_combat_message.add_theme_font_size_override("font_size", 18)
	_combat_message.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	interface.add_child(_combat_message)


func _register_exploration_hud() -> void:
	_exploration_hud_nodes.clear()
	_add_exploration_hud_node(help_label)
	_add_exploration_hud_node(status_label)
	_add_exploration_hud_node(interaction_label)
	_add_exploration_hud_node($Interface/MobileControls as CanvasItem)
	_add_exploration_hud_node(_character_button)
	_add_exploration_hud_node(_quest_button)
	_add_exploration_hud_node(_inventory_button)
	_add_exploration_hud_node(_target_label)
	_add_exploration_hud_node(_target_button)
	_add_exploration_hud_node(_attack_button)
	_add_exploration_hud_node(_combat_message)
	_add_exploration_hud_node(_ability_panel)


func _add_exploration_hud_node(node: CanvasItem) -> void:
	if node != null and not _exploration_hud_nodes.has(node):
		_exploration_hud_nodes.append(node)


func _sync_exploration_hud_visibility() -> void:
	var overlay_visible: bool = _any_overlay_visible()
	if overlay_visible == _hud_overlay_active:
		return
	_hud_overlay_active = overlay_visible
	if overlay_visible:
		_hud_saved_visibility.clear()
		for item: CanvasItem in _exploration_hud_nodes:
			if is_instance_valid(item):
				_hud_saved_visibility[item.get_instance_id()] = item.visible
				item.hide()
	else:
		for item: CanvasItem in _exploration_hud_nodes:
			if is_instance_valid(item):
				item.visible = bool(_hud_saved_visibility.get(item.get_instance_id(), false))
		_hud_saved_visibility.clear()
	for target: Node in get_tree().get_nodes_in_group("combat_targets"):
		if target.has_method("set_combat_overlay_visible"):
			target.call("set_combat_overlay_visible", not overlay_visible)


func _connect_progress_signals() -> void:
	if not GameState.quest_updated.is_connected(_on_quest_updated):
		GameState.quest_updated.connect(_on_quest_updated)
	if not GameState.inventory_changed.is_connected(_on_inventory_changed):
		GameState.inventory_changed.connect(_on_inventory_changed)


func _open_character_sheet() -> void:
	if GameState.input_locked or _character_sheet == null:
		return
	_character_sheet.open_sheet(GameState.player_character)
	_sync_exploration_hud_visibility()


func _open_quest_journal() -> void:
	if GameState.input_locked or _quest_journal == null:
		return
	_quest_journal.open_journal()
	_sync_exploration_hud_visibility()


func _open_inventory() -> void:
	if GameState.input_locked or _inventory_panel == null:
		return
	_inventory_panel.open_inventory()
	_sync_exploration_hud_visibility()


func _any_overlay_visible() -> bool:
	var dialogue_ui: CanvasItem = get_node_or_null("Interface/DialogueUI") as CanvasItem
	return (
		(_character_sheet != null and _character_sheet.visible)
		or (_quest_journal != null and _quest_journal.visible)
		or (_inventory_panel != null and _inventory_panel.visible)
		or (_attack_popup != null and _attack_popup.visible)
		or (dialogue_ui != null and dialogue_ui.visible)
	)


func _request_attack() -> void:
	if GameState.input_locked or _any_overlay_visible() or _attack_in_progress:
		return
	if not _target_is_valid(_selected_target):
		_select_nearest_target()
	if not _target_is_valid(_selected_target):
		show_combat_message("В комнате нет доступной цели.", false)
		return
	var target: Node = _selected_target
	var weapon: Dictionary = _class_data.get_equipped_weapon(GameState.player_character)
	var target_position: Vector2 = (target as Node2D).global_position
	var distance: int = DistanceSystem.distance_feet(player.global_position, target_position)
	var ammo_id: String = str(weapon.get("ammunition_id", ""))
	var context: Dictionary = {
		"target_name": _target_name(target),
		"distance_feet": distance,
		"disadvantage": _has_hostile_within_five_feet(),
		"no_ammunition": not ammo_id.is_empty() and not GameState.has_item(ammo_id)
	}
	var result: AttackResult = _combat_system.perform_basic_attack(
		GameState.player_character,
		int(target.call("get_armor_class")),
		weapon,
		-1,
		[],
		context
	)
	if result.out_of_range or result.no_ammunition:
		_attack_popup.show_result(result)
		_sync_exploration_hud_visibility()
		return
	_set_combat_busy(true)
	if not ammo_id.is_empty():
		GameState.remove_item(ammo_id, 1, false)
	if DistanceSystem.is_ranged_weapon(weapon):
		await _play_weapon_projectile(weapon, target_position, result.hit)
	else:
		player.play_attack_animation(target_position)
	if _target_is_valid(target):
		target.call("receive_player_attack", result, true)
	GameState.save_game()
	_update_status()
	_set_combat_busy(false)
	_sync_exploration_hud_visibility()


func _set_combat_busy(value: bool) -> void:
	_attack_in_progress = value
	if _attack_button != null:
		_attack_button.disabled = value
	if _target_button != null:
		_target_button.disabled = value


func _play_weapon_projectile(weapon: Dictionary, target_position: Vector2, hit: bool) -> void:
	var style: String = "arrow" if not str(weapon.get("ammunition_id", "")).is_empty() else "thrown"
	var accent: Color = Color(0.95, 0.72, 0.28, 1.0) if style == "arrow" else Color(0.75, 0.82, 0.9, 1.0)
	await _play_projectile(player.global_position, target_position, style, accent, hit)


func _play_magic_projectiles(ability: Dictionary, target_position: Vector2) -> void:
	var effect: String = str(ability.get("effect", "spell_attack"))
	var projectile_count: int = 3 if effect == "auto_hit_spell" else 1
	var accent: Color = _magic_projectile_color(str(ability.get("damage_type", "магический")))
	for index: int in range(projectile_count):
		var offset := Vector2(0.0, float(index - 1) * 14.0) if projectile_count > 1 else Vector2.ZERO
		await _play_projectile(player.global_position + offset * 0.25, target_position + offset, "magic", accent, true)


func _play_projectile(start_position: Vector2, target_position: Vector2, style: String, accent: Color, hit: bool) -> void:
	var projectile: RangedProjectile = RANGED_PROJECTILE_SCRIPT.new() as RangedProjectile
	add_child(projectile)
	projectile.configure(style, accent)
	await projectile.fly(start_position, target_position, hit)


func _magic_projectile_color(damage_type: String) -> Color:
	match damage_type:
		"огненный": return Color(1.0, 0.38, 0.12, 1.0)
		"силовой": return Color(0.58, 0.42, 1.0, 1.0)
		"стихийный": return Color(0.2, 0.85, 1.0, 1.0)
		_: return Color(0.55, 0.78, 1.0, 1.0)


func _cycle_target() -> void:
	if GameState.input_locked or _attack_in_progress:
		return
	var targets: Array[Node] = _available_targets()
	if targets.is_empty():
		_set_selected_target(null)
		show_combat_message("Нет доступных целей.", false)
		return
	var current_index: int = targets.find(_selected_target)
	_set_selected_target(targets[(current_index + 1) % targets.size()])


func _select_nearest_target() -> void:
	var targets: Array[Node] = _available_targets()
	if targets.is_empty():
		_set_selected_target(null)
		return
	var nearest: Node = targets[0]
	var nearest_distance: float = player.global_position.distance_squared_to((nearest as Node2D).global_position)
	for target: Node in targets:
		var candidate: float = player.global_position.distance_squared_to((target as Node2D).global_position)
		if candidate < nearest_distance:
			nearest = target
			nearest_distance = candidate
	_set_selected_target(nearest)


func _available_targets() -> Array[Node]:
	var result: Array[Node] = []
	for target: Node in get_tree().get_nodes_in_group("combat_targets"):
		if target is Node2D and target.has_method("is_combat_active") and bool(target.call("is_combat_active")):
			result.append(target)
	return result


func _set_selected_target(target: Node) -> void:
	if is_instance_valid(_selected_target) and _selected_target.has_method("set_combat_targeted"):
		_selected_target.call("set_combat_targeted", false)
	_selected_target = target
	if is_instance_valid(_selected_target) and _selected_target.has_method("set_combat_targeted"):
		_selected_target.call("set_combat_targeted", true)
	_update_target_label()


func _target_is_valid(target: Node) -> bool:
	return is_instance_valid(target) and target is Node2D and target.has_method("is_combat_active") and bool(target.call("is_combat_active"))


func _target_name(target: Node) -> String:
	return str(target.call("get_combat_name")) if is_instance_valid(target) and target.has_method("get_combat_name") else "Цель"


func _update_target_label() -> void:
	if _target_label == null:
		return
	if not _target_is_valid(_selected_target):
		_target_label.text = "Цель не выбрана · Tab/ЦЕЛЬ"
		return
	var distance: int = DistanceSystem.distance_feet(player.global_position, (_selected_target as Node2D).global_position)
	_target_label.text = "Цель: %s · %d футов · КД %d · %d HP" % [
		_target_name(_selected_target), distance, int(_selected_target.call("get_armor_class")), int(_selected_target.call("get_current_health"))
	]


func _has_hostile_within_five_feet() -> bool:
	for target: Node in get_tree().get_nodes_in_group("combat_targets"):
		if target is Node2D and target.has_method("is_hostile") and bool(target.call("is_hostile")):
			if DistanceSystem.distance_feet(player.global_position, (target as Node2D).global_position) <= DistanceSystem.MELEE_REACH_FEET:
				return true
	return false


func _on_ability_requested(ability_id: String) -> void:
	if GameState.input_locked or _attack_in_progress:
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
		if not _target_is_valid(_selected_target):
			_select_nearest_target()
		if not _target_is_valid(_selected_target) or not _selected_target.has_method("receive_signature_ability"):
			_ability_panel.set_message("Сначала выберите боевую цель.", false)
			return
		var target: Node = _selected_target
		var target_position: Vector2 = (target as Node2D).global_position
		var distance: int = DistanceSystem.distance_feet(player.global_position, target_position)
		var maximum_range: int = int(ability.get("range_ft", 5))
		if distance > maximum_range:
			_ability_panel.set_message("Цель дальше %d футов." % maximum_range, false)
			return
		var resource_key: String = str(ability.get("resource_key", "unlimited"))
		if resource_key != "unlimited" and not resource_key.is_empty() and GameState.player_character.get_resource(resource_key) <= 0:
			_ability_panel.set_message("Не осталось доступных применений способности.", false)
			return
		var context: Dictionary = {
			"target_name": _target_name(target),
			"distance_feet": distance,
			"disadvantage": _has_hostile_within_five_feet()
		}
		var effect: String = str(ability.get("effect", ""))
		if effect in ["spell_attack", "auto_hit_spell"]:
			_set_combat_busy(true)
			await _play_magic_projectiles(ability, target_position)
		response = target.call("receive_signature_ability", ability, true, context) as Dictionary
		_set_combat_busy(false)
	_ability_panel.set_message(str(response.get("message", "Способность применена.")), bool(response.get("success", false)))
	GameState.save_game()
	_update_status()
	_sync_exploration_hud_visibility()


func _on_rest_completed(rest_type: String) -> void:
	if rest_type == "long":
		for target: Node in get_tree().get_nodes_in_group("combat_targets"):
			if target.has_method("reset_combat_state"):
				target.call("reset_combat_state", true)
	show_combat_message("Короткий отдых завершён." if rest_type == "short" else "Долгий отдых завершён; все противники успокоились.", true)
	if _ability_panel != null:
		_ability_panel.refresh()
	_update_status()


func show_combat_message(message: String, is_success: bool = true) -> void:
	if _combat_message == null:
		return
	_combat_message.text = message
	_combat_message.add_theme_color_override("font_color", Color(0.64, 0.94, 0.68, 1.0) if is_success else Color(1.0, 0.55, 0.48, 1.0))


func handle_player_defeat(_source: Node = null) -> void:
	if GameState.input_locked:
		return
	GameState.input_locked = true
	show_combat_message("Персонаж теряет сознание. Через мгновение он очнётся у входа.", false)
	await get_tree().create_timer(1.5).timeout
	GameState.player_character.current_health = maxi(1, ceili(GameState.player_character.maximum_health / 2.0))
	player.global_position = GameState.DEFAULT_PLAYER_POSITION
	GameState.player_position = player.global_position
	for target: Node in get_tree().get_nodes_in_group("combat_targets"):
		if target.has_method("reset_combat_state"):
			target.call("reset_combat_state", true)
	GameState.input_locked = false
	GameState.save_game()
	_select_nearest_target()
	_update_status()


func _update_status() -> void:
	var identity: String = "%s · %s · ур. %d · HP %d/%d" % [
		GameState.player_character.character_name,
		GameState.player_character.character_class_name,
		GameState.player_character.level,
		GameState.player_character.current_health,
		GameState.player_character.maximum_health
	]
	status_label.text = "%s\n%s" % [identity, GameState.get_current_objective_text()]
	if _ability_panel != null:
		_ability_panel.refresh()


func _on_quest_updated(_quest_id: String) -> void:
	_update_status()


func _on_inventory_changed(_item_id: String) -> void:
	_update_status()
