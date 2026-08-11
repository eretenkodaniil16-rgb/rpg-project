extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var system := PartyStealthStateSystem.new()
	system.set_target_state("player_character", true, 21)
	system.set_target_state("companion_irna_guard_01", true, 15)
	system.set_target_state("companion_test_stealth_03", false, 0)
	if system.get_stealth_total("player_character") != 21 or system.get_stealth_total("companion_irna_guard_01") != 15:
		_fail("Independent party stealth totals collapsed into one value.")
		return
	if system.is_hidden("companion_test_stealth_03"):
		_fail("Visible third companion inherited another actor's hidden state.")
		return

	var irina_memory: Dictionary = system.record_sighting(
		"service_guard",
		"vault_watch",
		"companion_irna_guard_01",
		Vector2(420.0, 310.0),
		1.0,
		"visual",
		true
	)
	if str(irina_memory.get("target_actor_id", "")) != "companion_irna_guard_01":
		_fail("Observer memory lost the detected target actor_id.")
		return
	if not system.get_observer_memory("service_guard", "player_character").is_empty():
		_fail("Detecting Irina magically created hero memory.")
		return
	var shared: Dictionary = system.get_squad_memory("vault_watch", "companion_irna_guard_01")
	if shared.is_empty() or str(shared.get("shared_by_actor_id", "")) != "service_guard":
		_fail("Target-specific sighting was not shared with the observer squad.")
		return
	if not system.get_squad_memory("vault_watch", "player_character").is_empty():
		_fail("Squad sharing revealed an unrelated hidden party member.")
		return

	system.record_sighting(
		"service_guard",
		"vault_watch",
		"companion_test_stealth_03",
		Vector2(500.0, 350.0),
		0.55,
		"noise",
		true
	)
	var known: Array[String] = system.get_known_target_ids_for_observer("service_guard")
	if known != ["companion_irna_guard_01", "companion_test_stealth_03"]:
		_fail("Observer target memory is not actor-specific: %s" % JSON.stringify(known))
		return
	var latest: Dictionary = system.get_latest_observer_memory("service_guard")
	if str(latest.get("target_actor_id", "")) != "companion_test_stealth_03" or str(latest.get("source", "")) != "noise":
		_fail("Latest target memory does not preserve source identity.")
		return

	var persisted: Dictionary = system.serialize_persistent_state()
	var restored := PartyStealthStateSystem.new()
	restored.restore_persistent_state(persisted)
	if restored.get_stealth_total("player_character") != 21 or restored.get_stealth_total("companion_irna_guard_01") != 15:
		_fail("Party stealth state did not survive serialization.")
		return
	var restored_memory: Dictionary = restored.get_observer_memory("service_guard", "companion_irna_guard_01")
	if restored_memory.is_empty() or not restored_memory.get("position", null) is Vector2:
		_fail("Target-specific sighting position did not survive serialization.")
		return
	if (restored_memory.get("position", Vector2.ZERO) as Vector2) != Vector2(420.0, 310.0):
		_fail("Restored sighting position changed.")
		return

	restored.clear_target_memory("companion_irna_guard_01")
	if not restored.get_observer_memory("service_guard", "companion_irna_guard_01").is_empty():
		_fail("Target memory cleanup failed.")
		return
	if not restored.get_squad_memory("vault_watch", "companion_irna_guard_01").is_empty():
		_fail("Shared target memory cleanup failed.")
		return

	print("Party Stealth v3 independent states, target memory, squad sharing and persistence passed.")
	quit(0)


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
