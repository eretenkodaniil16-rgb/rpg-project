class_name ReactionCandidate
extends RefCounted

const CONTROLLER_PLAYER: String = "player"
const CONTROLLER_AI: String = "ai"
const TEAM_PARTY: String = "party"
const TEAM_HOSTILE: String = "hostile"

var reactor_id: String = ""
var actor: Node
var character: PlayerCharacter
var display_name: String = "Участник"
var team_id: String = ""
var controller_id: String = CONTROLLER_AI
var initiative: int = 0
var reaction_available: bool = false
var can_react: bool = true
var context_overrides: Dictionary = {}
var metadata: Dictionary = {}


func _init(
	new_reactor_id: String = "",
	new_actor: Node = null,
	new_character: PlayerCharacter = null
) -> void:
	reactor_id = new_reactor_id
	actor = new_actor
	character = new_character


func is_valid() -> bool:
	if reactor_id.is_empty() or not can_react or not reaction_available:
		return false
	if actor != null and not is_instance_valid(actor):
		return false
	return true


func build_context(base_context: Dictionary) -> Dictionary:
	var result: Dictionary = base_context.duplicate(true)
	for key: Variant in context_overrides.keys():
		result[key] = context_overrides[key]
	result["reactor"] = character
	result["reactor_actor"] = actor
	result["reactor_id"] = reactor_id
	result["reactor_name"] = display_name
	result["reactor_team_id"] = team_id
	result["reactor_controller_id"] = controller_id
	result["reaction_available"] = reaction_available
	result["reactor_can_react"] = can_react
	return result


static func from_descriptor(descriptor: Dictionary) -> ReactionCandidate:
	var candidate := ReactionCandidate.new(
		str(descriptor.get("reactor_id", "")),
		descriptor.get("actor") as Node,
		descriptor.get("character") as PlayerCharacter
	)
	candidate.display_name = str(descriptor.get("display_name", "Участник"))
	candidate.team_id = str(descriptor.get("team_id", ""))
	candidate.controller_id = str(descriptor.get("controller_id", CONTROLLER_AI))
	candidate.initiative = int(descriptor.get("initiative", 0))
	candidate.reaction_available = bool(descriptor.get("reaction_available", false))
	candidate.can_react = bool(descriptor.get("can_react", true))
	candidate.context_overrides = (descriptor.get("context_overrides", {}) as Dictionary).duplicate(true)
	candidate.metadata = (descriptor.get("metadata", {}) as Dictionary).duplicate(true)
	return candidate
