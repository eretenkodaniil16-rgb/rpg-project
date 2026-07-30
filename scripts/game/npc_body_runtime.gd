class_name BodyInteractionNpc
extends "res://scripts/game/npc.gd"

signal body_state_changed(actor_id: String, body_state: String)
signal corpse_loot_changed(actor_id: String)
signal restraint_state_changed(actor_id: String, bound: bool)

const CORPSE_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/corpse_interaction_system.gd")
const DRAG_FOLLOW_DISTANCE_PIXELS: float = 42.0
const DRAG_SMOOTHING: float = 12.0

var _corpse_system: CorpseInteractionSystem = CORPSE_SYSTEM_SCRIPT.new() as CorpseInteractionSystem
var _body_state: String = CorpseInteractionSystem.BODY_ALIVE
var _dragged_by: Node2D


func _ready() -> void:
	super._ready()
	_restore_persistent_body()


func _process(delta: float) -> void:
	super._process(delta)
	_update_drag_position(delta)


func receive_player_attack(result: AttackResult, show_interface: bool = true) -> void:
	var was_defeated: bool = defeated
	var nonlethal_knockout: bool = result != null and result.nonlethal_knockout and result.melee_attack
	super.receive_player_attack(result, show_interface)
	if not was_defeated and defeated:
		if nonlethal_knockout:
			current_health = 1
			_activate_body_from_defeat(CorpseInteractionSystem.BODY_UNCONSCIOUS)
		else:
			current_health = 0
			_activate_body_from_defeat(CorpseInteractionSystem.BODY_DEAD)


func reset_combat_state(full_restore: bool = true) -> void:
	stop_body_drag(false)
	super.reset_combat_state(full_restore)
	if not full_restore:
		return
	var state: Node = _body_game_state()
	if state != null:
		_corpse_system.clear_record(state, _body_actor_id(), false)
	_body_state = CorpseInteractionSystem.BODY_ALIVE
	remove_from_group("corpse_targets")
	remove_from_group("context_action_targets")
	remove_from_group("visible_bodies")
	remove_from_group("bound_bodies")
	add_to_group("combat_targets")
	_update_combat_visuals()


func interact() -> void:
	if is_body_interactable():
		var instruction: String = "Откройте ДЕЙСТВИЯ, чтобы осмотреть или перетащить тело."
		if is_dead_body() and not get_remaining_corpse_loot().is_empty():
			instruction = "Откройте ДЕЙСТВИЯ, чтобы снять предметы или перетащить тело."
		elif is_unconscious_body() and is_bound_body():
			instruction = "Цель без сознания и связана. Откройте ДЕЙСТВИЯ для осмотра или освобождения."
		elif is_unconscious_body():
			instruction = "Цель без сознания. При наличии пут её можно связать через ДЕЙСТВИЯ."
		get_tree().call_group("game_world", "show_combat_message", instruction, true)
		return
	super.interact()


func is_body_interactable() -> bool:
	return defeated and _body_state in [CorpseInteractionSystem.BODY_UNCONSCIOUS, CorpseInteractionSystem.BODY_DEAD]


func is_dead_body() -> bool:
	return defeated and _body_state == CorpseInteractionSystem.BODY_DEAD


func is_unconscious_body() -> bool:
	return defeated and _body_state == CorpseInteractionSystem.BODY_UNCONSCIOUS


func is_bound_body() -> bool:
	var state: Node = _body_game_state()
	return is_unconscious_body() and state != null and _corpse_system.is_bound(state, _body_actor_id())


func get_body_state() -> String:
	return _body_state


func get_body_actor_id() -> String:
	return _body_actor_id()


func get_binding_context() -> Dictionary:
	var state: Node = _body_game_state()
	return _corpse_system.get_binding_context(state, _body_actor_id()) if state != null else {}


func get_available_restraint_sources() -> Array[Dictionary]:
	var state: Node = _body_game_state()
	return _corpse_system.get_available_restraint_sources(state, _body_actor_id()) if state != null else []


func bind_unconscious_body(item_id: String) -> Dictionary:
	var state: Node = _body_game_state()
	if state == null:
		return {"success": false, "message": "Игровое состояние недоступно."}
	var result: Dictionary = _corpse_system.bind_unconscious(state, _body_actor_id(), item_id)
	if bool(result.get("success", false)):
		add_to_group("bound_bodies")
		restraint_state_changed.emit(_body_actor_id(), true)
	return result


func release_body_restraint() -> Dictionary:
	var state: Node = _body_game_state()
	if state == null:
		return {"success": false, "message": "Игровое состояние недоступно."}
	var result: Dictionary = _corpse_system.release_restraint(state, _body_actor_id())
	if bool(result.get("success", false)):
		remove_from_group("bound_bodies")
		restraint_state_changed.emit(_body_actor_id(), false)
	return result


func get_remaining_corpse_loot() -> Array[Dictionary]:
	var state: Node = _body_game_state()
	return _corpse_system.get_remaining_loot(state, _body_actor_id()) if state != null else []


