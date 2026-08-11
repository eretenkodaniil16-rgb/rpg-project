class_name GuardPostEnvironmentPresentation
extends Node2D

const CONFIG_PATH: String = "res://data/environment/guard_post_environment_v01.json"
const MODULE_ROOT: String = "res://assets/environment/approved/cold_ancient_stone_v01/modules"
const DOOR_SPRITE_SCRIPT: Script = preload("res://scripts/game/environment/environment_door_sprite.gd")

const FLOOR_Z: int = 0
const WALL_Z: int = 50
const CORNER_Z: int = 51
const FOREGROUND_Z: int = 50

const LEGACY_WALL_BODY_NAMES: Array[String] = [
	"WestPartitionTop",
	"WestPartitionBottom",
	"InnerPartitionTop",
	"InnerPartitionBottom",
	"OuterWallTop",
	"OuterWallBottom",
	"OuterWallLeft",
	"OuterWallRight"
]

var _config: Dictionary = {}
var _tile_set: TileSet
var _floor_layer: TileMapLayer
var _transition_layer: TileMapLayer
var _decal_layer: TileMapLayer
var _north_wall_layer: TileMapLayer
var _south_foreground_layer: TileMapLayer
var _left_wall_layer: TileMapLayer
var _right_wall_layer: TileMapLayer
var _partition_wall_layer: TileMapLayer
var _edge_fill_root: Node2D
var _corner_root: Node2D
var _door_sprites: Dictionary = {}
var _installed: bool = false
var _floor_seed: int = 0
var _full_columns: int = 0
var _full_rows: int = 0


func configure(
	room: Node2D,
	west_door: StealthDoor,
	inner_door: StealthDoor,
	legacy_wall_overlay: CanvasItem,
	tile_set_path_override: String = ""
) -> bool:
	if room == null or west_door == null or inner_door == null:
		return false
	_config = _load_config()
	if _config.is_empty() or not _validate_config(_config):
		return false
	var configured_path: String = str(_config.get("tile_set_path", ""))
	var tile_set_path: String = tile_set_path_override if not tile_set_path_override.is_empty() else configured_path
	_tile_set = ColdAncientStoneTileCatalog.load_tile_set(tile_set_path)
	if _tile_set == null or not _runtime_textures_exist():
		return false

	_floor_seed = int(_config.get("floor_seed", 0))
	_build_floor_layers()
	_build_floor_edge_fill()
	_build_overlay_layers()
	_build_wall_layers()
	_build_wall_edge_fill_and_corners()
	if not _install_door_sprite(west_door, str((_config["doors"] as Dictionary).get(west_door.door_id, ""))):
		_discard_door_sprites()
		return false
	if not _install_door_sprite(inner_door, str((_config["doors"] as Dictionary).get(inner_door.door_id, ""))):
		_discard_door_sprites()
		return false

	for value: Variant in _door_sprites.values():
		var door_sprite := value as EnvironmentDoorSprite
		if door_sprite != null:
			door_sprite.activate_replacement()
	_hide_legacy_visuals(room, legacy_wall_overlay)
	_installed = true
	return true


func is_installed_for_testing() -> bool:
	return _installed


func get_floor_layer_for_testing() -> TileMapLayer:
	return _floor_layer


func get_transition_layer_for_testing() -> TileMapLayer:
	return _transition_layer


func get_decal_layer_for_testing() -> TileMapLayer:
	return _decal_layer


func get_tile_layer_count_for_testing() -> int:
	var result: int = 0
	for child: Node in get_children():
		if child is TileMapLayer:
			result += 1
	return result


func get_rendered_cell_count_for_testing() -> int:
	var result: int = 0
	for child: Node in get_children():
		if child is TileMapLayer:
			result += (child as TileMapLayer).get_used_cells().size()
	return result


func get_floor_signature_for_testing() -> String:
	var bounds: Rect2 = _local_bounds()
	var columns: int = ceili(bounds.size.x / float(ColdAncientStoneTileCatalog.TILE_SIZE))
	var rows: int = ceili(bounds.size.y / float(ColdAncientStoneTileCatalog.TILE_SIZE))
	return ColdAncientStoneTileCatalog.floor_signature(columns, rows, _floor_seed)


