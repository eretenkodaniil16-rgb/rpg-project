extends SceneTree

const MAIN_MENU_SCENE: String = "res://scenes/menus/main_menu.tscn"
const BACKGROUND_PATH: String = "res://assets/branding/main_menu/approved/main_menu_tower_down_title_v01.webp"


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

	var approved_background: TextureRect = menu.get_node_or_null("ApprovedBackground") as TextureRect
	assert(approved_background != null, "Approved background node is missing")
	assert(approved_background.visible, "Approved background must be active when its resource exists")
	assert(approved_background.texture != null, "Approved background texture must load")
	assert(ResourceLoader.exists(BACKGROUND_PATH, "Texture2D"), "Approved background resource is missing")
	assert(menu.get_node_or_null("FallbackBackground") != null, "Fallback background is missing")
	assert(menu.get_node_or_null("Atmosphere") is MainMenuAtmosphere, "Atmosphere controller is missing")

	for path: String in [
		"CenterContainer/MenuPanel/MarginContainer/VBoxContainer/ContinueButton",
		"CenterContainer/MenuPanel/MarginContainer/VBoxContainer/NewGameButton",
		"CenterContainer/MenuPanel/MarginContainer/VBoxContainer/QuitButton",
	]:
		assert(menu.get_node_or_null(path) is Button, "Working menu button is missing: %s" % path)

	menu.queue_free()
	await process_frame
	print("Main menu branding smoke test passed")
	quit(0)
