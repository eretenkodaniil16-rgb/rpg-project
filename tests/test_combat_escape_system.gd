extends SceneTree

class PassiveObserver:
	extends Node2D
	var passive_value: int = 14

	func get_passive_perception() -> int:
		return passive_value


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var system := CombatEscapeSystem.new()
	var definition: Dictionary = {
		"escape": {
			"policy": "hidden_boundary",
			"edges": ["west", "south"],
			"depth_cells": 1,
			"safe_anchor": [120.0, 240.0],
			"reason_id": "player_escaped_hidden",
			"alert_flag": "guards_alerted",
			"restore_participants": true
		}
	}
	if not system.is_escape_allowed(definition):
		_fail("Hidden boundary escape policy was not recognized.")
		return
	if system.is_escape_allowed({"escape": {"policy": "forbidden"}}):
		_fail("Forbidden encounter unexpectedly allowed escape.")
		return

	var grid := BattleGrid.new()
	grid.field_rect = Rect2(0.0, 0.0, 320.0, 256.0)
	grid.cell_size = 64.0
	root.add_child(grid)
	await process_frame
	var cells: Array[Vector2i] = system.escape_cells(grid, definition)
	if Vector2i(0, 0) not in cells or Vector2i(0, 3) not in cells:
		_fail("West escape edge cells are missing.")
		return
	if Vector2i(4, 3) not in cells or Vector2i(2, 3) not in cells:
		_fail("South escape edge cells are missing.")
		return
	if Vector2i(2, 1) in cells:
		_fail("Interior cell was incorrectly marked as an escape zone.")
		return
	if not system.is_escape_cell(grid, definition, Vector2i(0, 2)):
		_fail("Escape-cell lookup disagrees with calculated cells.")
		return

	var observer := PassiveObserver.new()
	root.add_child(observer)
	var observers: Array[Node] = [observer]
	if system.highest_passive_perception(observers) != 14:
		_fail("Observer passive Perception was not used.")
		return
	if not system.stealth_succeeds(14, observers):
		_fail("A Stealth tie should meet the passive Perception DC.")
		return
	if system.stealth_succeeds(13, observers):
		_fail("Stealth below passive Perception unexpectedly succeeded.")
		return
	if system.perception_modifier(observer) != 4:
		_fail("Active Perception modifier was not derived from passive Perception.")
		return
	if system.get_safe_anchor(definition, Vector2.ZERO) != Vector2(120.0, 240.0):
		_fail("Safe escape anchor was not parsed.")
		return
	if system.get_reason_id(definition) != "player_escaped_hidden":
		_fail("Escape reason ID was not parsed.")
		return
	if system.get_alert_flag(definition) != "guards_alerted":
		_fail("Escape alert flag was not parsed.")
		return
	if not system.should_restore_participants(definition):
		_fail("Participant restore policy was not parsed.")
		return

	grid.queue_free()
	observer.queue_free()
	await process_frame
	print("Hidden combat escape policy, cells and opposed perception tests passed.")
	quit(0)
