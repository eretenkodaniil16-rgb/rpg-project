class_name EnvironmentReactiveNpcAiSystem
extends AdvancedNpcCombatAiSystem

const ENVIRONMENT_DATA_PATH: String = "res://data/ai/environment_reactions.json"

const ACTION_AVOID_HAZARD: String = "avoid_hazard"
const ACTION_EXPLOIT_OPENING: String = "exploit_opening"
const ACTION_SECURE_PASSAGE: String = "secure_passage"
const ACTION_HOLD_BREACH: String = "hold_breach"
const ACTION_RECOVER_COVER: String = "recover_cover"
const ACTION_INVESTIGATE_CHANGE: String = "investigate_change"
const ACTION_RESCUE_ALLY: String = "rescue_ally"
const ACTION_COVER_RESCUE: String = "cover_rescue"
const ACTION_SUPPORT_RESCUE: String = "support_rescue"
const ACTION_REPOSITION_FOR_SPELL: String = "reposition_for_spell"
const ACTION_GUARD_PASSAGE: String = "guard_passage"

var _environment_roles: Dictionary = {}
var _environment_actors: Dictionary = {}


func _init() -> void:
	super._init()
	_load_environment_profiles()


func get_environment_profile(actor_id: String, combat_profile: Dictionary = {}) -> Dictionary:
	var role_id_value: String = str(combat_profile.get("role", ROLE_MELEE))
	var role_value: Variant = _environment_roles.get(role_id_value, {})
	var actor_value: Variant = _environment_actors.get(actor_id, {})
	var result: Dictionary = (role_value as Dictionary).duplicate(true) if role_value is Dictionary else {}
	if actor_value is Dictionary:
		result.merge((actor_value as Dictionary).duplicate(true), true)
	return result


func choose_combat_intent(actor_id: String, context: Dictionary) -> Dictionary:
	var baseline: Dictionary = super.choose_combat_intent(actor_id, context)
	var event_value: Variant = context.get("environment_event", {})
	if not event_value is Dictionary:
		return baseline
	var event: Dictionary = event_value as Dictionary
	if event.is_empty():
		return baseline
	var combat_profile: Dictionary = get_profile(actor_id)
	var environment_profile: Dictionary = get_environment_profile(actor_id, combat_profile)
	var reactions_value: Variant = environment_profile.get("reactions", {})
	if not reactions_value is Dictionary:
		return baseline
	var event_type: String = str(event.get("type", ""))
	var reaction_value: Variant = (reactions_value as Dictionary).get(event_type, {})
	if not reaction_value is Dictionary:
		return baseline
	var reaction: Dictionary = reaction_value as Dictionary
	var action: String = str(reaction.get("action", ""))
	var intent: String = str(reaction.get("intent", ""))
	if action.is_empty() or intent.is_empty():
		return baseline
	if not _environment_reaction_allowed(action, event, context):
		return baseline
	var severity: float = clampf(float(event.get("severity", 1.0)), 0.25, 3.0)
	var relevance: float = clampf(float(context.get("environment_relevance", 1.0)), 0.0, 1.0)
	var score: float = float(reaction.get("score", 100.0)) * lerpf(0.55, 1.0, relevance) * lerpf(0.8, 1.2, clampf(severity / 2.0, 0.0, 1.0))
	if score <= float(baseline.get("score", BLOCKED_SCORE)) + 0.0001:
		return baseline
	return {
		"intent": intent,
		"score": score,
		"role": str(combat_profile.get("role", ROLE_MELEE)),
		"reason": _reaction_reason(action, event_type),
		"attack_range_feet": int(combat_profile.get("attack_range_feet", DistanceSystem.MELEE_REACH_FEET)),
		"minimum_range_feet": int(combat_profile.get("minimum_range_feet", 0)),
		"preferred_range_feet": int(combat_profile.get("preferred_range_feet", DistanceSystem.MELEE_REACH_FEET)),
		"environment_action": action,
		"environment_event_id": str(event.get("event_id", "")),
		"environment_event_type": event_type,
		"environment_event_position": event.get("position", Vector2.ZERO)
	}


func _environment_reaction_allowed(action: String, event: Dictionary, context: Dictionary) -> bool:
	var distance_feet: int = maxi(int(event.get("distance_feet", 0)), 0)
	match action:
		ACTION_AVOID_HAZARD:
			return bool(context.get("actor_in_environment_hazard", false)) or distance_feet <= 15
		ACTION_RECOVER_COVER, ACTION_REPOSITION_FOR_SPELL:
			return bool(context.get("environment_cover_compromised", false)) or distance_feet <= 25
		ACTION_SECURE_PASSAGE, ACTION_HOLD_BREACH, ACTION_GUARD_PASSAGE:
			return bool(context.get("environment_passage_relevant", false)) or distance_feet <= 30
		ACTION_RESCUE_ALLY, ACTION_COVER_RESCUE, ACTION_SUPPORT_RESCUE:
			return bool(context.get("environment_same_squad", false))
		_:
			return true


func _reaction_reason(action: String, event_type: String) -> String:
	match action:
		ACTION_AVOID_HAZARD:
			return "NPC замечает новую опасную зону и меняет маршрут, а не проходит через неё."
		ACTION_EXPLOIT_OPENING:
			return "NPC использует открывшийся проход или потерянное укрытие для давления на героя."
		ACTION_SECURE_PASSAGE:
			return "Защитник реагирует на открытый проход и пытается снова перекрыть его."
		ACTION_HOLD_BREACH:
			return "Защитник занимает разрушенный проход и превращает его в новую точку обороны."
		ACTION_RECOVER_COVER:
			return "Стрелок или маг замечает потерю укрытия и ищет новую защищённую позицию."
		ACTION_INVESTIGATE_CHANGE:
			return "NPC проверяет изменение окружения вместо слепого продолжения прежнего плана."
		ACTION_RESCUE_ALLY, ACTION_COVER_RESCUE, ACTION_SUPPORT_RESCUE:
			return "NPC замечает связанного союзника и перестраивает действия вокруг попытки спасения."
		ACTION_REPOSITION_FOR_SPELL:
			return "Маг меняет линию заклинания после изменения прохода или обзора."
		ACTION_GUARD_PASSAGE:
			return "Защитник закрепляется у изменившегося прохода."
		_:
			return "NPC реагирует на изменение окружения: %s." % event_type


func _load_environment_profiles() -> void:
	_environment_roles.clear()
	_environment_actors.clear()
	if not FileAccess.file_exists(ENVIRONMENT_DATA_PATH):
		return
	var file: FileAccess = FileAccess.open(ENVIRONMENT_DATA_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		return
	var data: Dictionary = parsed as Dictionary
	var roles_value: Variant = data.get("role_profiles", {})
	var actors_value: Variant = data.get("profiles", {})
	_environment_roles = (roles_value as Dictionary).duplicate(true) if roles_value is Dictionary else {}
	_environment_actors = (actors_value as Dictionary).duplicate(true) if actors_value is Dictionary else {}
