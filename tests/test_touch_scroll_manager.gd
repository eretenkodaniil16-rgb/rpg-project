extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _screen_touch(index: int, position: Vector2, pressed: bool) -> InputEventScreenTouch:
	var event: InputEventScreenTouch = InputEventScreenTouch.new()
	event.device = 0
	event.index = index
	event.position = position
	event.pressed = pressed
	return event


func _screen_drag(
	index: int,
	position: Vector2,
	relative: Vector2,
	velocity: Vector2
) -> InputEventScreenDrag:
	var event: InputEventScreenDrag = InputEventScreenDrag.new()
	event.device = 0
	event.index = index
	event.position = position
	event.relative = relative
	event.screen_relative = relative
	event.velocity = velocity
	event.screen_velocity = velocity
	return event


func _run() -> void:
	var manager: Node = root.get_node_or_null("TouchScrollManager")
	if manager == null:
		_fail("TouchScrollManager autoload is missing.")
		return

	var host: Control = Control.new()
	host.position = Vector2.ZERO
	host.size = Vector2(960.0, 640.0)
	root.add_child(host)

	var horizontal: ScrollContainer = ScrollContainer.new()
	horizontal.position = Vector2(40.0, 40.0)
	horizontal.size = Vector2(240.0, 100.0)
	horizontal.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	horizontal.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	host.add_child(horizontal)
	var horizontal_button: Button = Button.new()
	horizontal_button.text = "Scrollable button content"
	horizontal_button.custom_minimum_size = Vector2(720.0, 80.0)
	horizontal_button.set_meta("selector_id", "test_card")
	horizontal.add_child(horizontal_button)
	var press_counter: Array[int] = [0]
	horizontal_button.pressed.connect(func() -> void:
		press_counter[0] += 1
	)

	var vertical: ScrollContainer = ScrollContainer.new()
	vertical.position = Vector2(40.0, 180.0)
	vertical.size = Vector2(240.0, 140.0)
	vertical.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vertical.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	host.add_child(vertical)
	var vertical_button: Button = Button.new()
	vertical_button.text = "Tall button content"
	vertical_button.custom_minimum_size = Vector2(200.0, 520.0)
	vertical.add_child(vertical_button)

	var nested_outer: ScrollContainer = ScrollContainer.new()
	nested_outer.position = Vector2(340.0, 40.0)
	nested_outer.size = Vector2(300.0, 300.0)
	nested_outer.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	nested_outer.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	host.add_child(nested_outer)
	var nested_content: Control = Control.new()
	nested_content.custom_minimum_size = Vector2(280.0, 720.0)
	nested_outer.add_child(nested_content)
	var nested_inner: ScrollContainer = ScrollContainer.new()
	nested_inner.position = Vector2(20.0, 80.0)
	nested_inner.size = Vector2(250.0, 110.0)
	nested_inner.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	nested_inner.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	nested_content.add_child(nested_inner)
	var nested_button: Button = Button.new()
	nested_button.text = "Nested horizontal buttons"
	nested_button.custom_minimum_size = Vector2(840.0, 90.0)
	nested_button.set_meta("selector_id", "nested_test_card")
	nested_inner.add_child(nested_button)

	for _frame: int in range(5):
		await process_frame
	manager.call("_configure_existing_scroll_containers")
	await process_frame

	if horizontal.horizontal_scroll_mode != ScrollContainer.SCROLL_MODE_SHOW_NEVER:
		_fail("Horizontal scrollbar was not hidden.")
		return
	if vertical.vertical_scroll_mode != ScrollContainer.SCROLL_MODE_SHOW_NEVER:
		_fail("Vertical scrollbar was not hidden.")
		return
	if horizontal.vertical_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED:
		_fail("Disabled vertical scrolling was unexpectedly enabled.")
		return
	if vertical.horizontal_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED:
		_fail("Disabled horizontal scrolling was unexpectedly enabled.")
		return
	if horizontal.scroll_deadzone != 100000 or vertical.scroll_deadzone != 100000:
		_fail("Native touch scrolling was not disabled before custom gesture handling.")
		return
	if not horizontal.scroll_horizontal_by_default or nested_outer.scroll_horizontal_by_default:
		_fail("Scroll axis defaults were configured incorrectly.")
		return
	if not horizontal.is_in_group(&"touch_scroll_containers") or not nested_inner.is_in_group(&"touch_scroll_containers"):
		_fail("Scroll containers were not registered for custom touch dragging.")
		return

	# A deliberate tap with only tiny finger jitter activates the captured card.
	horizontal.scroll_horizontal = 120
	manager.call("_input", _screen_touch(0, Vector2(120.0, 80.0), true))
	manager.call("_input", _screen_drag(0, Vector2(117.0, 81.0), Vector2(-3.0, 1.0), Vector2(-60.0, 20.0)))
	manager.call("_input", _screen_touch(0, Vector2(117.0, 81.0), false))
	for _frame: int in range(2):
		await process_frame
	if horizontal.scroll_horizontal != 120:
		_fail("A deliberate tap unexpectedly scrolled the list.")
		return
	if press_counter[0] != 1:
		_fail("A deliberate card tap was not activated exactly once.")
		return

	# Movement larger than tap tolerance but smaller than the swipe threshold is
	# intentionally neutral: it must neither select the card nor move the list.
	manager.call("_input", _screen_touch(1, Vector2(120.0, 80.0), true))
	manager.call("_input", _screen_drag(1, Vector2(114.0, 81.0), Vector2(-6.0, 1.0), Vector2(-120.0, 20.0)))
	manager.call("_input", _screen_touch(1, Vector2(114.0, 81.0), false))
	for _frame: int in range(2):
		await process_frame
	if horizontal.scroll_horizontal != 120:
		_fail("A neutral movement unexpectedly scrolled the list.")
		return
	if press_counter[0] != 1:
		_fail("A swipe attempt below the scroll threshold incorrectly selected a card.")
		return

	# Horizontal dragging must work when the touch starts on the same Button and
	# must never activate that Button.
	manager.call("_input", _screen_touch(2, Vector2(120.0, 80.0), true))
	manager.call("_input", _screen_drag(2, Vector2(60.0, 83.0), Vector2(-60.0, 3.0), Vector2(-900.0, 45.0)))
	await process_frame
	var horizontal_after_drag: int = horizontal.scroll_horizontal
	if horizontal_after_drag < 170:
		_fail("Custom horizontal touch dragging did not move button content.")
		return
	manager.call("_input", _screen_touch(2, Vector2(60.0, 83.0), false))
	manager.call("_process", 0.08)
	await process_frame
	if horizontal.scroll_horizontal <= horizontal_after_drag:
		_fail("Horizontal fling inertia did not continue after release.")
		return
	if press_counter[0] != 1:
		_fail("A completed swipe incorrectly activated its starting card.")
		return

	# Touching a moving carousel only stops its inertia. Releasing immediately
	# must not activate the card under the finger.
	manager.call("_input", _screen_touch(3, Vector2(120.0, 80.0), true))
	manager.call("_input", _screen_touch(3, Vector2(120.0, 80.0), false))
	for _frame: int in range(2):
		await process_frame
	if press_counter[0] != 1:
		_fail("Stopping carousel inertia incorrectly activated a card.")
		return

	# Inside a nested horizontal list, horizontal motion belongs to the inner list.
	nested_inner.scroll_horizontal = 140
	nested_outer.scroll_vertical = 0
	manager.call("_input", _screen_touch(4, Vector2(420.0, 160.0), true))
	manager.call("_input", _screen_drag(4, Vector2(350.0, 165.0), Vector2(-70.0, 5.0), Vector2(-500.0, 35.0)))
	manager.call("_input", _screen_touch(4, Vector2(350.0, 165.0), false))
	await process_frame
	if nested_inner.scroll_horizontal < 200:
		_fail("Nested horizontal gesture was not assigned to the inner list.")
		return
	if nested_outer.scroll_vertical != 0:
		_fail("Horizontal nested gesture unexpectedly moved the outer vertical page.")
		return

	# The same starting area must route a vertical gesture to the outer page.
	var inner_before_vertical: int = nested_inner.scroll_horizontal
	manager.call("_input", _screen_touch(5, Vector2(420.0, 160.0), true))
	manager.call("_input", _screen_drag(5, Vector2(425.0, 90.0), Vector2(5.0, -70.0), Vector2(35.0, -500.0)))
	manager.call("_input", _screen_touch(5, Vector2(425.0, 90.0), false))
	await process_frame
	if nested_outer.scroll_vertical < 60:
		_fail("Vertical gesture inside a carousel was not assigned to the outer page.")
		return
	if nested_inner.scroll_horizontal != inner_before_vertical:
		_fail("Vertical nested gesture unexpectedly moved the inner carousel.")
		return

	# ScrollContainers created after scene startup must receive the same handler.
	var dynamic_scroll: ScrollContainer = ScrollContainer.new()
	dynamic_scroll.position = Vector2(700.0, 40.0)
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
	if dynamic_scroll.scroll_deadzone != 100000 or not dynamic_scroll.is_in_group(&"touch_scroll_containers"):
		_fail("Dynamic scroll container did not receive the custom touch handler.")
		return

	host.queue_free()
	await process_frame
	print("Captured card tap discrimination, custom touch routing, and inertia test passed.")
	quit(0)