func get_door_sprite_for_testing(door_id: String) -> EnvironmentDoorSprite:
	return _door_sprites.get(door_id) as EnvironmentDoorSprite


func _load_config() -> Dictionary:
	if not FileAccess.file_exists(CONFIG_PATH):
		return {}
	var file := FileAccess.open(CONFIG_PATH, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	return parsed as Dictionary if parsed is Dictionary else {}


func _validate_config(config: Dictionary) -> bool:
	if int(config.get("schema_version", 0)) != 1:
		return false
	if str(config.get("visual_id", "")) != "guard_post_cold_ancient_stone_v01":
		return false
	if int(config.get("tile_size", 0)) != ColdAncientStoneTileCatalog.TILE_SIZE:
		return false
	if not config.get("local_bounds", {}) is Dictionary:
		return false
	if not config.get("walls", {}) is Dictionary or not config.get("doors", {}) is Dictionary:
		return false
	return true


func _runtime_textures_exist() -> bool:
	var required_paths: Array[String] = []
	for variant: int in range(1, ColdAncientStoneTileCatalog.FLOOR_VARIANT_COUNT + 1):
		required_paths.append("%s/floors/cold_stone_floor_%02d.png" % [MODULE_ROOT, variant])
	required_paths.append_array([
		"%s/walls/stone_wall_north.png" % MODULE_ROOT,
		"%s/walls/stone_wall_east.png" % MODULE_ROOT,
		"%s/walls/stone_wall_south.png" % MODULE_ROOT,
		"%s/walls/stone_wall_west.png" % MODULE_ROOT,
		"%s/walls/stone_wall_corner_ne.png" % MODULE_ROOT,
		"%s/walls/stone_wall_corner_se.png" % MODULE_ROOT,
		"%s/walls/stone_wall_corner_sw.png" % MODULE_ROOT,
		"%s/walls/stone_wall_corner_nw.png" % MODULE_ROOT,
		"%s/doors/stone_door_x_closed.png" % MODULE_ROOT,
		"%s/doors/stone_door_x_open.png" % MODULE_ROOT,
		"%s/doors/stone_door_y_closed.png" % MODULE_ROOT,
		"%s/doors/stone_door_y_open.png" % MODULE_ROOT
	])
	for path: String in required_paths:
		if not ResourceLoader.exists(path, "Texture2D"):
			return false
	return true


func _local_bounds() -> Rect2:
	var definition: Dictionary = _config.get("local_bounds", {}) as Dictionary
	var position_values: Array = definition.get("position", []) as Array
	var size_values: Array = definition.get("size", []) as Array
	if position_values.size() != 2 or size_values.size() != 2:
		return Rect2()
	return Rect2(
		Vector2(float(position_values[0]), float(position_values[1])),
		Vector2(float(size_values[0]), float(size_values[1]))
	)


func _build_floor_layers() -> void:
	var bounds: Rect2 = _local_bounds()
	_full_columns = floori(bounds.size.x / float(ColdAncientStoneTileCatalog.TILE_SIZE))
	_full_rows = floori(bounds.size.y / float(ColdAncientStoneTileCatalog.TILE_SIZE))
	_floor_layer = ColdAncientStoneTileCatalog.create_layer("FloorLayer", _tile_set, bounds.position, FLOOR_Z)
	add_child(_floor_layer)
	for y: int in range(_full_rows):
		for x: int in range(_full_columns):
			ColdAncientStoneTileCatalog.set_floor_cell(_floor_layer, Vector2i(x, y), _floor_seed)


func _build_floor_edge_fill() -> void:
	var bounds: Rect2 = _local_bounds()
	var tile_size: int = ColdAncientStoneTileCatalog.TILE_SIZE
	var right_width: int = roundi(bounds.size.x) - _full_columns * tile_size
	var bottom_height: int = roundi(bounds.size.y) - _full_rows * tile_size
	_edge_fill_root = Node2D.new()
	_edge_fill_root.name = "FloorEdgeFill"
	_edge_fill_root.z_as_relative = false
	_edge_fill_root.z_index = FLOOR_Z
	add_child(_edge_fill_root)
	if right_width > 0:
		for y: int in range(_full_rows):
			_add_floor_region(
				Vector2i(_full_columns, y),
				Vector2(bounds.position.x + float(_full_columns * tile_size), bounds.position.y + float(y * tile_size)),
				Vector2i(right_width, tile_size)
			)
	if bottom_height > 0:
		for x: int in range(_full_columns):
			_add_floor_region(
				Vector2i(x, _full_rows),
				Vector2(bounds.position.x + float(x * tile_size), bounds.position.y + float(_full_rows * tile_size)),
				Vector2i(tile_size, bottom_height)
			)
	if right_width > 0 and bottom_height > 0:
		_add_floor_region(
			Vector2i(_full_columns, _full_rows),
			bounds.position + Vector2(float(_full_columns * tile_size), float(_full_rows * tile_size)),
			Vector2i(right_width, bottom_height)
		)


func _add_floor_region(cell: Vector2i, local_position: Vector2, region_size: Vector2i) -> void:
	var variant: int = ColdAncientStoneTileCatalog.deterministic_floor_variant(cell, _floor_seed) + 1
	var texture_path: String = "%s/floors/cold_stone_floor_%02d.png" % [MODULE_ROOT, variant]
	var texture := ResourceLoader.load(texture_path, "Texture2D") as Texture2D
	if texture == null:
		return
	var sprite: Sprite2D = _create_region_sprite(
		texture,
		Rect2(Vector2.ZERO, Vector2(region_size)),
		local_position,
		FLOOR_Z,
		false
	)
	_edge_fill_root.add_child(sprite)


func _build_overlay_layers() -> void:
	var bounds: Rect2 = _local_bounds()
	_transition_layer = ColdAncientStoneTileCatalog.create_layer(
		"TransitionLayer", _tile_set, bounds.position, FLOOR_Z
	)
	_decal_layer = ColdAncientStoneTileCatalog.create_layer("DecalLayer", _tile_set, bounds.position, FLOOR_Z)
	add_child(_transition_layer)
	add_child(_decal_layer)
	_populate_asset_entries(_transition_layer, _config.get("transitions", []) as Array)
	_populate_asset_entries(_decal_layer, _config.get("decals", []) as Array)


func _populate_asset_entries(layer: TileMapLayer, entries: Array) -> void:
	for value: Variant in entries:
		if not value is Dictionary:
			continue
		var entry: Dictionary = value as Dictionary
		var cell_values: Array = entry.get("cell", []) as Array
		if cell_values.size() != 2:
			continue
		var cell := Vector2i(int(cell_values[0]), int(cell_values[1]))
		ColdAncientStoneTileCatalog.set_asset_cell(layer, cell, str(entry.get("asset_id", "")))


func _build_wall_layers() -> void:
	var walls: Dictionary = _config.get("walls", {}) as Dictionary
	var room_left: float = float(walls.get("room_left", 0.0))
	var room_right: float = float(walls.get("room_right", 0.0))
	var room_top: float = float(walls.get("room_top", 0.0))
	var room_bottom: float = float(walls.get("room_bottom", 0.0))
	var partition_values: Array = walls.get("partition_x", []) as Array
	var tile_size: float = float(ColdAncientStoneTileCatalog.TILE_SIZE)

	_north_wall_layer = ColdAncientStoneTileCatalog.create_layer(
		"NorthWallLayer", _tile_set, Vector2(room_left, room_top - tile_size * 0.5), WALL_Z
	)
	_south_foreground_layer = ColdAncientStoneTileCatalog.create_layer(
		"SouthForegroundLayer", _tile_set, Vector2(room_left, room_bottom - tile_size * 0.5), FOREGROUND_Z
	)
	_left_wall_layer = ColdAncientStoneTileCatalog.create_layer(
		"LeftWallLayer", _tile_set, Vector2(room_left - tile_size * 0.5, room_top), WALL_Z
	)
	_right_wall_layer = ColdAncientStoneTileCatalog.create_layer(
		"RightWallLayer", _tile_set, Vector2(room_right - tile_size * 0.5, room_top), WALL_Z
	)
	var first_partition_x: float = float(partition_values[0]) if not partition_values.is_empty() else 0.0
	_partition_wall_layer = ColdAncientStoneTileCatalog.create_layer(
		"PartitionWallLayer", _tile_set, Vector2(first_partition_x - tile_size * 0.5, room_top), WALL_Z
	)
	for layer: TileMapLayer in [
		_north_wall_layer,
		_south_foreground_layer,
		_left_wall_layer,
		_right_wall_layer,
		_partition_wall_layer
	]:
		add_child(layer)

	for x: int in range(_full_columns):
		ColdAncientStoneTileCatalog.set_asset_cell(_north_wall_layer, Vector2i(x, 0), "stone_wall_north")
		ColdAncientStoneTileCatalog.set_asset_cell(
			_south_foreground_layer, Vector2i(x, 0), "stone_wall_south"
		)
	for y: int in range(_full_rows):
		ColdAncientStoneTileCatalog.set_asset_cell(_left_wall_layer, Vector2i(0, y), "stone_wall_west")
		ColdAncientStoneTileCatalog.set_asset_cell(_right_wall_layer, Vector2i(0, y), "stone_wall_east")

	var door_gap_top: float = float(walls.get("door_gap_top", room_top))
	var door_gap_bottom: float = float(walls.get("door_gap_bottom", room_bottom))
	var top_count: int = roundi((door_gap_top - room_top) / tile_size)
	var bottom_start: int = roundi((door_gap_bottom - room_top) / tile_size)
	var partition_step: int = 0
	if partition_values.size() >= 2:
		partition_step = roundi((float(partition_values[1]) - first_partition_x) / tile_size)
	for partition_index: int in range(partition_values.size()):
		var layer_x: int = 0 if partition_index == 0 else partition_step
		var wall_asset: String = "stone_wall_east" if partition_index == 0 else "stone_wall_west"
		for y: int in range(top_count):
			ColdAncientStoneTileCatalog.set_asset_cell(
				_partition_wall_layer, Vector2i(layer_x, y), wall_asset
			)
		for y: int in range(bottom_start, _full_rows):
			ColdAncientStoneTileCatalog.set_asset_cell(
				_partition_wall_layer, Vector2i(layer_x, y), wall_asset
			)


func _build_wall_edge_fill_and_corners() -> void:
	var walls: Dictionary = _config.get("walls", {}) as Dictionary
	var room_left: float = float(walls.get("room_left", 0.0))
	var room_right: float = float(walls.get("room_right", 0.0))
	var room_top: float = float(walls.get("room_top", 0.0))
	var room_bottom: float = float(walls.get("room_bottom", 0.0))
	var tile_size: int = ColdAncientStoneTileCatalog.TILE_SIZE
	var horizontal_remainder: int = roundi(room_right - room_left) - _full_columns * tile_size
	var vertical_remainder: int = roundi(room_bottom - room_top) - _full_rows * tile_size

	_corner_root = Node2D.new()
	_corner_root.name = "WallCornersAndRemainders"
	_corner_root.z_as_relative = false
	_corner_root.z_index = CORNER_Z
	add_child(_corner_root)
	if horizontal_remainder > 0:
		_add_wall_region(
			"stone_wall_north",
			Rect2(0.0, 0.0, float(horizontal_remainder), 96.0),
			Vector2(room_left + float(_full_columns * tile_size), room_top - 48.0),
			WALL_Z
		)
		_add_wall_region(
			"stone_wall_south",
			Rect2(0.0, 0.0, float(horizontal_remainder), 96.0),
			Vector2(room_left + float(_full_columns * tile_size), room_bottom - 48.0),
			FOREGROUND_Z
		)
	if vertical_remainder > 0:
		var remainder_y: float = room_top + float(_full_rows * tile_size)
		_add_vertical_wall_remainder("stone_wall_west", room_left, remainder_y, vertical_remainder)
		_add_vertical_wall_remainder("stone_wall_east", room_right, remainder_y, vertical_remainder)
		for x_value: Variant in walls.get("partition_x", []) as Array:
			_add_vertical_wall_remainder("stone_wall_east", float(x_value), remainder_y, vertical_remainder)

	_add_corner("stone_wall_corner_nw", Vector2(room_left, room_top))
	_add_corner("stone_wall_corner_ne", Vector2(room_right, room_top))
	_add_corner("stone_wall_corner_sw", Vector2(room_left, room_bottom))
	_add_corner("stone_wall_corner_se", Vector2(room_right, room_bottom))
	var partition_values: Array = walls.get("partition_x", []) as Array
	for index: int in range(partition_values.size()):
		var partition_x: float = float(partition_values[index])
		_add_corner("stone_wall_corner_ne" if index == 0 else "stone_wall_corner_nw", Vector2(partition_x, room_top))
		_add_corner("stone_wall_corner_se" if index == 0 else "stone_wall_corner_sw", Vector2(partition_x, room_bottom))


func _add_vertical_wall_remainder(asset_id: String, x: float, y: float, height: int) -> void:
	_add_wall_region(
		asset_id,
		Rect2(0.0, 16.0, 64.0, float(height)),
		Vector2(x - 32.0, y),
		WALL_Z
	)


func _add_wall_region(
	asset_id: String,
	region: Rect2,
	local_position: Vector2,
	z_value: int
) -> void:
	var texture_path: String = "%s/walls/%s.png" % [MODULE_ROOT, asset_id]
	var texture := ResourceLoader.load(texture_path, "Texture2D") as Texture2D
	if texture == null:
		return
	var sprite: Sprite2D = _create_region_sprite(texture, region, local_position, z_value, false)
	_corner_root.add_child(sprite)


func _add_corner(asset_id: String, local_position: Vector2) -> void:
	var texture_path: String = "%s/walls/%s.png" % [MODULE_ROOT, asset_id]
	var texture := ResourceLoader.load(texture_path, "Texture2D") as Texture2D
	if texture == null:
		return
	var sprite := Sprite2D.new()
	sprite.name = asset_id.to_pascal_case()
	sprite.texture = texture
	sprite.position = local_position
	sprite.centered = true
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.z_as_relative = false
	sprite.z_index = CORNER_Z
	_corner_root.add_child(sprite)


func _create_region_sprite(
	texture: Texture2D,
	region: Rect2,
	local_position: Vector2,
	z_value: int,
	centered: bool
) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.region_enabled = true
	sprite.region_rect = region
	sprite.region_filter_clip_enabled = true
	sprite.centered = centered
	sprite.position = local_position
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.z_as_relative = false
	sprite.z_index = z_value
	return sprite


func _install_door_sprite(door: StealthDoor, orientation: String) -> bool:
	if door == null or orientation not in ["x", "y"]:
		return false
	var sprite := DOOR_SPRITE_SCRIPT.new() as EnvironmentDoorSprite
	if sprite == null:
		return false
	sprite.name = "EnvironmentDoorSprite"
	door.add_child(sprite)
	if not sprite.configure(door, orientation):
		sprite.queue_free()
		return false
	_door_sprites[door.door_id] = sprite
	return true


func _discard_door_sprites() -> void:
	for value: Variant in _door_sprites.values():
		var sprite := value as EnvironmentDoorSprite
		if sprite != null and is_instance_valid(sprite):
			sprite.queue_free()
	_door_sprites.clear()


func _hide_legacy_visuals(room: Node2D, legacy_wall_overlay: CanvasItem) -> void:
	var game_root: Node = room.get_parent()
	if game_root != null:
		for node_name: String in ["Floor", "Carpet"]:
			var legacy_floor := game_root.get_node_or_null(node_name) as CanvasItem
			if legacy_floor != null:
				legacy_floor.hide()
	for body_name: String in LEGACY_WALL_BODY_NAMES:
		var body: Node = room.get_node_or_null(body_name)
		if body == null:
			continue
		for child: Node in body.get_children():
			if child is Polygon2D:
				(child as Polygon2D).hide()
	if legacy_wall_overlay != null:
		legacy_wall_overlay.hide()
