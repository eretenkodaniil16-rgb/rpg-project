extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const DEMO_SCENE: String = "res://scenes/game/environment/cold_ancient_stone_demo_v01.tscn"
const APPROVED_MANIFEST: String = "res://assets/environment/approved/cold_ancient_stone_v01/cold_ancient_stone_v01.approved.json"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	state.call("discard_autosave")
	state.call("new_game")
	state.set("player_character", _make_hero())

	if not _validate_approved_manifest():
		return
	if not _validate_tileset_contract():
		return
	if not _validate_two_phase_door_replacement():
		return
	if not _validate_fallback_before_runtime():
		return

	var game: Node = _instantiate_scene(GAME_SCENE)
	if game == null:
		_fail("Game scene could not be instantiated.")
		return
	root.add_child(game)
	for _frame: int in range(50):
		await process_frame

	var room := game.get_node_or_null("StealthTestRoom") as GuardPostEnvironmentIntegration
	if room == null or not room.is_environment_visual_ready_for_testing():
		_fail("Guard post did not install the approved environment presentation.")
		return
	var presentation: GuardPostEnvironmentPresentation = room.get_environment_presentation_for_testing()
	if presentation == null or not presentation.is_installed_for_testing():
		_fail("Environment presentation is missing or reports fallback mode.")
		return
	if presentation.get_tile_layer_count_for_testing() != 8:
		_fail("Environment presentation does not expose the expected eight TileMapLayer nodes.")
		return
	if presentation.get_floor_layer_for_testing().get_used_cells().size() != 162:
		_fail("The exact 18×9 full-tile floor core was not built.")
		return
	if presentation.get_transition_layer_for_testing().get_used_cells().size() != 3:
		_fail("Dry-to-damp transitions are incomplete.")
		return
	if presentation.get_decal_layer_for_testing().get_used_cells().size() != 12:
		_fail("Guard-post decal layout is incomplete.")
		return
	var rendered_cell_count: int = presentation.get_rendered_cell_count_for_testing()
	if rendered_cell_count != 245:
		_fail("Environment TileMap layout changed from the reviewed 245-cell composition.")
		return
	if rendered_cell_count > 260:
		_fail("Environment TileMap cell count exceeded the Android v01 budget.")
		return
	for child: Node in presentation.get_children():
		if child is TileMapLayer and (child as TileMapLayer).texture_filter != CanvasItem.TEXTURE_FILTER_NEAREST:
			_fail("Environment TileMapLayer does not enforce Nearest filtering: %s" % child.name)
			return

	var legacy_floor := game.get_node_or_null("Floor") as CanvasItem
	var legacy_carpet := game.get_node_or_null("Carpet") as CanvasItem
	var legacy_walls: GuardPostWallVisibilityOverlay = room.get_wall_visibility_overlay_for_testing()
	if legacy_floor == null or legacy_carpet == null or legacy_floor.visible or legacy_carpet.visible:
		_fail("Legacy Polygon2D floor visuals were not hidden after successful integration.")
		return
	if legacy_walls == null or legacy_walls.visible:
		_fail("Legacy wall overlay remained visible above approved wall modules.")
		return
	for wall_name: String in ["WestPartitionTop", "InnerPartitionTop", "OuterWallLeft"]:
		var wall_body := room.get_node_or_null(wall_name) as StaticBody2D
		if wall_body == null or not _has_collision_shape(wall_body):
			_fail("Presentation replacement damaged mechanical wall geometry: %s" % wall_name)
			return

	var signature_before: String = presentation.get_floor_signature_for_testing()
	if signature_before.is_empty() or signature_before != presentation.get_floor_signature_for_testing():
		_fail("Deterministic floor signature is empty or unstable within one runtime.")
		return
	if "guard_post_cold_ancient_stone_v01" in JSON.stringify(state.call("get_world_snapshot")):
		_fail("Purely visual environment data leaked into the world snapshot.")
		return

	var west_door: StealthDoor = room.get_test_door()
	var inner_door: StealthDoor = room.get_inner_gate()
	if not await _validate_door_sprite(presentation, west_door):
		return
	if not await _validate_door_sprite(presentation, inner_door):
		return

	game.queue_free()
	await process_frame
	await physics_frame
	await process_frame
	var second_game: Node = _instantiate_scene(GAME_SCENE)
	if second_game == null:
		_fail("Second game scene could not be instantiated for deterministic reload validation.")
		return
	root.add_child(second_game)
	for _frame: int in range(45):
		await process_frame
	var second_room := second_game.get_node_or_null("StealthTestRoom") as GuardPostEnvironmentIntegration
	var second_presentation: GuardPostEnvironmentPresentation = (
		second_room.get_environment_presentation_for_testing() if second_room != null else null
	)
	if second_presentation == null or second_presentation.get_floor_signature_for_testing() != signature_before:
		_fail("Floor pattern changed after reconstructing the game scene.")
		return
	second_game.queue_free()
	await process_frame
	await physics_frame
	await process_frame

	var demo: Node = _instantiate_scene(DEMO_SCENE)
	if demo == null:
		_fail("Environment 6×6 demo scene could not be instantiated.")
		return
	root.add_child(demo)
	for _frame: int in range(4):
		await process_frame
	var demo_layers: Array[TileMapLayer] = demo.call("get_tile_layers_for_testing") as Array[TileMapLayer]
	if demo_layers.size() != 7:
		_fail("Environment demo does not contain its seven review TileMapLayer nodes.")
		return
	if demo.get_node_or_null("ReviewOnlyStairs") == null or demo.get_node_or_null("HumanWarriorScaleReference") == null:
		_fail("Environment demo is missing stairs or the approved character scale reference.")
		return
	demo.queue_free()
	await process_frame
	await physics_frame
	await process_frame
	state.call("discard_autosave")
	print("Godot Environment Integration v01: assets, layers, fallback, doors, reload and demo passed.")
	quit(0)


