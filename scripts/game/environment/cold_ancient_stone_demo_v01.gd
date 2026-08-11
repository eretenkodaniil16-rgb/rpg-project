class_name ColdAncientStoneDemoV01
extends Node2D

const ROOM_ORIGIN: Vector2 = Vector2(448.0, 168.0)
const ROOM_CELLS: Vector2i = Vector2i(6, 6)
const FLOOR_SEED: int = 1729
const HUMAN_IDLE_PATH: String = "res://assets/characters/human/warrior_m01/gameplay/approved/atlases/human_warrior_m01_idle_v01.png"
const MODULE_ROOT: String = "res://assets/environment/approved/cold_ancient_stone_v01/modules"

var _tile_set: TileSet
var _layers: Array[TileMapLayer] = []


func _ready() -> void:
	_tile_set = ColdAncientStoneTileCatalog.load_tile_set()
	if _tile_set == null:
		push_warning("Cold ancient stone demo cannot load its TileSet.")
		return
	_build_floor()
	_build_overlays()
	_build_walls()
	_build_stairs()
	_build_character_reference()
	queue_redraw()


func get_tile_layers_for_testing() -> Array[TileMapLayer]:
	return _layers.duplicate()


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(1280.0, 720.0)), Color("091019"), true)
	draw_string(
		ThemeDB.fallback_font,
		Vector2(42.0, 56.0),
		"ХОЛОДНЫЙ ДРЕВНИЙ КАМЕНЬ · GODOT INTEGRATION v01",
		HORIZONTAL_ALIGNMENT_LEFT,
		900.0,
		22,
		Color("98a7ae")
	)
	draw_string(
		ThemeDB.fallback_font,
		Vector2(42.0, 88.0),
		"6×6 · TileMapLayer · 64 px · Nearest · лестница не интерактивна",
		HORIZONTAL_ALIGNMENT_LEFT,
		900.0,
		16,
		Color("6b808d")
	)


func _build_floor() -> void:
	var floor := _add_layer("FloorLayer", ROOM_ORIGIN, 0)
	for y: int in range(ROOM_CELLS.y):
		for x: int in range(ROOM_CELLS.x):
			ColdAncientStoneTileCatalog.set_floor_cell(floor, Vector2i(x, y), FLOOR_SEED)


func _build_overlays() -> void:
	var transitions := _add_layer("TransitionLayer", ROOM_ORIGIN, 0)
	var decals := _add_layer("DecalLayer", ROOM_ORIGIN, 0)
	for entry: Dictionary in [
		{"cell": Vector2i(0, 1), "asset": "stone_damp_01"},
		{"cell": Vector2i(1, 1), "asset": "dry_to_damp_east"},
		{"cell": Vector2i(4, 4), "asset": "dry_to_damp_west"}
	]:
		ColdAncientStoneTileCatalog.set_asset_cell(
			transitions, entry["cell"] as Vector2i, str(entry["asset"])
		)
	for entry: Dictionary in [
		{"cell": Vector2i(2, 1), "asset": "stone_crack_01"},
		{"cell": Vector2i(4, 5), "asset": "stone_crack_02"},
		{"cell": Vector2i(1, 4), "asset": "stone_damp_02"},
		{"cell": Vector2i(4, 3), "asset": "arcane_inlay_01"}
	]:
		ColdAncientStoneTileCatalog.set_asset_cell(
			decals, entry["cell"] as Vector2i, str(entry["asset"])
		)


func _build_walls() -> void:
	var room_size := Vector2(ROOM_CELLS) * float(ColdAncientStoneTileCatalog.TILE_SIZE)
	var half_tile: float = float(ColdAncientStoneTileCatalog.TILE_SIZE) * 0.5
	var north := _add_layer("NorthWallLayer", ROOM_ORIGIN - Vector2(0.0, half_tile), 50)
	var south := _add_layer(
		"SouthForegroundLayer",
		ROOM_ORIGIN + Vector2(0.0, room_size.y - half_tile),
		50
	)
	var west := _add_layer("WestWallLayer", ROOM_ORIGIN - Vector2(half_tile, 0.0), 50)
	var east := _add_layer(
		"EastWallLayer",
		ROOM_ORIGIN + Vector2(room_size.x - half_tile, 0.0),
		50
	)
	for index: int in range(ROOM_CELLS.x):
		ColdAncientStoneTileCatalog.set_asset_cell(north, Vector2i(index, 0), "stone_wall_north")
		ColdAncientStoneTileCatalog.set_asset_cell(south, Vector2i(index, 0), "stone_wall_south")
	for index: int in range(ROOM_CELLS.y):
		ColdAncientStoneTileCatalog.set_asset_cell(west, Vector2i(0, index), "stone_wall_west")
		ColdAncientStoneTileCatalog.set_asset_cell(east, Vector2i(0, index), "stone_wall_east")
	_add_corner("stone_wall_corner_nw", ROOM_ORIGIN)
	_add_corner("stone_wall_corner_ne", ROOM_ORIGIN + Vector2(room_size.x, 0.0))
	_add_corner("stone_wall_corner_sw", ROOM_ORIGIN + Vector2(0.0, room_size.y))
	_add_corner("stone_wall_corner_se", ROOM_ORIGIN + room_size)


func _build_stairs() -> void:
	var path: String = "%s/structures/stone_stairs_down_01.png" % MODULE_ROOT
	var texture := ResourceLoader.load(path, "Texture2D") as Texture2D
	if texture == null:
		return
	var stairs := Sprite2D.new()
	stairs.name = "ReviewOnlyStairs"
	stairs.texture = texture
	stairs.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	stairs.position = ROOM_ORIGIN + Vector2(1.5 * 64.0, 3.0 * 64.0 - 40.0)
	stairs.z_index = 4
	add_child(stairs)


func _build_character_reference() -> void:
	var atlas := ResourceLoader.load(HUMAN_IDLE_PATH, "Texture2D") as Texture2D
	if atlas == null:
		return
	var frame := AtlasTexture.new()
	frame.atlas = atlas
	frame.region = Rect2(0.0, 0.0, 96.0, 96.0)
	var character := Sprite2D.new()
	character.name = "HumanWarriorScaleReference"
	character.texture = frame
	character.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	character.position = ROOM_ORIGIN + Vector2(3.5 * 64.0, 3.5 * 64.0)
	character.z_index = 10
	add_child(character)


func _add_layer(node_name: String, local_position: Vector2, z_value: int) -> TileMapLayer:
	var layer: TileMapLayer = ColdAncientStoneTileCatalog.create_layer(
		node_name, _tile_set, local_position, z_value
	)
	add_child(layer)
	_layers.append(layer)
	return layer


func _add_corner(asset_id: String, local_position: Vector2) -> void:
	var path: String = "%s/walls/%s.png" % [MODULE_ROOT, asset_id]
	var texture := ResourceLoader.load(path, "Texture2D") as Texture2D
	if texture == null:
		return
	var corner := Sprite2D.new()
	corner.name = asset_id.to_pascal_case()
	corner.texture = texture
	corner.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	corner.position = local_position
	corner.z_as_relative = false
	corner.z_index = 51
	add_child(corner)
