extends SceneTree

class FakeState:
	extends Node
	var flags: Dictionary = {}

	func get_flag(flag_name: String, default_value: Variant = null) -> Variant:
		return flags.get(flag_name, default_value)

	func set_flag(flag_name: String, value: Variant) -> void:
		flags[flag_name] = value


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var system := StealthAlertSystem.new()
	var state := FakeState.new()
	root.add_child(state)
	if not system.ensure_state(state):
		_fail("Stealth registry was not initialized.")
		return
	if system.get_profile("caretaker").is_empty():
		_fail("Caretaker stealth profile is missing.")
		return
	if system.get_room_id_at(Vector2(100.0, 100.0)) != "west_service_room":
		_fail("West service room lookup failed.")
		return
	if system.get_room_id_at(Vector2(900.0, 360.0)) != "main_hall":
		_fail("Main hall lookup failed.")
		return
	if system.get_hiding_spot_at(Vector2(100.0, 100.0)).is_empty():
		_fail("Data-driven hiding spot lookup failed.")
		return

	var profile: Dictionary = system.get_profile("caretaker")
	if not system.can_see_target(Vector2.ZERO, Vector2.RIGHT, Vector2(192.0, 0.0), profile, true, false):
		_fail("Target in the primary view cone was not visible.")
		return
	if system.can_see_target(Vector2.ZERO, Vector2.LEFT, Vector2(288.0, 0.0), profile, true, false):
		_fail("Target behind the observer was visible outside peripheral range.")
		return
	if system.can_see_target(Vector2.ZERO, Vector2.RIGHT, Vector2(96.0, 0.0), profile, false, false):
		_fail("Blocked line of sight still detected the target.")
		return
	if system.can_see_target(Vector2.ZERO, Vector2.RIGHT, Vector2(192.0, 0.0), profile, true, true):
		_fail("A fully concealed distant target remained visible.")
		return

	if not system.door_blocks_line_of_sight(state, Vector2(900.0, 360.0), Vector2(100.0, 360.0)):
		_fail("Closed service door did not block line of sight.")
		return
	if not system.set_door_state(state, "west_service_door", "open"):
		_fail("Door state could not be changed.")
		return
	if system.door_blocks_line_of_sight(state, Vector2(900.0, 360.0), Vector2(100.0, 360.0)):
		_fail("Open service door still blocked line of sight.")
		return
	var open_noise: float = system.noise_multiplier_between_rooms(state, "west_service_room", "main_hall")
	system.set_door_state(state, "west_service_door", "closed")
	var closed_noise: float = system.noise_multiplier_between_rooms(state, "west_service_room", "main_hall")
	if closed_noise >= open_noise:
		_fail("Closed door did not damp cross-room noise.")
		return

	var record: Dictionary = system.get_actor_record(state, "caretaker")
	record = system.apply_visual_observation(record, true, false, Vector2(500.0, 300.0), 1.0, profile)
	if float(record.get("suspicion", 0.0)) <= 0.0 or str(record.get("state", "")) != StealthAlertSystem.STATE_SUSPICIOUS:
		_fail("Visible player did not raise suspicion.")
		return
	record = system.apply_visual_observation(record, true, false, Vector2(500.0, 300.0), 2.0, profile)
	if str(record.get("state", "")) != StealthAlertSystem.STATE_ALERTED:
		_fail("Sustained observation did not reach alert state.")
		return

	var noise_event: Dictionary = {
		"noise_type": "weapon",
		"position": [460.0, 360.0],
		"room_id": "main_hall",
		"radius_feet": 55,
		"intensity": 62
	}
	var noise_record: Dictionary = system.apply_noise(system.get_actor_record(state, "caretaker"), noise_event, profile)
	if str(noise_record.get("state", "")) != StealthAlertSystem.STATE_INVESTIGATING:
		_fail("Audible noise did not create an investigation.")
		return
	if not system.actor_hears_noise(state, Vector2(900.0, 360.0), "main_hall", noise_event, profile):
		_fail("Actor inside the noise radius did not hear it.")
		return

	var stored: Dictionary = system.store_actor_record(state, "caretaker", noise_record)
	var restored: Dictionary = system.get_actor_record(state, "caretaker")
	if str(restored.get("state", "")) != str(stored.get("state", "")):
		_fail("Alert record was not preserved in the registry.")
		return
	var stored_noise: Dictionary = system.append_noise_event(state, noise_event)
	if system.get_noise_events(state, int(stored_noise.get("sequence", 0)) - 1).size() != 1:
		_fail("Noise event sequence filtering failed.")
		return

	state.queue_free()
	print("Exploration stealth profiles, vision, doors, noise, suspicion and persistence tests passed.")
	quit(0)
