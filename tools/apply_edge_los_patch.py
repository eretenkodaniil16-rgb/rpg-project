from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected block not found in {path}: {old[:120]!r}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "scripts/game/combat_environment.gd",
    "func register_edge_blocker(object_id: String, edges: Array, active: bool = true) -> void:",
    "func register_edge_blocker(object_id: String, edges: Array, active: bool = true, blocks_line_of_sight: bool = true) -> void:"
)
replace_once(
    "scripts/game/combat_environment.gd",
    '''\tedge_blockers[object_id] = {
\t\t"active": active,
\t\t"edges": normalized_edges
\t}''',
    '''\tedge_blockers[object_id] = {
\t\t"active": active,
\t\t"blocks_line_of_sight": blocks_line_of_sight,
\t\t"edges": normalized_edges
\t}'''
)
replace_once(
    "scripts/game/combat_environment.gd",
    '''\tfor obstacle: Dictionary in cover_objects:
\t\tif not _obstacle_is_active(obstacle):
\t\t\tcontinue
\t\tvar rect: Rect2 = obstacle.get("rect", Rect2()) as Rect2
\t\tif not _segment_crosses_rect(start, finish, rect):
\t\t\tcontinue
\t\tif bool(obstacle.get("blocks_line_of_sight", false)):
\t\t\ttotal_cover = true
\t\t\tbreak
\t\tbest_bonus = maxi(best_bonus, int(obstacle.get("cover_bonus", 0)))
\treturn {''',
    '''\tfor obstacle: Dictionary in cover_objects:
\t\tif not _obstacle_is_active(obstacle):
\t\t\tcontinue
\t\tvar rect: Rect2 = obstacle.get("rect", Rect2()) as Rect2
\t\tif not _segment_crosses_rect(start, finish, rect):
\t\t\tcontinue
\t\tif bool(obstacle.get("blocks_line_of_sight", false)):
\t\t\ttotal_cover = true
\t\t\tbreak
\t\tbest_bonus = maxi(best_bonus, int(obstacle.get("cover_bonus", 0)))
\tvar grid: BattleGrid = get_tree().get_first_node_in_group("battle_grid") as BattleGrid
\tif not total_cover and _segment_crosses_blocking_edge(grid, attacker_position, target_position):
\t\ttotal_cover = true
\treturn {'''
)
replace_once(
    "scripts/game/combat_environment.gd",
    '''func has_line_of_sight(attacker_position: Vector2, target_position: Vector2) -> bool:
\treturn not bool(get_cover(attacker_position, target_position).get("total_cover", false))


func _rebuild_collision_bodies() -> void:''',
    '''func has_line_of_sight(attacker_position: Vector2, target_position: Vector2) -> bool:
\treturn not bool(get_cover(attacker_position, target_position).get("total_cover", false))


func _segment_crosses_blocking_edge(grid: BattleGrid, sight_start: Vector2, sight_end: Vector2) -> bool:
\tif grid == null or sight_start.is_equal_approx(sight_end):
\t\treturn false
\tfor record_value: Variant in edge_blockers.values():
\t\tif not (record_value is Dictionary):
\t\t\tcontinue
\t\tvar record: Dictionary = record_value as Dictionary
\t\tif not bool(record.get("active", true)) or not bool(record.get("blocks_line_of_sight", true)):
\t\t\tcontinue
\t\tvar edges_value: Variant = record.get("edges", [])
\t\tif not (edges_value is Array):
\t\t\tcontinue
\t\tfor edge_value: Variant in edges_value as Array:
\t\t\tif not (edge_value is Dictionary):
\t\t\t\tcontinue
\t\t\tvar segment: Dictionary = _edge_world_segment(grid, edge_value as Dictionary)
\t\t\tif segment.is_empty():
\t\t\t\tcontinue
\t\t\tif _segments_intersect_strict(
\t\t\t\tsight_start,
\t\t\t\tsight_end,
\t\t\t\tsegment.get("start", Vector2.ZERO) as Vector2,
\t\t\t\tsegment.get("end", Vector2.ZERO) as Vector2
\t\t\t):
\t\t\t\treturn true
\treturn false


func _edge_world_segment(grid: BattleGrid, edge: Dictionary) -> Dictionary:
\tvar first: Vector2i = edge.get("a", INVALID_CELL) as Vector2i
\tvar second: Vector2i = edge.get("b", INVALID_CELL) as Vector2i
\tif first == INVALID_CELL or second == INVALID_CELL:
\t\treturn {}
\tvar first_center: Vector2 = grid.cell_to_world_center(first)
\tvar second_center: Vector2 = grid.cell_to_world_center(second)
\tvar midpoint: Vector2 = (first_center + second_center) * 0.5
\tvar half_cell: float = grid.get_cell_size() * 0.5
\tif first.x != second.x:
\t\treturn {
\t\t\t"start": midpoint + Vector2(0.0, -half_cell),
\t\t\t"end": midpoint + Vector2(0.0, half_cell)
\t\t}
\treturn {
\t\t"start": midpoint + Vector2(-half_cell, 0.0),
\t\t"end": midpoint + Vector2(half_cell, 0.0)
\t}


func _segments_intersect_strict(
\tsight_start: Vector2,
\tsight_end: Vector2,
\tedge_start: Vector2,
\tedge_end: Vector2
) -> bool:
\tvar sight_direction: Vector2 = sight_end - sight_start
\tvar edge_direction: Vector2 = edge_end - edge_start
\tvar denominator: float = sight_direction.cross(edge_direction)
\tif absf(denominator) <= 0.0001:
\t\treturn false
\tvar offset: Vector2 = edge_start - sight_start
\tvar sight_ratio: float = offset.cross(edge_direction) / denominator
\tvar edge_ratio: float = offset.cross(sight_direction) / denominator
\treturn (
\t\tsight_ratio > 0.0001
\t\tand sight_ratio < 0.9999
\t\tand edge_ratio >= -0.0001
\t\tand edge_ratio <= 1.0001
\t)


func _rebuild_collision_bodies() -> void:'''
)

