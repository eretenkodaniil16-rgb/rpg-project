class_name NpcCasualtyAwarenessSystem
extends RefCounted

var _acknowledged_by_actor: Dictionary = {}
var _squad_casualties: Dictionary = {}
var _squad_rally_until_round: Dictionary = {}


func observe_body(
	actor_id: String,
	squad_id: String,
	corpse_id: String,
	body_actor_id: String,
	world_position: Vector2,
	round_number: int,
	visible: bool,
	same_squad: bool
) -> Dictionary:
	if actor_id.is_empty() or squad_id.is_empty() or corpse_id.is_empty() or not visible or not same_squad:
		return {"new": false}
	var actor_seen: Dictionary = _acknowledged_by_actor.get(actor_id, {}) as Dictionary if _acknowledged_by_actor.get(actor_id, {}) is Dictionary else {}
	var is_new_for_actor: bool = not actor_seen.has(corpse_id)
	actor_seen[corpse_id] = true
	_acknowledged_by_actor[actor_id] = actor_seen

	var casualties: Dictionary = _squad_casualties.get(squad_id, {}) as Dictionary if _squad_casualties.get(squad_id, {}) is Dictionary else {}
	if not casualties.has(corpse_id):
		casualties[corpse_id] = {
			"corpse_id": corpse_id,
			"body_actor_id": body_actor_id,
			"position": world_position,
			"round": maxi(round_number, 0),
			"observer_actor_id": actor_id
		}
	_squad_casualties[squad_id] = casualties
	return {
		"new": is_new_for_actor,
		"corpse_id": corpse_id,
		"body_actor_id": body_actor_id,
		"position": world_position,
		"round": maxi(round_number, 0),
		"casualty_count": casualties.size()
	}


func get_context(actor_id: String, squad_id: String, round_number: int) -> Dictionary:
	var casualties: Dictionary = _squad_casualties.get(squad_id, {}) as Dictionary if _squad_casualties.get(squad_id, {}) is Dictionary else {}
	var latest: Dictionary = {}
	for value: Variant in casualties.values():
		if value is Dictionary and (latest.is_empty() or int((value as Dictionary).get("round", 0)) > int(latest.get("round", 0))):
			latest = (value as Dictionary).duplicate(true)
	return {
		"casualty_count": casualties.size(),
		"latest_casualty": latest,
		"rally_active": is_rally_active(squad_id, round_number),
		"rally_rounds_remaining": maxi(int(_squad_rally_until_round.get(squad_id, -1)) - maxi(round_number, 0) + 1, 0),
		"acknowledged_count": (_acknowledged_by_actor.get(actor_id, {}) as Dictionary).size() if _acknowledged_by_actor.get(actor_id, {}) is Dictionary else 0
	}


func rally_squad(squad_id: String, current_round: int, duration_rounds: int) -> bool:
	if squad_id.is_empty() or duration_rounds <= 0:
		return false
	_squad_rally_until_round[squad_id] = maxi(current_round, 0) + duration_rounds - 1
	return true


func is_rally_active(squad_id: String, current_round: int) -> bool:
	return not squad_id.is_empty() and int(_squad_rally_until_round.get(squad_id, -1)) >= maxi(current_round, 0)


func clear() -> void:
	_acknowledged_by_actor.clear()
	_squad_casualties.clear()
	_squad_rally_until_round.clear()


func get_squad_casualties_for_testing(squad_id: String) -> Dictionary:
	var value: Variant = _squad_casualties.get(squad_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}
