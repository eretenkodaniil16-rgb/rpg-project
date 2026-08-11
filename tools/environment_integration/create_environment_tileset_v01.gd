extends SceneTree

const OUTPUT_PATH: String = "res://assets/environment/approved/cold_ancient_stone_v01/tilesets/cold_ancient_stone_v01.tres"
const ATLAS_ROOT: String = "res://assets/environment/approved/cold_ancient_stone_v01/atlases"

const SOURCES: Array[Dictionary] = [
	{
		"source_id": 0,
		"texture": "cold_stone_floor_atlas_v01.png",
		"region_size": Vector2i(64, 64),
		"asset_ids": [
			"cold_stone_floor_01", "cold_stone_floor_02", "cold_stone_floor_03",
			"cold_stone_floor_04", "cold_stone_floor_05", "cold_stone_floor_06",
			"cold_stone_floor_07", "cold_stone_floor_08"
		]
	},
	{
		"source_id": 1,
		"texture": "cold_stone_overlay_atlas_v01.png",
		"region_size": Vector2i(64, 64),
		"asset_ids": [
			"stone_crack_01", "stone_crack_02", "stone_dust_01", "stone_dust_02",
			"stone_damp_01", "stone_damp_02", "dry_to_damp_north",
			"dry_to_damp_east", "dry_to_damp_south", "dry_to_damp_west",
			"arcane_inlay_01", "arcane_inlay_02"
		]
	},
	{
		"source_id": 2,
		"texture": "cold_stone_wall_edge_atlas_v01.png",
		"region_size": Vector2i(64, 96),
		"asset_ids": [
			"stone_wall_north", "stone_wall_east", "stone_wall_south", "stone_wall_west"
		]
	},
	{
		"source_id": 3,
		"texture": "cold_stone_wall_corner_atlas_v01.png",
		"region_size": Vector2i(96, 96),
		"asset_ids": [
			"stone_wall_corner_ne", "stone_wall_corner_se",
			"stone_wall_corner_sw", "stone_wall_corner_nw"
		]
	},
	{
		"source_id": 4,
		"texture": "cold_stone_door_atlas_v01.png",
		"region_size": Vector2i(64, 96),
		"asset_ids": [
			"stone_door_x_closed", "stone_door_x_open",
			"stone_door_y_closed", "stone_door_y_open"
		]
	},
	{
		"source_id": 5,
		"texture": "cold_stone_structure_atlas_v01.png",
		"region_size": Vector2i(64, 96),
		"asset_ids": ["stone_stairs_down_01"]
	}
]


func _init() -> void:
	var tile_set := TileSet.new()
	tile_set.tile_size = Vector2i(64, 64)
	tile_set.add_custom_data_layer(0)
	tile_set.set_custom_data_layer_name(0, "visual_id")
	tile_set.set_custom_data_layer_type(0, TYPE_STRING)

	for source_definition: Dictionary in SOURCES:
		var source_id: int = int(source_definition["source_id"])
		var texture_path: String = "%s/%s" % [ATLAS_ROOT, str(source_definition["texture"])]
		var texture := load(texture_path) as Texture2D
		if texture == null:
			push_error("Cannot load environment atlas: %s" % texture_path)
			quit(2)
			return
		var atlas_source := TileSetAtlasSource.new()
		atlas_source.texture = texture
		atlas_source.texture_region_size = source_definition["region_size"] as Vector2i
		tile_set.add_source(atlas_source, source_id)
		var asset_ids: Array = source_definition["asset_ids"] as Array
		for index: int in range(asset_ids.size()):
			var atlas_coordinates := Vector2i(index, 0)
			atlas_source.create_tile(atlas_coordinates)
			var tile_data: TileData = atlas_source.get_tile_data(atlas_coordinates, 0)
			if tile_data != null:
				tile_data.set_custom_data("visual_id", str(asset_ids[index]))

	var output_absolute: String = ProjectSettings.globalize_path(OUTPUT_PATH)
	var output_directory: String = output_absolute.get_base_dir()
	var make_error: Error = DirAccess.make_dir_recursive_absolute(output_directory)
	if make_error != OK:
		push_error("Cannot create TileSet directory: %s" % error_string(make_error))
		quit(3)
		return
	var save_error: Error = ResourceSaver.save(tile_set, OUTPUT_PATH)
	if save_error != OK:
		push_error("Cannot save environment TileSet: %s" % error_string(save_error))
		quit(4)
		return
	print("Created environment TileSet: %s" % OUTPUT_PATH)
	quit(0)