replace_once(
    "scripts/game/game_hidden_escape_runtime.gd",
    '''\t\tshow_combat_message("Скрыться не удалось: хотя бы один противник сохраняет прямую линию обзора.", false)''',
    '''\t\tshow_combat_message(_line_of_sight_failure_message(visible_observers), false)'''
)
replace_once(
    "scripts/game/game_hidden_escape_runtime.gd",
    '''\t_refresh_escape_overlay()
\t_refresh_turn_interface()
\t_refresh_action_catalog()


func _execute_planned_path() -> void:''',
    '''\t_refresh_escape_overlay()
\t_refresh_turn_interface()
\t_refresh_action_catalog()


func _line_of_sight_failure_message(observers: Array[Node]) -> String:
\tvar names: Array[String] = []
\tfor observer: Node in observers:
\t\tif not is_instance_valid(observer):
\t\t\tcontinue
\t\tvar observer_name: String = _target_name(observer)
\t\tif not observer_name.is_empty() and observer_name not in names:
\t\t\tnames.append(observer_name)
\tif names.is_empty():
\t\treturn "Скрыться не удалось: противник сохраняет прямую линию обзора."
\tvar verb: String = "сохраняет" if names.size() == 1 else "сохраняют"
\treturn "Скрыться не удалось: прямую линию обзора %s %s." % [verb, ", ".join(names)]


func _execute_planned_path() -> void:'''
)

replace_once(
    "scripts/game/game_exploration_stealth_runtime.gd",
    '''\tif _player_visible_to_any_exploration_actor():
\t\tshow_combat_message("Скрыться нельзя: Смотритель сохраняет прямую линию обзора.", false)
\t\treturn''',
    '''\tvar visible_observers: Array[Node] = _visible_exploration_observers()
\tif not visible_observers.is_empty():
\t\tshow_combat_message(_line_of_sight_failure_message(visible_observers), false)
\t\treturn'''
)
replace_once(
    "scripts/game/game_exploration_stealth_runtime.gd",
    '''func _player_visible_to_any_exploration_actor() -> bool:
\tfor actor: Node in _exploration_alert_actors():
\t\tvar actor_id: String = str(actor.call("get_actor_id"))
\t\tif _exploration_actor_can_see_player(actor, _stealth_alerts.get_profile(actor_id)):
\t\t\treturn true
\treturn false''',
    '''func _visible_exploration_observers() -> Array[Node]:
\tvar result: Array[Node] = []
\tfor actor: Node in _exploration_alert_actors():
\t\tvar actor_id: String = str(actor.call("get_actor_id"))
\t\tif _exploration_actor_can_see_player(actor, _stealth_alerts.get_profile(actor_id)):
\t\t\tresult.append(actor)
\treturn result


func _player_visible_to_any_exploration_actor() -> bool:
\treturn not _visible_exploration_observers().is_empty()'''
)

