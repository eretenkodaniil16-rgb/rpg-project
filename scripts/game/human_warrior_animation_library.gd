class_name HumanWarriorAnimationLibrary
extends RefCounted

const MANIFEST_PATH: String = "res://data/visuals/human_warrior_m01_runtime_v01.json"
const EXPECTED_CHARACTER_ID: String = "human_warrior_m01"
const EXPECTED_REVISION: String = "runtime_v01"
const EXPECTED_CELL_SIZE: int = 96
const EXPECTED_DIRECTIONS: Array[String] = ["down", "left", "right", "up"]

var _manifest: Dictionary = {}
var _texture_cache: Dictionary = {}
var _last_error: String = ""


func build_sprite_frames() -> SpriteFrames:
	_last_error = ""
	_manifest = _load_manifest()
	if _manifest.is_empty():
		return null
	if not _validate_manifest(_manifest):
		return null

	var frames := SpriteFrames.new()
	if frames.has_animation(&"default"):
		frames.remove_animation(&"default")
	var sets_value: Variant = _manifest.get("sets", {})
	var sets: Dictionary = sets_value as Dictionary
	for set_id_value: Variant in sets.keys():
		var set_id: String = str(set_id_value)
		var set_value: Variant = sets[set_id_value]
		if not set_value is Dictionary:
			return _fail_frames("Animation set %s is not a dictionary." % set_id)
		if not _append_set(frames, set_id, set_value as Dictionary):
			return null
	return frames


func get_manifest() -> Dictionary:
	return _manifest.duplicate(true)


func get_last_error() -> String:
	return _last_error


func _load_manifest() -> Dictionary:
	if not FileAccess.file_exists(MANIFEST_PATH):
		_last_error = "Animation manifest is missing: %s" % MANIFEST_PATH
		return {}
	var file := FileAccess.open(MANIFEST_PATH, FileAccess.READ)
	if file == null:
		_last_error = "Animation manifest cannot be opened: %s" % MANIFEST_PATH
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		_last_error = "Animation manifest is not a JSON object."
		return {}
	return (parsed as Dictionary).duplicate(true)


func _validate_manifest(manifest: Dictionary) -> bool:
	if str(manifest.get("character_id", "")) != EXPECTED_CHARACTER_ID:
		return _fail("Animation manifest character_id drifted.")
	if str(manifest.get("revision", "")) != EXPECTED_REVISION:
		return _fail("Animation manifest revision drifted.")
	if int(manifest.get("cell_size", 0)) != EXPECTED_CELL_SIZE:
		return _fail("Animation manifest cell size must remain 96.")
	var directions: Array[String] = _string_array(manifest.get("direction_order", []))
	if directions != EXPECTED_DIRECTIONS:
		return _fail("Animation manifest direction order drifted.")
	var sets_value: Variant = manifest.get("sets", {})
	if not sets_value is Dictionary or (sets_value as Dictionary).size() != 6:
		return _fail("Animation manifest must contain six runtime sets.")
	return true


func _append_set(frames: SpriteFrames, set_id: String, definition: Dictionary) -> bool:
	var sheet_path: String = str(definition.get("sheet_path", ""))
	var prefix: String = str(definition.get("animation_prefix", ""))
	var frame_count: int = int(definition.get("frame_count", 0))
	var fps: float = float(definition.get("fps", 0.0))
	var loop: bool = bool(definition.get("loop", true))
	if sheet_path.is_empty() or prefix.is_empty() or frame_count <= 0 or fps <= 0.0:
		return _fail("Animation set %s has invalid metadata." % set_id)
	var texture: Texture2D = _load_texture(sheet_path)
	if texture == null:
		return _fail("Animation sheet is missing: %s" % sheet_path)
	var expected_width: int = frame_count * EXPECTED_CELL_SIZE
	var expected_height: int = EXPECTED_DIRECTIONS.size() * EXPECTED_CELL_SIZE
	if texture.get_width() != expected_width or texture.get_height() != expected_height:
		return _fail(
			"Animation sheet %s must be %dx%d, got %dx%d."
			% [sheet_path, expected_width, expected_height, texture.get_width(), texture.get_height()]
		)
	for row: int in range(EXPECTED_DIRECTIONS.size()):
		var direction: String = EXPECTED_DIRECTIONS[row]
		var animation_name := StringName("%s_%s" % [prefix, direction])
		frames.add_animation(animation_name)
		frames.set_animation_loop(animation_name, loop)
		frames.set_animation_speed(animation_name, fps)
		for column: int in range(frame_count):
			var atlas_frame := AtlasTexture.new()
			atlas_frame.atlas = texture
			atlas_frame.region = Rect2(
				Vector2(column * EXPECTED_CELL_SIZE, row * EXPECTED_CELL_SIZE),
				Vector2(EXPECTED_CELL_SIZE, EXPECTED_CELL_SIZE)
			)
			frames.add_frame(animation_name, atlas_frame)
	return true


func _load_texture(path: String) -> Texture2D:
	var cached: Variant = _texture_cache.get(path)
	if cached is Texture2D:
		return cached as Texture2D
	if not ResourceLoader.exists(path):
		return null
	var texture: Texture2D = load(path) as Texture2D
	if texture != null:
		_texture_cache[path] = texture
	return texture


func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value as Array:
			result.append(str(item))
	return result


func _fail(message: String) -> bool:
	_last_error = message
	push_warning(message)
	return false


func _fail_frames(message: String) -> SpriteFrames:
	_fail(message)
	return null
