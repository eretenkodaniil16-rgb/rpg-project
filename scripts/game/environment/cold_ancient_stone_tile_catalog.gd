class_name ColdAncientStoneTileCatalog
extends RefCounted

const TILE_SIZE: int = 64
const FLOOR_VARIANT_COUNT: int = 8
const TILE_SET_PATH: String = "res://assets/environment/approved/cold_ancient_stone_v01/tilesets/cold_ancient_stone_v01.tres"

const SOURCE_FLOOR: int = 0
const SOURCE_OVERLAY: int = 1
const SOURCE_WALL_EDGE: int = 2
const SOURCE_WALL_CORNER: int = 3
const SOURCE_DOOR: int = 4
const SOURCE_STRUCTURE: int = 5

const SOURCE_BY_ASSET: Dictionary = {
	"stone_crack_01": SOURCE_OVERLAY,
	"stone_crack_02": SOURCE_OVERLAY,
	"stone_dust_01": SOURCE_OVERLAY,
	"stone_dust_02": SOURCE_OVERLAY,
	"stone_damp_01": SOURCE_OVERLAY,
	"stone_damp_02": SOURCE_OVERLAY,
	"dry_to_damp_north": SOURCE_OVERLAY,
	"dry_to_damp_east": SOURCE_OVERLAY,
	"dry_to_damp_south": SOURCE_OVERLAY,
	"dry_to_damp_west": SOURCE_OVERLAY,
	"arcane_inlay_01": SOURCE_OVERLAY,
	"arcane_inlay_02": SOURCE_OVERLAY,
	"stone_wall_north": SOURCE_WALL_EDGE,
	"stone_wall_east": SOURCE_WALL_EDGE,
	"stone_wall_south": SOURCE_WALL_EDGE,
	"stone_wall_west": SOURCE_WALL_EDGE,
	"stone_wall_corner_ne": SOURCE_WALL_CORNER,
	"stone_wall_corner_se": SOURCE_WALL_CORNER,
	"stone_wall_corner_sw": SOURCE_WALL_CORNER,
	"stone_wall_corner_nw": SOURCE_WALL_CORNER,
	"stone_door_x_closed": SOURCE_DOOR,
	"stone_door_x_open": SOURCE_DOOR,
	"stone_door_y_closed": SOURCE_DOOR,
	"stone_door_y_open": SOURCE_DOOR,
	"stone_stairs_down_01": SOURCE_STRUCTURE
}

const COORDINATES_BY_ASSET: Dictionary = {
	"stone_crack_01": Vector2i(0, 0),
	"stone_crack_02": Vector2i(1, 0),
	"stone_dust_01": Vector2i(2, 0),
	"stone_dust_02": Vector2i(3, 0),
	"stone_damp_01": Vector2i(4, 0),
	"stone_damp_02": Vector2i(5, 0),
	"dry_to_damp_north": Vector2i(6, 0),
	"dry_to_damp_east": Vector2i(7, 0),
	"dry_to_damp_south": Vector2i(8, 0),
	"dry_to_damp_west": Vector2i(9, 0),
	"arcane_inlay_01": Vector2i(10, 0),
	"arcane_inlay_02": Vector2i(11, 0),
	"stone_wall_north": Vector2i(0, 0),
	"stone_wall_east": Vector2i(1, 0),
	"stone_wall_south": Vector2i(2, 0),
	"stone_wall_west": Vector2i(3, 0),
	"stone_wall_corner_ne": Vector2i(0, 0),
	"stone_wall_corner_se": Vector2i(1, 0),
	"stone_wall_corner_sw": Vector2i(2, 0),
	"stone_wall_corner_nw": Vector2i(3, 0),
	"stone_door_x_closed": Vector2i(0, 0),
	"stone_door_x_open": Vector2i(1, 0),
	"stone_door_y_closed": Vector2i(2, 0),
	"stone_door_y_open": Vector2i(3, 0),
	"stone_stairs_down_01": Vector2i(0, 0)
}


static func load_tile_set(path: String = TILE_SET_PATH) -> TileSet:
	if path.is_empty() or not ResourceLoader.exists(path, "TileSet"):
		return null
	var resource: Resource = ResourceLoader.load(path, "TileSet")
	var tile_set := resource as TileSet
	return tile_set if is_contract_valid(tile_set) else null


static func is_contract_valid(tile_set: TileSet) -> bool:
	if tile_set == null or tile_set.tile_size != Vector2i(TILE_SIZE, TILE_SIZE):
		return false
	for source_id: int in [
		SOURCE_FLOOR,
		SOURCE_OVERLAY,
		SOURCE_WALL_EDGE,
		SOURCE_WALL_CORNER,
		SOURCE_DOOR,
		SOURCE_STRUCTURE
	]:
		if not tile_set.has_source(source_id):
			return false
	var floor_source := tile_set.get_source(SOURCE_FLOOR) as TileSetAtlasSource
	if floor_source == null:
		return false
	for index: int in range(FLOOR_VARIANT_COUNT):
		if not floor_source.has_tile(Vector2i(index, 0)):
			return false
	for asset_id: String in SOURCE_BY_ASSET:
		var source_id: int = int(SOURCE_BY_ASSET[asset_id])
		var source := tile_set.get_source(source_id) as TileSetAtlasSource
		var coordinates: Vector2i = COORDINATES_BY_ASSET[asset_id] as Vector2i
		if source == null or not source.has_tile(coordinates):
			return false
		var tile_data: TileData = source.get_tile_data(coordinates, 0)
		if tile_data == null or str(tile_data.get_custom_data("visual_id")) != asset_id:
			return false
	return true


static func create_layer(
	node_name: String,
	tile_set: TileSet,
	local_position: Vector2,
	z_value: int
) -> TileMapLayer:
	var layer := TileMapLayer.new()
	layer.name = node_name
	layer.tile_set = tile_set
	layer.position = local_position
	layer.z_as_relative = false
	layer.z_index = z_value
	layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	layer.rendering_quadrant_size = 16
	layer.collision_enabled = false
	layer.navigation_enabled = false
	return layer


static func set_floor_cell(layer: TileMapLayer, cell: Vector2i, seed: int) -> bool:
	if layer == null:
		return false
	var variant: int = deterministic_floor_variant(cell, seed)
	layer.set_cell(cell, SOURCE_FLOOR, Vector2i(variant, 0), 0)
	return true


static func set_asset_cell(layer: TileMapLayer, cell: Vector2i, asset_id: String) -> bool:
	if layer == null or not SOURCE_BY_ASSET.has(asset_id) or not COORDINATES_BY_ASSET.has(asset_id):
		return false
	layer.set_cell(
		cell,
		int(SOURCE_BY_ASSET[asset_id]),
		COORDINATES_BY_ASSET[asset_id] as Vector2i,
		0
	)
	return true


static func deterministic_floor_variant(cell: Vector2i, seed: int) -> int:
	var mixed: int = seed
	mixed = int((mixed ^ (cell.x * 73856093)) & 0x7fffffff)
	mixed = int((mixed ^ (cell.y * 19349663)) & 0x7fffffff)
	mixed = int((mixed ^ (cell.x * cell.y * 83492791)) & 0x7fffffff)
	return posmod(mixed, FLOOR_VARIANT_COUNT)


static func floor_signature(columns: int, rows: int, seed: int) -> String:
	var values := PackedStringArray()
	for y: int in range(maxi(rows, 0)):
		for x: int in range(maxi(columns, 0)):
			values.append(str(deterministic_floor_variant(Vector2i(x, y), seed)))
	return ",".join(values)
