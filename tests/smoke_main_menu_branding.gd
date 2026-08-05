extends SceneTree

const MAIN_MENU_SCENE: String = "res://scenes/menus/main_menu.tscn"


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed: PackedScene = load(MAIN_MENU_SCENE) as PackedScene
	assert(packed != null, "Main menu scene must load")
	var menu: Control = packed.instantiate() as Control
	assert(menu != null, "Main menu scene must instantiate")
	root.add_child(menu)
	await process_frame
	await process_frame

	var approved_background: MainMenuTiledBackground = menu.get_node_or_null("ApprovedBackground") as MainMenuTiledBackground
	assert(approved_background != null, "Approved tiled background node is missing")
	assert(approved_background.expected_tile_count() == 19, "Unexpected main-menu strip count")
	assert(approved_background.source_size() == Vector2(1920.0, 1080.0), "Unexpected HQ background size")
	assert(approved_background.has_complete_tiles(), "Approved background strip set is incomplete")
	assert(approved_background.visible, "Approved background must be active when all strips exist")
	assert(menu.get_node_or_null("FallbackBackground") != null, "Fallback background is missing")
	assert(menu.get_node_or_null("Atmosphere") is MainMenuAtmosphere, "Atmosphere controller is missing")
	var title_glow: MainMenuTitleGlow = menu.get_node_or_null("TitleGlow") as MainMenuTitleGlow
	assert(title_glow != null, "Title glow controller is missing")
	assert(title_glow.has_glow_material(), "Title glow shader material is missing")
	assert(title_glow.wait_interval_range() == Vector2(5.0, 10.0), "Unexpected title glow interval")

	for path: String in [
		"CenterContainer/MenuPanel/MarginContainer/VBoxContainer/ContinueButton",
		"CenterContainer/MenuPanel/MarginContainer/VBoxContainer/NewGameButton",
		"CenterContainer/MenuPanel/MarginContainer/VBoxContainer/SettingsButton",
		"CenterContainer/MenuPanel/MarginContainer/VBoxContainer/QuitButton",
	]:
		assert(menu.get_node_or_null(path) is Button, "Working menu button is missing: %s" % path)

	assert(menu.get_node_or_null("SettingsLayer") is MainMenuSettingsPanel, "Settings layer is missing")
	menu.queue_free()
	await process_frame
	print("Main menu branding smoke test passed")
	quit(0)