func _validate_approved_manifest() -> bool:
	if not FileAccess.file_exists(APPROVED_MANIFEST):
		_fail("Approved environment manifest is missing.")
		return false
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(APPROVED_MANIFEST))
	if not parsed is Dictionary:
		_fail("Approved environment manifest is invalid JSON.")
		return false
	var manifest: Dictionary = parsed as Dictionary
	var approval: Dictionary = manifest.get("approval", {}) as Dictionary
	if (
		str(manifest.get("visual_id", "")) != "cold_ancient_stone_v01"
		or str(manifest.get("stage", "")) != "approved_runtime_asset"
		or not bool(approval.get("approved", false))
		or not bool(approval.get("runtime_integrated", false))
	):
		_fail("Approved environment manifest does not declare the runtime approval contract.")
		return false
	if (manifest.get("modules", []) as Array).size() != 33 or (manifest.get("atlases", {}) as Dictionary).size() != 6:
		_fail("Approved environment manifest does not contain 33 modules and six atlases.")
		return false
	return true


func _validate_tileset_contract() -> bool:
	var tile_set: TileSet = ColdAncientStoneTileCatalog.load_tile_set()
	if tile_set == null or not ColdAncientStoneTileCatalog.is_contract_valid(tile_set):
		_fail("Approved TileSet could not satisfy the v01 source contract.")
		return false
	var floor_source := tile_set.get_source(ColdAncientStoneTileCatalog.SOURCE_FLOOR) as TileSetAtlasSource
	var first_tile: TileData = floor_source.get_tile_data(Vector2i.ZERO, 0) if floor_source != null else null
	if first_tile == null or str(first_tile.get_custom_data("visual_id")) != "cold_stone_floor_01":
		_fail("TileSet stable visual_id metadata is missing.")
		return false
	return true


func _validate_fallback_before_runtime() -> bool:
	var fixture := Node2D.new()
	fixture.name = "FallbackFixture"
	root.add_child(fixture)
	var legacy_floor := Polygon2D.new()
	legacy_floor.name = "Floor"
	fixture.add_child(legacy_floor)
	var legacy_carpet := Polygon2D.new()
	legacy_carpet.name = "Carpet"
	fixture.add_child(legacy_carpet)
	var room := Node2D.new()
	room.name = "Room"
	fixture.add_child(room)
	var presentation := GuardPostEnvironmentPresentation.new()
	room.add_child(presentation)
	var west_door := StealthDoor.new()
	var inner_door := StealthDoor.new()
	var result: bool = presentation.configure(
		room,
		west_door,
		inner_door,
		null,
		"res://assets/environment/approved/cold_ancient_stone_v01/tilesets/missing.tres"
	)
	west_door.free()
	inner_door.free()
	if result or not legacy_floor.visible or not legacy_carpet.visible:
		fixture.queue_free()
		_fail("Missing TileSet did not retain legacy Polygon2D fallback visuals.")
		return false
	fixture.queue_free()
	return true


func _validate_two_phase_door_replacement() -> bool:
	var door := StealthDoor.new()
	door.door_id = "two_phase_fixture"
	root.add_child(door)
	var fallback_decorator := StealthDoorVisualDecorator.new()
	door.add_child(fallback_decorator)
	fallback_decorator.configure(door)
	var replacement := EnvironmentDoorSprite.new()
	door.add_child(replacement)
	if not replacement.configure(door, "y") or not fallback_decorator.visible:
		door.queue_free()
		_fail("Door replacement hid fallback art before the full environment was ready.")
		return false
	replacement.activate_replacement()
	if fallback_decorator.modulate.a > 0.001:
		door.queue_free()
		_fail("Door replacement did not make fallback art visually inert after activation.")
		return false
	door.queue_free()
	return true


func _validate_door_sprite(
	presentation: GuardPostEnvironmentPresentation,
	door: StealthDoor
) -> bool:
	if door == null:
		_fail("Environment door fixture is missing.")
		return false
	var sprite: EnvironmentDoorSprite = presentation.get_door_sprite_for_testing(door.door_id)
	if sprite == null or sprite.get_module_count_for_testing() != 2:
		_fail("Door does not use two approved cell-edge modules: %s" % door.door_id)
		return false
	door.set_door_state("closed", false)
	await process_frame
	var closed_texture: Texture2D = sprite.get_current_texture_for_testing()
	door.set_door_state("open", false)
	await process_frame
	var open_texture: Texture2D = sprite.get_current_texture_for_testing()
	for child: Node in door.get_children():
		if child is StealthDoorVisualDecorator and (child as StealthDoorVisualDecorator).modulate.a > 0.001:
			_fail("Legacy door decorator became visible after the approved door changed state: %s" % door.door_id)
			return false
	if (
		closed_texture == null
		or open_texture == null
		or closed_texture == open_texture
		or sprite.get_current_state_for_testing() != "open"
	):
		_fail("Door artwork did not switch from closed to open: %s" % door.door_id)
		return false
	return true


func _instantiate_scene(path: String) -> Node:
	var packed := ResourceLoader.load(path, "PackedScene") as PackedScene
	return packed.instantiate() if packed != null else null


func _has_collision_shape(body: StaticBody2D) -> bool:
	for child: Node in body.get_children():
		if child is CollisionShape2D and (child as CollisionShape2D).shape != null:
			return true
	return false


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель окружения"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 5
	hero.maximum_health = 42
	hero.current_health = 42
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
