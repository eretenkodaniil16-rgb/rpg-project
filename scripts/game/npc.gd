class_name CombatNpc
extends Area2D

@export_file("*.json") var dialogue_path: String = "res://data/dialogues/caretaker_intro.json"
@export var combat_name: String = "Смотритель"
@export var armor_class: int = 12
@export var maximum_health: int = 14
@export var attack_bonus: int = 3
@export var damage_die: int = 6
@export var damage_bonus: int = 1
@export var damage_type: String = "slashing"
@export var initiative_modifier: int = 1
@export var combat_speed_feet: int = 30
@export var strength_save_modifier: int = 1
@export var dexterity_save_modifier: int = 1
@export var constitution_save_modifier: int = 1

@onready var body_visual: Polygon2D = $Body
@onready var name_label: Label = $NameLabel

var player_in_range: Node = null
var current_health: int = 14
var hostile: bool = false
var defeated: bool = false
var _targeted: bool = false
var _turn_active: bool = false
var _combat_overlay_visible: bool = true
var _attack_cooldown: float = 0.0
var _target_marker: Label
var _turn_marker: Label
var _health_label: Label
var _dice: DiceRoller = DiceRoller.new()
var _class_data: ClassDataSystem = ClassDataSystem.new()
var _ability_system: ClassAbilitySystem = ClassAbilitySystem.new()


func _ready() -> void:
	add_to_group("combat_targets")
	maximum_health = maxi(maximum_health, 1)
	current_health = maximum_health
	name_label.text = combat_name
	_build_combat_labels()
	_update_combat_visuals()


func _process(delta: float) -> void:
	if _is_turn_based_combat_active():
		return
	if not hostile or defeated or GameState.input_locked:
		return
	_attack_cooldown = maxf(_attack_cooldown - delta, 0.0)
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if player == null:
		return
	if DistanceSystem.distance_feet(global_position, player.global_position) <= DistanceSystem.MELEE_REACH_FEET and _attack_cooldown <= 0.0:
		_attack_cooldown = 1.4
		_perform_retaliation()


func interact() -> void:
	if defeated:
		get_tree().call_group("game_world", "show_combat_message", "%s без сознания." % combat_name, false)
		return
	if hostile:
		get_tree().call_group("game_world", "show_combat_message", "%s настроен враждебно и не желает говорить." % combat_name, false)
		return
	var dialogue_data: Dictionary = _load_dialogue()
	if dialogue_data.is_empty():
		return
	var quest_event: String = str(dialogue_data.get("quest_event", ""))
	if not quest_event.is_empty():
		GameState.report_quest_event(quest_event)
	get_tree().call_group("dialogue_ui", "start_dialogue", dialogue_data)
	get_tree().call_group("game_world", "set_interaction_hint", false)


func get_combat_name() -> String:
	return combat_name


func get_armor_class() -> int:
	return armor_class


func get_current_health() -> int:
	return current_health


func get_initiative_modifier() -> int:
	return initiative_modifier


func get_combat_speed_feet() -> int:
	return maxi(combat_speed_feet, 0)


func get_saving_throw_modifier(ability_id: String) -> int:
	match ability_id:
		"strength": return strength_save_modifier
		"dexterity": return dexterity_save_modifier
		"constitution": return constitution_save_modifier
		_: return 0


func can_take_combat_turn() -> bool:
	return hostile and not defeated


func is_combat_active() -> bool:
	return not defeated


func is_hostile() -> bool:
	return hostile and not defeated


func enter_combat_hostile() -> void:
	if not defeated:
		hostile = true
		_update_combat_visuals()


func set_turn_active(value: bool) -> void:
	_turn_active = value
	_update_combat_visuals()


func perform_combat_turn_attack() -> void:
	if can_take_combat_turn():
		_perform_retaliation()


func perform_opportunity_attack() -> void:
	if can_take_combat_turn():
		get_tree().call_group("game_world", "show_combat_message", "%s проводит атаку по возможности." % combat_name, false)
		_perform_retaliation()


func set_combat_targeted(value: bool) -> void:
	_targeted = value
	_update_combat_visuals()


func set_combat_overlay_visible(value: bool) -> void:
	_combat_overlay_visible = value
	_update_combat_visuals()


func receive_player_attack(result: AttackResult, show_interface: bool = true) -> void:
	if defeated:
		result.note = "Цель уже без сознания."
		return
	hostile = true
	if result.hit:
		current_health = maxi(0, current_health - result.damage)
		_flash(Color(1.0, 0.45, 0.4, 1.0))
	else:
		_flash(Color(1.0, 1.0, 1.0, 0.55))
	result.target_health_after = current_health
	result.target_max_health = maximum_health
	if current_health <= 0:
		defeated = true
		hostile = false
		result.note = _append_note(result.note, "%s теряет сознание." % combat_name)
	_update_combat_visuals()
	if show_interface:
		get_tree().call_group("combat_ui", "show_result", result)


