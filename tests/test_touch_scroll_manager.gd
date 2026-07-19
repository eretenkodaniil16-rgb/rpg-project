extends SceneTree

const DRAG_DISTANCE_PX: float = 96.0


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var manager: Node = root.get_node_or_null("TouchScrollManager")
	if manager == null:
		_fail("TouchScrollManager autoload is missing.")
		return

	var host: Control = Control.new()
	host.position = Vector2.ZERO
	host.size = Vector2(640.0, 480.0)
	root.add_child(host)

	var horizontal: ScrollContainer = ScrollContainer.new()
	horizontal.position = Vector2(40.0, 40.0)
	horizontal.size = Vector2(240.0, 100.0)
	horizontal.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	horizontal.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	host.add_child(horizontal)
	var wide_content: Control = Control.new()
	wide_content.custom_minimum_size = Vector2(720.0, 80.0)
	horizontal.add_child(wide_content)

	var vertical: ScrollContainer = ScrollContainer.new()
	vertical.position = Vector2(40.0, 180.0)
	vertical.size = Vector2(240.0, 140.0)
	vertical.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vertical.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	host.add_child(vertical)
	var tall_content: Control = Control.new()
	tall_content.custom_minimum_size = Vector2(200.0, 520.0)
	vertical.add_child(tall_content)

	for _frame: int in range(4):
		await process_frame
	manager.call("_configure_existing_scroll_containers")
	await process_frame

	if horizontal.horizontal_scroll_mode != ScrollContainer.SCROLL_MODE_SHOW_NEVER:
		_fail("Horizontal scrollbar was not hidden.")
		return
	if horizontal.vertical_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED:
		_fail("Disabled vertical scrolling was unexpectedly enabled.")
		return
	if vertical.vertical_scroll_mode != ScrollContainer.SCROLL_MODE_SHOW_NEVER:
		_fail("Vertical scrollbar was not hidden.")
		return
	if vertical.horizontal_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED:
		_fail("Disabled horizontal scrolling was unexpectedly enabled.")
		return
	if horizontal.scroll_deadzone != 12 or vertical.scroll_deadzone != 12:
		_fail("Press-and-drag deadzone was not configured.")
		return
	if not horizontal.is_in_group(&"touch_scroll_containers") or not vertical.is_in_group(&"touch_scroll_containers"):
		_fail("Scroll containers were not registered for touch dragging.")
		return

	await _drag_touch(Vector2(180.0, 80.0), Vector2(180.0 - DRAG_DISTANCE_PX, 80.0), 7)
	if horizontal.scroll_horizontal <= 0:
		_fail("Horizontal press-and-drag did not move the content.")
		return

	await _drag_touch(Vector2(120.0, 270.0), Vector2(120.0, 270.0 - DRAG_DISTANCE_PX), 8)
	if vertical.scroll_vertical <= 0:
		_fail("Vertical press-and-drag did not move the content.")
		return

	var horizontal_before_tap: int = horizontal.scroll_horizontal
	await _tap(Vector2(120.0, 80.0), 9)
	if horizontal.scroll_horizontal != horizontal_before_tap:
		_fail("A simple tap changed the scroll position.")
		return

	host.queue_free()
	await process_frame
	print("Native press-and-drag scrolling test passed.")
	quit(0)


func _drag_touch(start: Vector2, finish: Vector2, pointer_id: int) -> void:
	var press: InputEventScreenTouch = InputEventScreenTouch.new()
	press.index = pointer_id
	press.position = start
	press.pressed = true
	root.push_input(press)
	await process_frame

	var drag: InputEventScreenDrag = InputEventScreenDrag.new()
	drag.index = pointer_id
	drag.position = finish
	drag.relative = finish - start
	drag.velocity = drag.relative * 10.0
	root.push_input(drag)
	await process_frame
	await process_frame

	var release: InputEventScreenTouch = InputEventScreenTouch.new()
	release.index = pointer_id
	release.position = finish
	release.pressed = false
	root.push_input(release)
	await process_frame


func _tap(position: Vector2, pointer_id: int) -> void:
	var press: InputEventScreenTouch = InputEventScreenTouch.new()
	press.index = pointer_id
	press.position = position
	press.pressed = true
	root.push_input(press)
	await process_frame
	var release: InputEventScreenTouch = InputEventScreenTouch.new()
	release.index = pointer_id
	release.position = position
	release.pressed = false
	root.push_input(release)
	await process_frame
