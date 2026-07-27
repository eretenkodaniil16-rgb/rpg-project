extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var world := Node2D.new()
	root.add_child(world)
	var projectile := RangedProjectile.new()
	world.add_child(projectile)
	projectile.configure("arrow", Color(1.0, 0.75, 0.25, 1.0))
	await projectile.fly(Vector2(20.0, 30.0), Vector2(220.0, 30.0), true)
	await process_frame
	if is_instance_valid(projectile):
		_fail("Projectile was not removed after completing its flight.")
		return
	print("Ranged projectile smoke test passed.")
	quit(0)
