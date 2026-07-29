extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var system := PatrolAlertGroupSystem.new()
	if not system.has_actor_config("caretaker") or not system.has_actor_config("service_guard"):
		_fail("Patrol alert actor configs are missing.")
		return
	if system.get_alert_group_id("caretaker") != "vault_watch" or system.get_alert_group_id("service_guard") != "vault_watch":
		_fail("Alert group membership is incorrect.")
		return
	if system.can_start_combat("service_guard") or not system.can_start_combat("caretaker"):
		_fail("Combat-start capability is not separated from observation.")
		return
	var initial_position: Vector2 = system.get_initial_patrol_position("service_guard")
	if initial_position != Vector2(760.0, 160.0):
		_fail("Patrol route initial position is invalid.")
		return

	var record: Dictionary = {"actor_id": "service_guard", "state": StealthAlertSystem.STATE_CALM}
	var patrol: Dictionary = system.advance_patrol("service_guard", record, Vector2(700.0, 160.0), 0.5)
	if not bool(patrol.get("active", false)) or not bool(patrol.get("moved", false)):
		_fail("Calm patrol did not move toward its waypoint.")
		return
	var moved_position: Vector2 = patrol.get("position", Vector2.ZERO) as Vector2
	if moved_position.x <= 700.0 or moved_position.x > 760.0:
		_fail("Patrol movement exceeded its configured speed or direction.")
		return
	record = patrol.get("record", {}) as Dictionary
	patrol = system.advance_patrol("service_guard", record, Vector2(760.0, 160.0), 0.4)
	record = patrol.get("record", {}) as Dictionary
	if float(record.get("patrol_wait_remaining", 0.0)) <= 0.0:
		_fail("Patrol waypoint wait time was not applied.")
		return
	patrol = system.advance_patrol("service_guard", record, Vector2(760.0, 160.0), 0.5)
	record = patrol.get("record", {}) as Dictionary
	patrol = system.advance_patrol("service_guard", record, Vector2(760.0, 160.0), 0.0)
	record = patrol.get("record", {}) as Dictionary
	if int(record.get("patrol_waypoint_index", -1)) != 1:
		_fail("Ping-pong patrol did not advance to the next waypoint.")
		return

	if not system.can_relay_alert("service_guard", "caretaker", Vector2(760.0, 160.0), Vector2(900.0, 360.0), 1.0):
		_fail("Nearby members of one alert group could not relay an alert.")
		return
	if system.can_relay_alert("service_guard", "caretaker", Vector2(100.0, 360.0), Vector2(900.0, 360.0), 1.0):
		_fail("Alert relay ignored its maximum radius.")
		return
	if system.can_relay_alert("service_guard", "caretaker", Vector2(100.0, 360.0), Vector2(500.0, 360.0), 0.38):
		_fail("Closed-room audibility did not reduce alert relay range.")
		return

	var listener_record: Dictionary = {
		"actor_id": "caretaker",
		"state": StealthAlertSystem.STATE_CALM,
		"suspicion": 0.0,
		"last_known_position": [0.0, 0.0]
	}
	var source_record: Dictionary = {
		"actor_id": "service_guard",
		"state": StealthAlertSystem.STATE_ALERTED,
		"suspicion": 100.0,
		"last_known_position": [520.0, 360.0]
	}
	var relayed: Dictionary = system.apply_alert_relay(
		"caretaker",
		listener_record,
		"service_guard",
		source_record,
		{"search_duration_seconds": 12.0, "alert_cooldown_seconds": 24.0}
	)
	if str(relayed.get("state", "")) != StealthAlertSystem.STATE_INVESTIGATING:
		_fail("Alert relay did not start an investigation.")
		return
	if str(relayed.get("last_alert_source_id", "")) != "service_guard":
		_fail("Alert relay source ID was not recorded.")
		return
	if relayed.get("last_known_position", []) != [520.0, 360.0]:
		_fail("Alert relay lost the source's last known position.")
		return

	print("Patrol routes, waits, alert groups, audibility and relay state tests passed.")
	quit(0)
