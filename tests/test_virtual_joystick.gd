extends SceneTree


func _init() -> void:
	var inside_dead_zone: Vector2 = VirtualJoystick.calculate_output_vector(Vector2(0.1, 0.0), 0.16)
	assert(inside_dead_zone.is_zero_approx())

	var full_right: Vector2 = VirtualJoystick.calculate_output_vector(Vector2.RIGHT, 0.16)
	assert(full_right.is_equal_approx(Vector2.RIGHT))

	var diagonal: Vector2 = VirtualJoystick.calculate_output_vector(Vector2(0.8, -0.8), 0.16)
	assert(diagonal.x > 0.0)
	assert(diagonal.y < 0.0)
	assert(diagonal.length() <= 1.001)

	var partial: Vector2 = VirtualJoystick.calculate_output_vector(Vector2(0.5, 0.0), 0.16)
	assert(partial.x > 0.0 and partial.x < 1.0)
	assert(is_zero_approx(partial.y))

	print("Virtual joystick tests passed.")
	quit(0)