func receive_signature_ability(ability: Dictionary, show_interface: bool = true, attack_context: Dictionary = {}) -> Dictionary:
	if defeated:
		return {"success": false, "message": "%s уже без сознания." % combat_name}
	var effect: String = str(ability.get("effect", ""))
	if effect == "hunters_mark":
		var setup: Dictionary = _ability_system.apply_target_ability(GameState.player_character, ability)
		GameState.save_game()
		return setup
	if effect not in ["spell_attack", "auto_hit_spell", "saving_throw_spell"]:
		return {"success": false, "message": "Эта способность не действует на выбранную цель."}
	var result: AttackResult = _ability_system.perform_offensive_ability(GameState.player_character, ability, armor_class, -1, [], attack_context)
	if result.out_of_range or (not result.note.is_empty() and not result.hit):
		return {"success": false, "message": result.note}
	hostile = true
	receive_player_attack(result, show_interface)
	GameState.save_game()
	return {"success": true, "message": "%s применена к цели %s." % [result.attack_name, combat_name]}


func reset_combat_state(full_restore: bool = true) -> void:
	hostile = false
	defeated = false
	_turn_active = false
	_attack_cooldown = 0.0
	if full_restore:
		current_health = maximum_health
	body_visual.modulate = Color.WHITE
	_update_combat_visuals()


func _perform_retaliation() -> void:
	var game: Node = get_tree().get_first_node_in_group("game_world")
	if game != null and game.has_method("resolve_npc_attack"):
		game.call("resolve_npc_attack", self, attack_bonus, damage_die, damage_bonus, damage_type)
		return
	var natural_first: int = _dice.roll_die(20)
	var natural: int = natural_first
	var player_dodging: bool = game != null and game.has_method("player_is_dodging") and bool(game.call("player_is_dodging"))
	if player_dodging:
		var natural_second: int = _dice.roll_die(20)
		natural = mini(natural_first, natural_second)
	var target_ac: int = _class_data.get_armor_class(GameState.player_character)
	var total: int = natural + attack_bonus
	if natural == 1 or (natural != 20 and total < target_ac):
		get_tree().call_group("game_world", "show_combat_message", "%s промахивается: d20 %d + %d против КД %d." % [combat_name, natural, attack_bonus, target_ac], false)
		return
	var damage: int = _dice.roll_die(maxi(damage_die, 2)) + damage_bonus
	GameState.player_character.current_health = maxi(0, GameState.player_character.current_health - damage)
	get_tree().call_group("game_world", "show_combat_message", "%s наносит %d урона. Здоровье: %d/%d." % [combat_name, damage, GameState.player_character.current_health, GameState.player_character.maximum_health], false)
	GameState.save_game()
	if GameState.player_character.current_health <= 0:
		get_tree().call_group("game_world", "handle_player_defeat", self)


func _build_combat_labels() -> void:
	_target_marker = Label.new()
	_target_marker.text = "▼ ЦЕЛЬ"
	_target_marker.position = Vector2(-42, -92)
	_target_marker.add_theme_color_override("font_color", Color(1.0, 0.35, 0.3, 1.0))
	_target_marker.add_theme_font_size_override("font_size", 16)
	add_child(_target_marker)
	_turn_marker = Label.new()
	_turn_marker.text = "◆ ХОД"
	_turn_marker.position = Vector2(-34, -116)
	_turn_marker.add_theme_color_override("font_color", Color(0.5, 1.0, 0.55, 1.0))
	_turn_marker.add_theme_font_size_override("font_size", 15)
	add_child(_turn_marker)
	_health_label = Label.new()
	_health_label.position = Vector2(-70, 42)
	_health_label.size = Vector2(140, 24)
	_health_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_health_label.add_theme_font_size_override("font_size", 14)
	add_child(_health_label)


func _update_combat_visuals() -> void:
	if _target_marker != null:
		_target_marker.visible = _combat_overlay_visible and _targeted and not defeated
	if _turn_marker != null:
		_turn_marker.visible = _combat_overlay_visible and _turn_active and not defeated
	if _health_label != null:
		_health_label.text = "%s · КД %d · %d/%d" % ["без сознания" if defeated else ("враждебен" if hostile else "нейтрален"), armor_class, current_health, maximum_health]
		_health_label.visible = _combat_overlay_visible and (_targeted or _turn_active or hostile or current_health < maximum_health)
	body_visual.modulate = Color(0.45, 0.45, 0.45, 0.75) if defeated else Color.WHITE


func _flash(color: Color) -> void:
	body_visual.modulate = color
	var tween: Tween = create_tween()
	tween.tween_property(body_visual, "modulate", Color.WHITE, 0.22)


func _load_dialogue() -> Dictionary:
	if not FileAccess.file_exists(dialogue_path):
		return {}
	var file: FileAccess = FileAccess.open(dialogue_path, FileAccess.READ)
	if file == null:
		return {}
	var parsed_data: Variant = JSON.parse_string(file.get_as_text())
	return parsed_data as Dictionary if parsed_data is Dictionary else {}


func _on_body_entered(body: Node2D) -> void:
	if not body.is_in_group("player"):
		return
	player_in_range = body
	if body.has_method("set_interactable"):
		body.call("set_interactable", self)
	get_tree().call_group("game_world", "set_interaction_hint", true)


func _on_body_exited(body: Node2D) -> void:
	if body != player_in_range:
		return
	if body.has_method("clear_interactable"):
		body.call("clear_interactable", self)
	player_in_range = null
	get_tree().call_group("game_world", "set_interaction_hint", false)


func _is_turn_based_combat_active() -> bool:
	var game: Node = get_tree().get_first_node_in_group("game_world")
	return game != null and game.has_method("is_turn_based_combat_active") and bool(game.call("is_turn_based_combat_active"))


func _append_note(current: String, addition: String) -> String:
	return addition if current.is_empty() else "%s %s" % [current, addition]
