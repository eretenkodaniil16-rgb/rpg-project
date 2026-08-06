extends SceneTree

const PHASE_SYSTEM_SCRIPT: Script = preload(
	"res://scripts/systems/encounter_music_phase_system.gd"
)


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var system: EncounterMusicPhaseSystem = PHASE_SYSTEM_SCRIPT.new() as EncounterMusicPhaseSystem
	var base_context: Dictionary = {
		"actor_id": "training_mage",
		"spell_id": "thunderwave",
		"spell_level": 1,
		"round_number": 2
	}
	var result: Dictionary = system.evaluate_event(
		"vault_inner_watch_01",
		"enemy_spell_committed",
		base_context,
		&"standard"
	)
	if not bool(result.get("triggered", false)):
		_fail("Rune overload phase was not triggered by a committed levelled spell in round two.")
		return
	if str(result.get("phase_id", "")) != "rune_overload":
		_fail("Unexpected phase id.")
		return
	if StringName(str(result.get("profile_id", ""))) != &"climax":
		_fail("Rune overload must request climax profile.")
		return
	if StringName(str(result.get("trigger_id", ""))) != &"dangerous_ability":
		_fail("Rune overload must use dangerous_ability trigger.")
		return

	var first_round: Dictionary = base_context.duplicate(true)
	first_round["round_number"] = 1
	if bool(system.evaluate_event("vault_inner_watch_01", "enemy_spell_committed", first_round, &"standard").get("triggered", false)):
		_fail("The opening round must remain on standard combat music.")
		return

	var wrong_actor: Dictionary = base_context.duplicate(true)
	wrong_actor["actor_id"] = "training_marksman"
	if bool(system.evaluate_event("vault_inner_watch_01", "enemy_spell_committed", wrong_actor, &"standard").get("triggered", false)):
		_fail("Marksman actions must not trigger rune overload.")
		return

	var cantrip: Dictionary = base_context.duplicate(true)
	cantrip["spell_level"] = 0
	if bool(system.evaluate_event("vault_inner_watch_01", "enemy_spell_committed", cantrip, &"standard").get("triggered", false)):
		_fail("A cantrip must not trigger the dangerous ability phase.")
		return

	if bool(system.evaluate_event("vault_guard_post_01", "enemy_spell_committed", base_context, &"standard").get("triggered", false)):
		_fail("Other encounters must remain unchanged.")
		return
	if bool(system.evaluate_event("vault_inner_watch_01", "enemy_spell_committed", base_context, &"climax").get("triggered", false)):
		_fail("Restored or active climax must not retrigger the phase.")
		return
	if bool(system.evaluate_event("vault_inner_watch_01", "enemy_spell_committed", base_context, &"scripted").get("triggered", false)):
		_fail("Scripted music control must not be overridden.")
		return

	print("Encounter music phase system tests passed.")
	quit(0)


func _init() -> void:
	call_deferred("_run")
