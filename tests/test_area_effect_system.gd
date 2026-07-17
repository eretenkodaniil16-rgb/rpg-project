extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var origin := Vector2.ZERO
	var near := Node2D.new()
	near.name = "Near"
	near.global_position = Vector2(64.0, 0.0)
	root.add_child(near)
	var diagonal := Node2D.new()
	diagonal.name = "Diagonal"
	diagonal.global_position = Vector2(128.0, 64.0)
	root.add_child(diagonal)
	var far := Node2D.new()
	far.name = "Far"
	far.global_position = Vector2(640.0, 0.0)
	root.add_child(far)
	var side := Node2D.new()
	side.name = "Side"
	side.global_position = Vector2(128.0, 180.0)
	root.add_child(side)
	var candidates: Array[Node] = [near, diagonal, far, side]

	var sphere: Array[Node] = AreaEffectSystem.targets_in_sphere(origin, 12, candidates)
	if near not in sphere or diagonal not in sphere or far in sphere:
		_fail("Sphere target selection is incorrect: %s" % sphere)
		return
	var cube: Array[Node] = AreaEffectSystem.targets_in_cube(Vector2(64.0, 0.0), 10, candidates)
	if near not in cube or far in cube:
		_fail("Cube target selection is incorrect: %s" % cube)
		return
	var line: Array[Node] = AreaEffectSystem.targets_in_line(origin, Vector2.RIGHT, 20, 5, candidates)
	if near not in line or diagonal not in line or side in line or far in line:
		_fail("Line target selection is incorrect: %s" % line)
		return
	var cone: Array[Node] = AreaEffectSystem.targets_in_cone(origin, Vector2.RIGHT, 20, candidates)
	if near not in cone or diagonal not in cone or side in cone or far in cone:
		_fail("Cone target selection is incorrect: %s" % cone)
		return
	var sorted: Array[Node] = AreaEffectSystem.sort_by_distance(origin, [far, diagonal, near])
	if sorted.size() != 3 or sorted[0] != near or sorted[2] != far:
		_fail("Area target sorting is incorrect: %s" % sorted)
		return

	near.queue_free()
	diagonal.queue_free()
	far.queue_free()
	side.queue_free()
	await process_frame
	print("Area effect system tests passed.")
	quit(0)
