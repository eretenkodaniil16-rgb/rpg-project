extends SceneTree


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

	horizontal.scroll_horizontal = 96
	vertical.scroll_vertical = 96
	await process_frame
	if horizontal.scroll_horizontal <= 0:
		_fail("Horizontal scrolling was disabled while hiding its scrollbar.")
		return
	if vertical.scroll_vertical <= 0:
		_fail("Vertical scrolling was disabled while hiding its scrollbar.")
		return

	var dynamic_scroll: ScrollContainer = ScrollContainer.new()
	dynamic_scroll.position = Vector2(340.0, 40.0)
	dynamic_scroll.size = Vector2(200.0, 140.0)
	dynamic_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	dynamic_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	host.add_child(dynamic_scroll)
	var dynamic_content: Control = Control.new()
	dynamic_content.custom_minimum_size = Vector2(180.0, 420.0)
	dynamic_scroll.add_child(dynamic_content)
	for _frame: int in range(3):
		await process_frame
	if dynamic_scroll.vertical_scroll_mode != ScrollContainer.SCROLL_MODE_SHOW_NEVER:
		_fail("A dynamically created scroll container was not configured.")
		return
	if dynamic_scroll.horizontal_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED:
		_fail("Dynamic configuration enabled a disabled axis.")
		return
	if dynamic_scroll.scroll_deadzone != 12 or not dynamic_scroll.is_in_group(&"touch_scroll_containers"):
		_fail("Dynamic scroll container did not receive touch settings.")
		return
	dynamic_scroll.scroll_vertical = 72
	await process_frame
	if dynamic_scroll.scroll_vertical <= 0:
		_fail("Dynamically configured container is not scrollable.")
		return

	host.queue_free()
	await process_frame
	print("Global native scroll configuration test passed.")
	quit(0)
