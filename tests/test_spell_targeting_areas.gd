extends SceneTree


class BlockingEnvironment:
	extends Node
	var wall_x: float = 0.0

	func has_line_of_sight(start: Vector2, finish: Vector2) -> bool:
		return not (start.x < wall_x and finish.x > wall_x)


class AreaTarget:
	extends Node2D
	var combat_name: String = "Цель"
	var saving_throw_modifier: int = 0

	func get_combat_name() -> String:
		return combat_name

	func get_saving_throw_modifier(_ability_id: String) -> int:
		return saving_throw_modifier


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _casting_context(turn_token: String) -> Dictionary:
	return {
		"can_speak": true,
		"armor_trained": true,
		"free_hands": 1,
		"focus_in_hand": true,
		"has_component_pouch": false,
		"has_required_material": true,
		"turn_token": turn_token
	}


func _run() -> void:
	var grid := BattleGrid.new()
	grid.field_rect = Rect2(0.0, 0.0, 640.0, 640.0)
	grid.cell_size = 64.0
	root.add_child(grid)
	await process_frame

	var areas := SpellAreaSystem.new()
	var caster_cell := Vector2i(4, 4)

	var sphere: Array[Vector2i] = areas.get_area_cells(grid, caster_cell, Vector2i(5, 5), {
		"shape": "sphere", "origin": "point", "radius_ft": 10
	})
	if Vector2i(5, 5) not in sphere or Vector2i(7, 5) not in sphere or Vector2i(8, 5) in sphere:
		_fail("Sphere footprint did not use its selected point and radius.")
		return

	var cone: Array[Vector2i] = areas.get_area_cells(grid, caster_cell, Vector2i(8, 4), {
		"shape": "cone", "origin": "self", "length_ft": 15, "include_origin": false
	})
	if caster_cell in cone or Vector2i(5, 4) not in cone or Vector2i(7, 4) not in cone or Vector2i(4, 7) in cone:
		_fail("Cone footprint did not extend from the caster in the chosen direction.")
		return

	var cube: Array[Vector2i] = areas.get_area_cells(grid, caster_cell, Vector2i(8, 4), {
		"shape": "cube", "origin": "self", "size_ft": 15, "include_origin": false
	})
	if Vector2i(5, 3) not in cube or Vector2i(7, 5) not in cube or caster_cell in cube:
		_fail("Cube footprint did not extend from its origin face.")
		return

	var cylinder: Array[Vector2i] = areas.get_area_cells(grid, caster_cell, Vector2i(5, 5), {
		"shape": "cylinder", "origin": "point", "radius_ft": 10, "height_ft": 20
	})
	if Vector2i(5, 5) not in cylinder or Vector2i(7, 7) not in cylinder:
		_fail("Cylinder did not expose its circular top-down footprint.")
		return

	var emanation: Array[Vector2i] = areas.get_area_cells(grid, caster_cell, Vector2i(8, 4), {
		"shape": "emanation", "origin": "self", "distance_ft": 10, "include_origin": false
	})
	if caster_cell in emanation or Vector2i(6, 4) not in emanation or Vector2i(7, 4) in emanation:
		_fail("Emanation did not move outward from the caster while excluding its origin.")
		return

	var line: Array[Vector2i] = areas.get_area_cells(grid, caster_cell, Vector2i(8, 4), {
		"shape": "line", "origin": "self", "length_ft": 20, "width_ft": 5, "include_origin": true
	})
	if caster_cell not in line or Vector2i(8, 4) not in line or Vector2i(6, 5) in line:
		_fail("Line footprint did not preserve its configured length and width.")
		return

	grid.set_spell_area_preview(cone, caster_cell)
	if not grid.is_spell_area_preview_active() or grid.get_spell_area_preview_cells() != cone:
		_fail("BattleGrid did not retain the spell-area preview.")
		return
	grid.clear_spell_area_preview()
	if grid.is_spell_area_preview_active():
		_fail("BattleGrid did not clear the spell-area preview.")
		return

	var environment := BlockingEnvironment.new()
	environment.wall_x = grid.cell_to_world_center(Vector2i(5, 4)).x
	root.add_child(environment)
	var origin_world: Vector2 = grid.cell_to_world_center(caster_cell)
	var blocked_cells: Array[Vector2i] = areas.filter_cells_by_total_cover(grid, line, origin_world, environment)
	if Vector2i(8, 4) in blocked_cells or caster_cell not in blocked_cells:
		_fail("Total Cover did not remove blocked cells from the area.")
		return
	var clipped_origin: Vector2 = areas.resolve_point_of_origin(origin_world, grid.cell_to_world_center(Vector2i(8, 4)), environment)
	if clipped_origin.x > environment.wall_x:
		_fail("An unseen point of origin was not clipped to the near side of Total Cover.")
		return

	var visible_target := AreaTarget.new()
	visible_target.position = grid.cell_to_world_center(Vector2i(4, 4))
	root.add_child(visible_target)
	var blocked_target := AreaTarget.new()
	blocked_target.position = grid.cell_to_world_center(Vector2i(8, 4))
	root.add_child(blocked_target)
	var collected: Array[Node] = areas.collect_targets(grid, line, [visible_target, blocked_target], origin_world, environment)
	if visible_target not in collected or blocked_target in collected:
		_fail("Area target collection ignored the Total Cover boundary.")
		return

	var spells := SpellcastingSystem.new()
	var abilities := ClassAbilitySystem.new()
	var wizard := PlayerCharacter.new()
	wizard.character_class_id = "wizard"
	wizard.character_class_name = "Волшебник"
	wizard.level = 5
	wizard.abilities["intelligence"] = 18
	wizard.base_abilities["intelligence"] = 18
	spells.ensure_character(wizard, false)
	var burning_hands: Dictionary = spells.get_spell_definition("burning_hands")
	if burning_hands.is_empty() or not spells.is_prepared(wizard, "burning_hands"):
		_fail("Burning Hands was not available as the first executable area spell.")
		return
	spells.set_selected_slot_level(wizard, "burning_hands", 2)
	var level_two_before: int = wizard.get_resource("spell_slots_2")
	var failed_save_target := AreaTarget.new()
	failed_save_target.combat_name = "Провалившая спасбросок цель"
	var successful_save_target := AreaTarget.new()
	successful_save_target.combat_name = "Успешная цель"
	root.add_child(failed_save_target)
	root.add_child(successful_save_target)
	var area_result: Dictionary = abilities.perform_area_spell(
		wizard,
		burning_hands,
		[
			{"target": failed_save_target, "target_name": failed_save_target.combat_name, "defender_state": CombatantState.new(), "target_save_modifier": 0, "save_rolls_override": [1]},
			{"target": successful_save_target, "target_name": successful_save_target.combat_name, "defender_state": CombatantState.new(), "target_save_modifier": 0, "save_rolls_override": [20]}
		],
		_casting_context("area_turn_1"),
		[6, 6, 6, 6]
	)
	if not bool(area_result.get("success", false)) or int(area_result.get("slot_level", 0)) != 2:
		_fail("Area spell did not resolve with the selected level-two slot.")
		return
	if wizard.get_resource("spell_slots_2") != level_two_before - 1:
		_fail("Area spell consumed more or less than one selected spell slot.")
		return
	var resolutions: Array = area_result.get("resolutions", []) as Array
	if resolutions.size() != 2:
		_fail("Area spell did not produce one resolution per unique target.")
		return
	var first_result: AttackResult = (resolutions[0] as Dictionary).get("result") as AttackResult
	var second_result: AttackResult = (resolutions[1] as Dictionary).get("result") as AttackResult
	if first_result == null or second_result == null or first_result.damage != 24 or second_result.damage != 12:
		_fail("Area spell did not share one damage roll and halve it on a successful save.")
		return

	spells.set_selected_slot_level(wizard, "burning_hands", 1)
	var level_one_before: int = wizard.get_resource("spell_slots_1")
	var empty_area_result: Dictionary = abilities.perform_area_spell(
		wizard,
		burning_hands,
		[],
		_casting_context("area_turn_2"),
		[2, 2, 2]
	)
	if not bool(empty_area_result.get("success", false)) or int(empty_area_result.get("targets_count", -1)) != 0:
		_fail("A valid empty area should complete even when it catches no creatures.")
		return
	if wizard.get_resource("spell_slots_1") != level_one_before - 1:
		_fail("An empty but valid area did not consume exactly one spell slot.")
		return

	print("Spell area geometry, Total Cover, preview, multi-target saves, shared damage and slot tests passed.")
	quit(0)
