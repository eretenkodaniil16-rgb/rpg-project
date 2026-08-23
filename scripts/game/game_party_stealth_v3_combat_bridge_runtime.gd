extends "res://scripts/game/game_party_stealth_v3_runtime.gd"


# The inherited combat bootstrap still contains the legacy single-hero stealth
# cleanup. Preserve independent Party Stealth v3 state across that transition
# for party actors that did not trigger the alert. Node references are kept only
# for this synchronous transition so post-bootstrap party availability changes
# cannot make a previously hidden actor disappear from restoration.
func _start_turn_based_combat(trigger_target: Node) -> void:
	var hidden_snapshot: Dictionary = _snapshot_hidden_party_targets_v3()
	super._start_turn_based_combat(trigger_target)
	_restore_hidden_party_targets_v3(hidden_snapshot)


func _snapshot_hidden_party_targets_v3() -> Dictionary:
	var snapshot: Dictionary = {}
	for target: Node in _party_stealth_targets_v3():
		if not _party_stealth_target_available_v3(target):
			continue
		var actor_id: String = _party_stealth_actor_id_v3(target)
		if actor_id.is_empty() or actor_id == _combat_entry_target_id_v3:
			continue
		if not _is_party_target_hidden_v3(target):
			continue
		snapshot[actor_id] = {
			"target": target,
			"stealth_total": _get_party_stealth_total_v3(target),
		}
	return snapshot


func _restore_hidden_party_targets_v3(snapshot: Dictionary) -> void:
	if snapshot.is_empty():
		return
	for actor_id_value: Variant in snapshot.keys():
		var actor_id: String = str(actor_id_value)
		if actor_id == _combat_entry_target_id_v3:
			continue
		var value: Variant = snapshot.get(actor_id, {})
		if not value is Dictionary:
			continue
		var entry: Dictionary = value as Dictionary
		var target: Node = entry.get("target", null) as Node
		if not is_instance_valid(target):
			continue
		_set_party_target_stealth_v3(target, true, int(entry.get("stealth_total", 0)))

	# Combat hidden is currently represented separately from exploration stealth
	# for the hero. Reassert it after the legacy bootstrap for the same target-only
	# semantics used by Party Stealth v3.
	if snapshot.has(PLAYER_STEALTH_ACTOR_ID_V3) and _combat_entry_target_id_v3 != PLAYER_STEALTH_ACTOR_ID_V3:
		_set_player_combat_hidden_v3(true)