replace_once(
    "tests/smoke_movement_wall_integrity.gd",
    '''\t\tif not environment.is_transition_blocked(grid, left_cell, right_cell):
\t\t\t_fail("Closed partition edge does not block movement: %s" % JSON.stringify(edge))
\t\t\treturn

\tvar planner := PlannedMovementSystem.new()''',
    '''\t\tif not environment.is_transition_blocked(grid, left_cell, right_cell):
\t\t\t_fail("Closed partition edge does not block movement: %s" % JSON.stringify(edge))
\t\t\treturn

\tvar wall_los_edge: Dictionary = top_edges[0]
\tvar wall_los_left: Vector2i = wall_los_edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
\tvar wall_los_right: Vector2i = wall_los_edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
\tif environment.has_line_of_sight(grid.cell_to_world_center(wall_los_left), grid.cell_to_world_center(wall_los_right)):
\t\t_fail("A solid wall edge does not block line of sight.")
\t\treturn
\tvar door_los_edge: Dictionary = door_edges[0]
\tvar door_los_left: Vector2i = door_los_edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
\tvar door_los_right: Vector2i = door_los_edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
\tif environment.has_line_of_sight(grid.cell_to_world_center(door_los_left), grid.cell_to_world_center(door_los_right)):
\t\t_fail("A closed door edge does not block line of sight.")
\t\treturn

\tvar planner := PlannedMovementSystem.new()'''
)
replace_once(
    "tests/smoke_movement_wall_integrity.gd",
    '''\tfor edge: Dictionary in door_edges:
\t\tvar left_cell: Vector2i = edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
\t\tvar right_cell: Vector2i = edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
\t\tif environment.is_transition_blocked(grid, left_cell, right_cell):
\t\t\t_fail("Opened door still blocks its cell edge: %s" % JSON.stringify(edge))
\t\t\treturn
\tvar open_result: Dictionary''',
    '''\tfor edge: Dictionary in door_edges:
\t\tvar left_cell: Vector2i = edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
\t\tvar right_cell: Vector2i = edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i
\t\tif environment.is_transition_blocked(grid, left_cell, right_cell):
\t\t\t_fail("Opened door still blocks its cell edge: %s" % JSON.stringify(edge))
\t\t\treturn
\tif not environment.has_line_of_sight(grid.cell_to_world_center(door_los_left), grid.cell_to_world_center(door_los_right)):
\t\t_fail("An opened door edge still blocks line of sight.")
\t\treturn
\tvar open_result: Dictionary'''
)

