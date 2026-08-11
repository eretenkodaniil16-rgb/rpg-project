extends SceneTree

const PERCEPTION_SCRIPT: Script = preload("res://scripts/systems/exploration_stealth_perception_system.gd")
const TARGETING_SCRIPT: Script = preload("res://scripts/systems/npc_tactical_targeting_system.gd")


func _init() -> void:
	var perception: ExplorationStealthPerceptionSystem = PERCEPTION_SCRIPT.new() as ExplorationStealthPerceptionSystem
	var targeting: NpcTacticalTargetingSystem = TARGETING_SCRIPT.new() as NpcTacticalTargetingSystem
	if perception == null or targeting == null:
		_fail("AI v2 systems could not be created.")
		return
	if perception.get_hide_entry_dc() != 15:
		_fail("Hide entry DC must follow the configured SRD baseline of 15.")
		return

	var no_los: Dictionary = perception.resolve_passive_detection(18, 12, 5, false, false)
	if bool(no_los.get("detected", true)):
		_fail("Passive perception detected a hidden target without geometric contact.")
		return
	var beats_passive: Dictionary = perception.resolve_passive_detection(18, 12, 20, true, false)
	if bool(beats_passive.get("detected", true)):
		_fail("Stealth beating passive perception should remain hidden outside the close-contact threshold.")
		return
	var close_contact: Dictionary = perception.resolve_passive_detection(18, 12, 5, true, false)
	if not bool(close_contact.get("detected", false)):
		_fail("Close contact must eventually reveal a hidden target even after a strong Stealth roll.")
		return
	var passive_wins: Dictionary = perception.resolve_passive_detection(12, 12, 30, true, false)
	if not bool(passive_wins.get("detected", false)):
		_fail("Passive Perception equal to the Stealth total must detect geometric contact.")
		return
	var active_search: Dictionary = perception.resolve_active_search(16, 2, 14)
	if not bool(active_search.get("success", false)) or int(active_search.get("total", 0)) != 16:
		_fail("Active Search did not resolve Perception against the stored Stealth DC.")
		return

	var candidates: Array[Dictionary] = [
		{
			"target_id": 101,
			"available": true,
			"visible": true,
			"distance_feet": 25,
			"attack_ready": false,
			"preferred_range_feet": 5,
			"health_ratio": 1.0,
			"previous_target": true,
			"claim_count": 0,
			"immediate_melee_threat": false,
			"full_tactics_supported": true,
			"role": "melee"
		},
		{
			"target_id": 202,
			"available": true,
			"visible": true,
			"distance_feet": 5,
			"attack_ready": true,
			"preferred_range_feet": 5,
			"health_ratio": 0.55,
			"previous_target": false,
			"claim_count": 0,
			"immediate_melee_threat": true,
			"full_tactics_supported": false,
			"role": "melee"
		}
	]
	var selection: Dictionary = targeting.choose_target(candidates, 101)
	if int(selection.get("target_id", 0)) != 202:
		_fail("Tactical target selection ignored an immediate attack-ready threat.")
		return

	var near_tie: Array[Dictionary] = [
		{
			"target_id": 101,
			"available": true,
			"visible": true,
			"distance_feet": 5,
			"attack_ready": true,
			"preferred_range_feet": 5,
			"health_ratio": 0.9,
			"previous_target": true,
			"claim_count": 0,
			"immediate_melee_threat": true,
			"full_tactics_supported": true,
			"role": "melee"
		},
		{
			"target_id": 202,
			"available": true,
			"visible": true,
			"distance_feet": 5,
			"attack_ready": true,
			"preferred_range_feet": 5,
			"health_ratio": 0.8,
			"previous_target": false,
			"claim_count": 0,
			"immediate_melee_threat": true,
			"full_tactics_supported": true,
			"role": "melee"
		}
	]
	var stable_selection: Dictionary = targeting.choose_target(near_tie, 101)
	if int(stable_selection.get("target_id", 0)) != 101:
		_fail("Target hysteresis did not preserve a tactically equivalent previous target.")
		return

	print("AI perception and tactical targeting v2 unit tests passed.")
	quit(0)


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
