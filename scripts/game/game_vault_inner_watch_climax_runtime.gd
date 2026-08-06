extends "res://scripts/game/game_party_medicine_recovery_runtime.gd"

const ENCOUNTER_MUSIC_PHASE_SYSTEM_SCRIPT: Script = preload(
	"res://scripts/systems/encounter_music_phase_system.gd"
)
const PHASE_EVENT_ID: String = "enemy_spell_committed"
const PHASE_SOURCE_ACTOR_ID: String = "training_mage"

var _encounter_music_phase_system: EncounterMusicPhaseSystem = (
	ENCOUNTER_MUSIC_PHASE_SYSTEM_SCRIPT.new() as EncounterMusicPhaseSystem
)
var _vault_phase_source_instance_id: int = 0


func _ready() -> void:
	super._ready()
	call_deferred("_connect_vault_inner_watch_phase_source")


func _start_turn_based_combat(trigger_target: Node) -> void:
	super._start_turn_based_combat(trigger_target)
	call_deferred("_connect_vault_inner_watch_phase_source")


func _connect_vault_inner_watch_phase_source() -> void:
	for candidate: Node in get_tree().get_nodes_in_group("combat_targets"):
		if not is_instance_valid(candidate) or not candidate.has_method("get_actor_id"):
			continue
		if str(candidate.call("get_actor_id")) != PHASE_SOURCE_ACTOR_ID:
			continue
		if not candidate.has_signal("combat_spell_committed"):
			continue
		var callback: Callable = Callable(self, "_on_enemy_spell_committed")
		if not candidate.is_connected("combat_spell_committed", callback):
			candidate.connect("combat_spell_committed", callback)
		_vault_phase_source_instance_id = candidate.get_instance_id()
		return


func _on_enemy_spell_committed(actor_id: String, spell_id: String, spell_level: int) -> void:
	if not _turn_system.active:
		return
	var encounter_id: String = get_active_combat_encounter_id()
	if encounter_id.is_empty():
		return
	var result: Dictionary = _encounter_music_phase_system.evaluate_event(
		encounter_id,
		PHASE_EVENT_ID,
		{
			"actor_id": actor_id,
			"spell_id": spell_id,
			"spell_level": spell_level,
			"round_number": _turn_system.round_number
		},
		get_active_combat_music_profile()
	)
	if not bool(result.get("triggered", false)):
		return
	var profile_id: StringName = StringName(str(result.get("profile_id", "climax")))
	var trigger_id: StringName = StringName(str(result.get("trigger_id", "dangerous_ability")))
	var source_id: String = str(result.get("source_id", actor_id))
	var applied: bool = false
	if profile_id == &"climax":
		applied = request_combat_music_climax(trigger_id, source_id)
	else:
		applied = set_combat_music_profile(profile_id, trigger_id, source_id)
	if not applied:
		return
	var message: String = str(result.get("message", ""))
	if not message.is_empty():
		show_combat_message(message, true)
	GameState.save_game()


func evaluate_vault_inner_watch_music_phase_for_testing(
	context: Dictionary,
	current_profile: StringName = &"standard"
) -> Dictionary:
	return _encounter_music_phase_system.evaluate_event(
		"vault_inner_watch_01",
		PHASE_EVENT_ID,
		context,
		current_profile
	)


func get_vault_phase_source_instance_id_for_testing() -> int:
	return _vault_phase_source_instance_id