func take_corpse_item(item_id: String, quantity: int = 1) -> Dictionary:
	var state: Node = _body_game_state()
	if state == null:
		return {"success": false, "message": "Игровое состояние недоступно."}
	var result: Dictionary = _corpse_system.take_item(state, _body_actor_id(), item_id, quantity)
	if bool(result.get("success", false)):
		corpse_loot_changed.emit(_body_actor_id())
	return result


func take_all_corpse_loot() -> Dictionary:
	var state: Node = _body_game_state()
	if state == null:
		return {"success": false, "transferred": [], "failures": ["Игровое состояние недоступно."]}
	var result: Dictionary = _corpse_system.take_all(state, _body_actor_id())
	if bool(result.get("success", false)):
		corpse_loot_changed.emit(_body_actor_id())
	return result


func begin_body_drag(dragger: Node2D) -> bool:
	if not is_body_interactable() or not is_instance_valid(dragger):
		return false
	_dragged_by = dragger
	return true


func stop_body_drag(save_position: bool = true) -> void:
	if save_position and is_body_interactable():
		var state: Node = _body_game_state()
		if state != null:
			_corpse_system.update_body_position(state, _body_actor_id(), global_position, true)
	_dragged_by = null


func is_body_being_dragged() -> bool:
	return is_instance_valid(_dragged_by)


func get_context_status_text() -> String:
	if is_dead_body():
		var loot_count: int = 0
		for entry: Dictionary in get_remaining_corpse_loot():
			loot_count += maxi(int(entry.get("quantity", 0)), 0)
		var loot_text: String = "Видимых предметов не осталось." if loot_count <= 0 else "На теле осталось предметов: %d." % loot_count
		return "Мёртв. %s Тело можно перетащить." % loot_text
	if is_unconscious_body():
		var binding: Dictionary = get_binding_context()
		if not binding.is_empty():
			return "Без сознания и связан: %s, Сл освобождения %d. Предметы нельзя снимать." % [
				str(binding.get("label", "путы")),
				int(binding.get("escape_dc", 10))
			]
		return "Без сознания после несмертельного удара. Предметы нельзя снимать; цель можно связать или перетащить."
	var relation: String = "враждебен" if is_hostile() else "не проявляет открытой враждебности"
	return "Жив. Отношение: %s." % relation


func _activate_body_from_defeat(outcome: String) -> void:
	var actor_id: String = _body_actor_id()
	var state: Node = _body_game_state()
	if outcome not in CorpseInteractionSystem.VALID_DEFEAT_OUTCOMES:
		outcome = CorpseInteractionSystem.BODY_DEAD
	if state == null or actor_id.is_empty() or not _corpse_system.has_profile(actor_id):
		_body_state = outcome
	else:
		var record: Dictionary = _corpse_system.mark_defeated(state, actor_id, global_position, outcome)
		_body_state = str(record.get("body_state", outcome))
	_apply_body_groups()
	body_state_changed.emit(actor_id, _body_state)
	_update_combat_visuals()


func _restore_persistent_body() -> void:
	var actor_id: String = _body_actor_id()
	var state: Node = _body_game_state()
	if state == null or actor_id.is_empty():
		return
	var record: Dictionary = _corpse_system.get_record(state, actor_id)
	if record.is_empty():
		return
	var restored_state: String = str(record.get("body_state", CorpseInteractionSystem.BODY_ALIVE))
	if restored_state not in CorpseInteractionSystem.VALID_DEFEAT_OUTCOMES:
		return
	_body_state = restored_state
	defeated = true
	hostile = false
	current_health = 1 if restored_state == CorpseInteractionSystem.BODY_UNCONSCIOUS else 0
	global_position = _corpse_system.get_body_position(record, global_position)
	_apply_body_groups()
	_update_combat_visuals()


func _apply_body_groups() -> void:
	remove_from_group("combat_targets")
	add_to_group("corpse_targets")
	add_to_group("context_action_targets")
	add_to_group("visible_bodies")
	if is_bound_body():
		add_to_group("bound_bodies")
	else:
		remove_from_group("bound_bodies")


func _update_drag_position(delta: float) -> void:
	if not is_instance_valid(_dragged_by) or not is_body_interactable():
		_dragged_by = null
		return
	var direction: Vector2 = global_position - _dragged_by.global_position
	if direction.length_squared() <= 0.0001:
		direction = Vector2.DOWN
	var target_position: Vector2 = _dragged_by.global_position + direction.normalized() * DRAG_FOLLOW_DISTANCE_PIXELS
	global_position = global_position.lerp(target_position, clampf(delta * DRAG_SMOOTHING, 0.0, 1.0))


func _body_actor_id() -> String:
	if has_method("get_actor_id"):
		var value: String = str(call("get_actor_id"))
		if not value.is_empty():
			return value
	return name.to_snake_case()


func _body_game_state() -> Node:
	return get_tree().root.get_node_or_null("GameState") if is_inside_tree() else null
