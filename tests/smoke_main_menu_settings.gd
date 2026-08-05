extends SceneTree

const MAIN_MENU_SCENE: String = "res://scenes/menus/main_menu.tscn"
const MASTER_BUS: StringName = &"Master"
const MUSIC_BUS: StringName = &"Music"


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var music_manager: Node = root.get_node_or_null("MusicManager")
	assert(music_manager != null, "MusicManager autoload is missing")
	assert(music_manager.has_method("get_bus_volume_linear"), "MusicManager volume getter is missing")
	assert(music_manager.has_method("set_bus_volume_linear"), "MusicManager volume setter is missing")
	var original_reduced_motion: bool = InterfaceSettingsStore.load_and_apply()
	var original_master_volume: float = float(
		music_manager.call("get_bus_volume_linear", MASTER_BUS)
	)
	var original_music_volume: float = float(
		music_manager.call("get_bus_volume_linear", MUSIC_BUS)
	)

	var packed: PackedScene = load(MAIN_MENU_SCENE) as PackedScene
	assert(packed != null, "Main menu scene must load")
	var menu: Control = packed.instantiate() as Control
	assert(menu != null, "Main menu scene must instantiate")
	root.add_child(menu)
	await process_frame
	await process_frame

	var settings_button: Button = menu.get_node_or_null(
		"CenterContainer/MenuPanel/MarginContainer/VBoxContainer/SettingsButton"
	) as Button
	var settings_panel: MainMenuSettingsPanel = menu.get_node_or_null(
		"SettingsLayer"
	) as MainMenuSettingsPanel
	var atmosphere: MainMenuAtmosphere = menu.get_node_or_null("Atmosphere") as MainMenuAtmosphere
	var title_glow: MainMenuTitleGlow = menu.get_node_or_null("TitleGlow") as MainMenuTitleGlow
	assert(settings_button != null, "Settings button is missing")
	assert(settings_panel != null, "Settings panel is missing")
	assert(atmosphere != null, "Menu atmosphere is missing")
	assert(title_glow != null, "Title glow is missing")
	assert(not settings_panel.is_open(), "Settings panel must start closed")

	settings_button.pressed.emit()
	await process_frame
	assert(settings_panel.is_open(), "Settings panel must open from the menu button")
	assert(settings_button.focus_mode == Control.FOCUS_NONE, "Background menu must lose focus")

	var master_slider: HSlider = settings_panel.get_node_or_null(
		"CenterContainer/Panel/Margin/Content/MasterRow/MasterVolumeSlider"
	) as HSlider
	var music_slider: HSlider = settings_panel.get_node_or_null(
		"CenterContainer/Panel/Margin/Content/MusicRow/MusicVolumeSlider"
	) as HSlider
	var reduced_motion_toggle: CheckButton = settings_panel.get_node_or_null(
		"CenterContainer/Panel/Margin/Content/ReducedMotionRow/ReducedMotionToggle"
	) as CheckButton
	assert(master_slider != null, "Master volume slider is missing")
	assert(music_slider != null, "Music volume slider is missing")
	assert(reduced_motion_toggle != null, "Reduced motion toggle is missing")
	assert(master_slider.custom_minimum_size.y >= 54.0, "Master slider touch target is too small")
	assert(music_slider.custom_minimum_size.y >= 54.0, "Music slider touch target is too small")

	master_slider.value = 37.0
	music_slider.value = 46.0
	await process_frame
	assert(
		is_equal_approx(
			float(music_manager.call("get_bus_volume_linear", MASTER_BUS)),
			0.37
		),
		"Master volume was not applied through MusicManager"
	)
	assert(
		is_equal_approx(
			float(music_manager.call("get_bus_volume_linear", MUSIC_BUS)),
			0.46
		),
		"Music volume was not applied through MusicManager"
	)

	var test_reduced_motion: bool = not original_reduced_motion
	reduced_motion_toggle.button_pressed = test_reduced_motion
	await process_frame
	assert(
		InterfaceSettingsStore.is_reduced_motion_enabled() == test_reduced_motion,
		"Reduced motion setting was not persisted"
	)
	assert(
		atmosphere.is_reduced_motion_enabled() == test_reduced_motion,
		"Atmosphere did not apply reduced motion"
	)
	assert(
		title_glow.is_reduced_motion_enabled() == test_reduced_motion,
		"Title glow did not apply reduced motion"
	)

	settings_panel.close()
	await process_frame
	assert(not settings_panel.is_open(), "Settings panel must close")
	assert(settings_button.focus_mode == Control.FOCUS_ALL, "Menu focus must be restored")

	music_manager.call(
		"set_bus_volume_linear",
		MASTER_BUS,
		original_master_volume,
		true
	)
	music_manager.call(
		"set_bus_volume_linear",
		MUSIC_BUS,
		original_music_volume,
		true
	)
	InterfaceSettingsStore.set_reduced_motion_enabled(original_reduced_motion)
	menu.queue_free()
	await process_frame
	print("Main menu settings smoke test passed")
	quit(0)