Path("tests/smoke_edge_line_of_sight_runtime.gd").write_text('''extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_squad_tactical_plans_runtime.gd"
const DOOR_BLOCKER_ID: String = "west_service_door_blocker"


func _init() -> void:
\tcall_deferred("_run")


func _run() -> void:
\tvar state: Node = root.get_node_or_null("GameState")
\tif state == null:
\t\t_fail("GameState autoload is missing.")
\t\treturn
\tvar save_path: String = ProjectSettings.globalize_path("user://savegame.json")
\tif FileAccess.file_exists(save_path):
\t\tDirAccess.remove_absolute(save_path)
\tstate.call("new_game")
\tstate.set("player_character", _make_hero())

\tvar packed: PackedScene = load(GAME_SCENE) as PackedScene
\tif packed == null:
\t\t_fail("Game scene could not be loaded.")
\t\treturn
\tvar game: Node = packed.instantiate()
\troot.add_child(game)
\tfor _frame: int in range(30):
\t\tawait process_frame
\tif str((game.get_script() as Script).resource_path) != EXPECTED_RUNTIME:
\t\t_fail("Game scene does not use the expected tactical runtime.")
\t\treturn

\tvar grid: BattleGrid = game.call("_get_battle_grid") as BattleGrid
\tvar environment: CombatEnvironment = get_first_node_in_group("combat_environment") as CombatEnvironment
\tvar room: Node = game.get_node_or_null("StealthTestRoom")
\tvar player: Node2D = game.get_node_or_null("Player") as Node2D
\tvar caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
\tvar message_label: Label = game.get_node_or_null("Interface/CombatMessageLabel") as Label
\tif grid == null or environment == null or room == null or player == null or caretaker == null or message_label == null:
\t\t_fail("Line-of-sight simulation fixtures are incomplete.")
\t\treturn

\tvar door: Node = room.call("get_test_door") as Node
\tvar guard: Node2D = room.call("get_patrol_observer") as Node2D
\tvar marksman: Node2D = room.call("get_training_marksman") as Node2D
\tvar mage: Node2D = room.call("get_training_mage") as Node2D
\tif door == null or guard == null or marksman == null or mage == null:
\t\t_fail("Door or tactical observers are missing.")
\t\treturn

\tvar door_edges: Array[Dictionary] = environment.get_edge_blocker_edges_for_testing(DOOR_BLOCKER_ID)
\tif door_edges.is_empty():
\t\t_fail("Door edge blocker was not registered.")
\t\treturn
\tvar doorway_edge: Dictionary = door_edges[0]
\tvar doorway_left: Vector2i = doorway_edge.get("a", CombatEnvironment.INVALID_CELL) as Vector2i
\tvar doorway_right: Vector2i = doorway_edge.get("b", CombatEnvironment.INVALID_CELL) as Vector2i

\tdoor.call("set_door_state", "closed", false)
\tplayer.global_position = grid.cell_to_world_center(doorway_left)
\tcaretaker.global_position = grid.cell_to_world_center(doorway_right + Vector2i(3, 0))
\tguard.global_position = grid.cell_to_world_center(doorway_right + Vector2i(2, -2))
\tmarksman.global_position = grid.cell_to_world_center(doorway_right + Vector2i(4, -3))
\tmage.global_position = grid.cell_to_world_center(doorway_right + Vector2i(4, 3))
\tawait process_frame

\tgame.call("_start_turn_based_combat", caretaker)
\tgame.call("force_player_turn_for_testing")
\tgame.set("_enemy_turn_running", false)
\tawait process_frame
\tvar observers: Array[Node] = game.call("_active_observers") as Array[Node]
\tif observers.size() < 4:
\t\t_fail("The complete hostile squad did not join the visibility simulation.")
\t\treturn
\tfor observer: Node in observers:
\t\tif bool(game.call("_observer_can_see_position", observer, player.global_position)):
\t\t\t_fail("Closed edge partition still gives line of sight to %s." % str(game.call("_target_name", observer)))
\t\t\treturn

\tgame.call("set_hide_roll_overrides_for_testing", [20])
\tgame.call("_on_hide_requested")
\tawait process_frame
\tvar combat_state: CombatantState = game.get("_player_combat_state") as CombatantState
\tif combat_state == null or not combat_state.hidden:
\t\t_fail("The player could not hide while every observer was behind the closed partition.")
\t\treturn

\tcombat_state.hidden = false
\tdoor.call("set_door_state", "open", false)
\tplayer.global_position = grid.cell_to_world_center(doorway_left)
\tcaretaker.global_position = grid.cell_to_world_center(doorway_right)
\tgame.call("force_player_turn_for_testing")
\tgame.set("_enemy_turn_running", false)
\tawait process_frame

\tvar visible_observers: Array[Node] = []
\tfor observer: Node in game.call("_active_observers") as Array[Node]:
\t\tif bool(game.call("_observer_can_see_position", observer, player.global_position)):
\t\t\tvisible_observers.append(observer)
\tif visible_observers.is_empty():
\t\t_fail("Opening the doorway did not restore line of sight for any observer.")
\t\treturn
\tgame.call("_on_hide_requested")
\tawait process_frame
\tif combat_state.hidden:
\t\t_fail("The player hid successfully while an observer had direct line of sight through the open doorway.")
\t\treturn
\tif message_label.text.contains("хотя бы один противник"):
\t\t_fail("Hide failure still uses the anonymous observer message.")
\t\treturn
\tfor observer: Node in visible_observers:
\t\tvar observer_name: String = str(game.call("_target_name", observer))
\t\tif not message_label.text.contains(observer_name):
\t\t\t_fail("Hide failure did not name visible observer %s: %s" % [observer_name, message_label.text])
\t\t\treturn

\tgame.queue_free()
\tawait process_frame
\tif FileAccess.file_exists(save_path):
\t\tDirAccess.remove_absolute(save_path)
\tprint("Cell-edge line of sight and named hide observers passed.")
\tquit(0)


func _make_hero() -> PlayerCharacter:
\tvar hero := PlayerCharacter.new()
\thero.character_name = "Испытатель обзора"
\thero.character_class_id = "rogue"
\thero.character_class_name = "Плут"
\thero.race_id = "human"
\thero.race_name = "Человек"
\thero.level = 5
\thero.maximum_health = 42
\thero.current_health = 42
\thero.hit_die_size = 8
\thero.hit_dice_maximum = 5
\thero.hit_dice_current = 5
\thero.abilities["dexterity"] = 18
\thero.base_abilities["dexterity"] = 18
\thero.skill_proficiencies.append("stealth")
\treturn hero


func _fail(message: String) -> void:
\tpush_error(message)
\tquit(1)
'''.replace("\\t", "\t"), encoding="utf-8")

workflow_path = Path(".github/workflows/validate-squad-tactical-plans.yml")
workflow = workflow_path.read_text(encoding="utf-8")
workflow = workflow.replace("permissions:\n  contents: write", "permissions:\n  contents: read", 1)
start_marker = "      - name: Apply edge LOS and named observer patch\n"
end_marker = "      - name: Download Godot 4.7.1 Standard\n"
start = workflow.find(start_marker)
end = workflow.find(end_marker)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("Temporary workflow step markers were not found.")
workflow = workflow[:start] + workflow[end:]
workflow_path.write_text(workflow, encoding="utf-8")
Path("tools/apply_edge_los_patch.py").unlink(missing_ok=True)
