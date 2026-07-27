extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var origin := Vector2(100.0, 100.0)
	var near := Node2D.new()
	near.position = Vector2(228.0, 100.0)
	root.add_child(near)
	var far := Node2D.new()
	far.position = Vector2(420.0, 100.0)
	root.add_child(far)
	var side := Node2D.new()
	side.position = Vector2(220.0, 180.0)
	root.add_child(side)
	var behind := Node2D.new()
	behind.position = Vector2(20.0, 100.0)
	root.add_child(behind)

	var candidates: Array[Node] = [far, side, behind, near]
	var chosen: Node = DirectionalTargetingSystem.find_first_target(origin, Vector2.RIGHT, candidates, 500.0)
	if chosen != near:
		_fail("Free aim must choose the nearest target in front of the player.")
		return
	var left_target: Node = DirectionalTargetingSystem.find_first_target(origin, Vector2.LEFT, candidates, 500.0)
	if left_target != behind:
		_fail("Free aim must respect the current facing direction.")
		return
	var no_target: Node = DirectionalTargetingSystem.find_first_target(origin, Vector2.UP, candidates, 500.0)
	if no_target != null:
		_fail("Targets outside the firing corridor must be ignored.")
		return
	if absf(DirectionalTargetingSystem.feet_to_pixels(5) - 64.0) > 0.01:
		_fail("Five feet must equal one 64-pixel cell.")
		return
	var endpoint: Vector2 = DirectionalTargetingSystem.endpoint_inside_rect(
		Vector2(320.0, 360.0),
		Vector2.RIGHT,
		2000.0,
		Rect2(45.0, 45.0, 1190.0, 630.0)
	)
	if endpoint.x >= 1235.0 or absf(endpoint.y - 360.0) > 0.01:
		_fail("Free aim endpoint must remain inside the combat field.")
		return

	near.queue_free()
	far.queue_free()
	side.queue_free()
	behind.queue_free()
	print("Directional targeting tests passed.")
	quit(0)
