extends SceneTree

class PassiveObserver:
	extends Node2D
	var passive_value: int = 14
	var tracking_value: int = 3

	func get_passive_perception() -> int:
		return passive_value

	func get_tracking_modifier() -> int:
		return tracking_value


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var system := CombatEscapeSystem.new()
	var definition: Dictionary = {
		"escape": {
			"policy": "pursuit_routes",
			"default_required_search_sweeps": 2,
			"safe_anchor": [120.0, 240.0],
			"reason_id": "player_escaped_after_pursuit",
			"alert_flag": "guards_alerted",
			"restore_participants": true,
			"routes": [
				{
					"id": "secret_niche",
					"type": "hideout",
					"label": "Секретная ниша",
					"objective_cells": [[4, 3]],
					"concealment_bonus": 6,
					"trace_dc_bonus": 4,
					"required_search_sweeps": 3,
					"safe_anchor": [90.0, 180.0]
				},
				{
					"id": "side_room",
					"type": "room_transition",
					"transition_cells": [[1, 2]],
					"destination_cells": [[0, 1], [0, 2], [0, 3], [1, 1], [1, 2], [1, 3]],
					"hide_cells": [[0, 1], [0, 3]],
					"requires_rehide": true,
					"blocks_cross_room_los": true,
					"concealment_bonus": 3,
					"trace_dc_bonus": 2
				}
			]
		}
	}
	if not system.is_escape_allowed(definition):
		_fail("Pursuit-route escape policy was not recognized.")
		return
	if system.is_escape_allowed({"escape": {"policy": "forbidden"}}):
		_fail("Forbidden encounter unexpectedly allowed escape.")
		return

	var routes: Array[Dictionary] = system.get_routes(definition)
	if routes.size() != 2:
		_fail("Escape routes were not parsed.")
		return
	var hideout: Dictionary = system.get_route(definition, "secret_niche")
	var room: Dictionary = system.get_route(definition, "side_room")
	if system.get_route_type(hideout) != CombatEscapeSystem.ROUTE_HIDEOUT:
		_fail("Hideout route type was not parsed.")
		return
	if system.find_hide_route(definition, Vector2i(4, 3)).get("id", "") != "secret_niche":
		_fail("Hideout cell did not resolve to its route.")
		return
	var room_path: Array[Vector2i] = [Vector2i(2, 2), Vector2i(1, 2), Vector2i(0, 2)]
	if system.find_room_transition_route(definition, room_path).get("id", "") != "side_room":
		_fail("Crossing the doorway did not resolve the room route.")
		return
	if not system.route_requires_rehide(room):
		_fail("Room route did not require a second Hide action.")
		return
	if system.get_concealment_bonus(hideout) != 6 or system.get_trace_dc_bonus(hideout) != 4:
		_fail("Hideout concealment or trace difficulty was not parsed.")
		return
	if system.get_required_search_sweeps(hideout, definition) != 3:
		_fail("Route-specific search sweep requirement was not parsed.")
		return
	if system.get_tracking_dc(18, hideout) != 22 or system.get_search_dc(18, hideout) != 24:
		_fail("Tracking and final search DCs do not include route difficulty.")
		return
	if system.get_safe_anchor(definition, Vector2.ZERO, hideout) != Vector2(90.0, 180.0):
		_fail("Route-specific safe anchor was not parsed.")
		return

	var grid := BattleGrid.new()
	grid.field_rect = Rect2(0.0, 0.0, 320.0, 256.0)
	grid.cell_size = 64.0
	root.add_child(grid)
	await process_frame
	var overlay: Dictionary = system.overlay_cells(definition)
	if Vector2i(4, 3) not in (overlay.get("hideout", []) as Array[Vector2i]):
		_fail("Hideout overlay cell is missing.")
		return
	if Vector2i(1, 2) not in (overlay.get("transition", []) as Array[Vector2i]):
		_fail("Room transition overlay cell is missing.")
		return
	if Vector2i(0, 1) not in (overlay.get("destination", []) as Array[Vector2i]):
		_fail("Room re-hide cell is missing.")
		return
	if not system.blocks_cross_room_line_of_sight(
		grid,
		definition,
		grid.cell_to_world_center(Vector2i(3, 2)),
		grid.cell_to_world_center(Vector2i(0, 2))
	):
		_fail("Room boundary did not block cross-room line of sight.")
		return
	if system.blocks_cross_room_line_of_sight(
		grid,
		definition,
		grid.cell_to_world_center(Vector2i(0, 1)),
		grid.cell_to_world_center(Vector2i(0, 3))
	):
		_fail("Actors in the same room incorrectly lost line of sight.")
		return

	var observer := PassiveObserver.new()
	root.add_child(observer)
	var observers: Array[Node] = [observer]
	if system.highest_passive_perception(observers) != 14:
		_fail("Observer passive Perception was not used.")
		return
	if not system.stealth_succeeds(14, observers) or system.stealth_succeeds(13, observers):
		_fail("Stealth opposed by passive Perception is incorrect.")
		return
	if system.perception_modifier(observer) != 4 or system.tracking_modifier(observer) != 3:
		_fail("Perception or tracking modifier was not resolved.")
		return
	if system.get_alert_flag(definition) != "guards_alerted" or not system.should_restore_participants(definition):
		_fail("Persistent escape consequences were not parsed.")
		return

	grid.queue_free()
	observer.queue_free()
	await process_frame
	print("Pursuit routes, hidden places, room transitions, tracking and search DC tests passed.")
	quit(0)
