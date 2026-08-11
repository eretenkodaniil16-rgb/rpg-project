class_name HumanWarriorAnimationLibrary
extends RefCounted

const MANIFEST_PATH: String = "res://data/visuals/human_warrior_m01_animation_assets_v01.json"
const EXPECTED_CHARACTER_ID: String = "human_warrior_m01"
const EXPECTED_REVISION: String = "animation_assets_v01"
const EXPECTED_CELL_SIZE: int = 96
const EXPECTED_DIRECTIONS: Array[String] = ["down", "left", "right", "up"]
const EXPECTED_CORE_SET_IDS: Array[String] = [
	"idle",
	"walk",
	"combat_idle_onehand",
	"combat_idle_twohand",
	"walk_onehand",
	"walk_twohand",
	"attack_sword_01_onehand",
	"attack_sword_01_twohand",
	"hit_01_onehand",
	"hit_01_twohand"
]
const DEFAULT_DEATH_FALLBACK_VARIANT_ID: String = "death_01_base"
const DEFAULT_DEATH_DURATION_SECONDS: float = 0.8

var _last_error: String = ""
var _attack_contact_frame_indices: Dictionary = {}
var _attack_set_by_weapon_id: Dictionary = {}
var _death_variant_entries: Array[Dictionary] = []
var _death_set_by_variant_id: Dictionary = {}
var _death_anchor_offsets_by_variant_id: Dictionary = {}
var _death_hold_frames_by_variant_id: Dictionary = {}
var _death_fallback_variant_id: String = DEFAULT_DEATH_FALLBACK_VARIANT_ID
var _death_duration_seconds: float = DEFAULT_DEATH_DURATION_SECONDS


func build_sprite_frames() -> SpriteFrames:
	_last_error = ""
	_attack_contact_frame_indices.clear()
	_attack_set_by_weapon_id.clear()
	_death_variant_entries.clear()
	_death_set_by_variant_id.clear()
	_death_anchor_offsets_by_variant_id.clear()
	_death_hold_frames_by_variant_id.clear()
	_death_fallback_variant_id = DEFAULT_DEATH_FALLBACK_VARIANT_ID
	_death_duration_seconds = DEFAULT_DEATH_DURATION_SECONDS
	if not FileAccess.file_exists(MANIFEST_PATH):
		return _fail("manifest is missing: %s" % MANIFEST_PATH)

	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST_PATH))
	if not parsed is Dictionary:
		return _fail("manifest is not a JSON object")
	var manifest: Dictionary = parsed as Dictionary
	if str(manifest.get("character_id", "")) != EXPECTED_CHARACTER_ID:
		return _fail("unexpected character_id")
	if str(manifest.get("revision", "")) != EXPECTED_REVISION:
		return _fail("unexpected manifest revision")
	if int(manifest.get("cell_size", 0)) != EXPECTED_CELL_SIZE:
		return _fail("unexpected cell size")
	if _string_array(manifest.get("direction_order", [])) != EXPECTED_DIRECTIONS:
		return _fail("unexpected direction order")

	var sets_value: Variant = manifest.get("sets", {})
	if not sets_value is Dictionary:
		return _fail("manifest sets are missing")
	var sets: Dictionary = sets_value as Dictionary
	for set_id: String in EXPECTED_CORE_SET_IDS:
		if not sets.has(set_id) or not sets[set_id] is Dictionary:
			return _fail("animation set is missing: %s" % set_id)

	var frames := SpriteFrames.new()
	if frames.has_animation(&"default"):
		frames.remove_animation(&"default")
	for set_id: String in EXPECTED_CORE_SET_IDS:
		if not _append_set(frames, set_id, sets[set_id] as Dictionary):
			return null
	_append_optional_death_sets(frames, manifest, sets)
	return frames


func get_last_error() -> String:
	return _last_error


func get_attack_contact_frame_index(set_id: StringName) -> int:
	return int(_attack_contact_frame_indices.get(str(set_id), 3))


func get_attack_set_for_weapon_id(weapon_id: String) -> StringName:
	return StringName(str(_attack_set_by_weapon_id.get(weapon_id, "")))


func get_death_variant_entries() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for entry: Dictionary in _death_variant_entries:
		result.append(entry.duplicate(true))
	return result


func get_death_set_for_variant(death_variant_id: String) -> StringName:
	return StringName(str(_death_set_by_variant_id.get(death_variant_id, "")))


func get_death_fallback_variant_id() -> String:
	return _death_fallback_variant_id


func get_death_duration_seconds() -> float:
	return _death_duration_seconds


func get_death_corpse_hold_frame_index(death_variant_id: String) -> int:
	return maxi(int(_death_hold_frames_by_variant_id.get(death_variant_id, 8)) - 1, 0)


func get_death_anchor_offset(death_variant_id: String, direction_id: StringName) -> Vector2:
	var offsets_value: Variant = _death_anchor_offsets_by_variant_id.get(death_variant_id, {})
	if not offsets_value is Dictionary:
		return Vector2.ZERO
	var offsets: Dictionary = offsets_value as Dictionary
	return _vector2_from_array(offsets.get(str(direction_id), []))


func _append_optional_death_sets(
	frames: SpriteFrames,
	manifest: Dictionary,
	sets: Dictionary
) -> void:
	var runtime_value: Variant = manifest.get("death_runtime", {})
	if not runtime_value is Dictionary:
		return
	var runtime: Dictionary = runtime_value as Dictionary
	_death_fallback_variant_id = str(
		runtime.get("fallback_variant_id", DEFAULT_DEATH_FALLBACK_VARIANT_ID)
	)
	_death_duration_seconds = maxf(
		float(runtime.get("duration_seconds", DEFAULT_DEATH_DURATION_SECONDS)),
		0.0
	)
	var variants_value: Variant = runtime.get("variants", [])
	if not variants_value is Array:
		return
	for entry_value: Variant in variants_value as Array:
		if not entry_value is Dictionary:
			continue
		var entry: Dictionary = entry_value as Dictionary
		var death_variant_id: String = str(entry.get("death_variant_id", ""))
		var set_id: String = str(entry.get("set_id", ""))
		var weight: float = float(entry.get("weight", 0.0))
		if (
			death_variant_id.is_empty()
			or set_id.is_empty()
			or weight <= 0.0
			or _death_set_by_variant_id.has(death_variant_id)
			or not sets.has(set_id)
			or not sets[set_id] is Dictionary
		):
			continue
		var previous_error: String = _last_error
		if not _append_set(frames, set_id, sets[set_id] as Dictionary):
			var optional_error: String = _last_error
			_last_error = previous_error
			push_warning(
				"Optional human_warrior_m01 death set skipped: %s (%s)"
				% [set_id, optional_error]
			)
			continue
		var spec: Dictionary = sets[set_id] as Dictionary
		_death_variant_entries.append({
			"death_variant_id": death_variant_id,
			"set_id": set_id,
			"weight": weight
		})
		_death_set_by_variant_id[death_variant_id] = set_id
		var offsets_value: Variant = spec.get("runtime_anchor_offset_by_direction", {})
		_death_anchor_offsets_by_variant_id[death_variant_id] = (
			(offsets_value as Dictionary).duplicate(true)
			if offsets_value is Dictionary
			else {}
		)
		_death_hold_frames_by_variant_id[death_variant_id] = int(
			spec.get("corpse_hold_frame", int(spec.get("frame_count", 1)))
		)
func _append_set(frames: SpriteFrames, set_id: String, spec: Dictionary) -> bool:
	var sheet_path: String = str(spec.get("sheet_path", ""))
	var prefix: String = str(spec.get("animation_prefix", ""))
	var frame_count: int = int(spec.get("frame_count", 0))
	var fps: float = float(spec.get("fps", 0.0))
	var loops: bool = bool(spec.get("loop", false))
	if sheet_path.is_empty() or prefix.is_empty() or frame_count <= 0 or fps <= 0.0:
		_fail("invalid animation set contract: %s" % set_id)
		return false
	if not ResourceLoader.exists(sheet_path):
		_fail("animation atlas is missing: %s" % sheet_path)
		return false
	var atlas_texture: Texture2D = load(sheet_path) as Texture2D
	if atlas_texture == null:
		_fail("animation atlas failed to load: %s" % sheet_path)
		return false
	var expected_width: int = EXPECTED_CELL_SIZE * frame_count
	var expected_height: int = EXPECTED_CELL_SIZE * EXPECTED_DIRECTIONS.size()
	if atlas_texture.get_width() != expected_width or atlas_texture.get_height() != expected_height:
		_fail(
			"animation atlas size mismatch: %s=%dx%d expected=%dx%d"
			% [
				sheet_path,
				atlas_texture.get_width(),
				atlas_texture.get_height(),
				expected_width,
				expected_height
			]
		)
		return false

	for row: int in range(EXPECTED_DIRECTIONS.size()):
		var direction: String = EXPECTED_DIRECTIONS[row]
		var animation_name := StringName("%s_%s" % [prefix, direction])
		frames.add_animation(animation_name)
		frames.set_animation_loop(animation_name, loops)
		frames.set_animation_speed(animation_name, fps)
		for column: int in range(frame_count):
			var frame_texture := AtlasTexture.new()
			frame_texture.atlas = atlas_texture
			frame_texture.region = Rect2(
				float(column * EXPECTED_CELL_SIZE),
				float(row * EXPECTED_CELL_SIZE),
				float(EXPECTED_CELL_SIZE),
				float(EXPECTED_CELL_SIZE)
			)
			frames.add_frame(animation_name, frame_texture)

	if set_id.begins_with("attack_sword_01_"):
		var contact_frame_number: int = clampi(int(spec.get("contact_frame", 4)), 1, frame_count)
		_attack_contact_frame_indices[set_id] = contact_frame_number - 1
		for weapon_id: String in _string_array(spec.get("weapon_ids", [])):
			if not weapon_id.is_empty():
				_attack_set_by_weapon_id[weapon_id] = set_id
	return true


func _fail(message: String) -> SpriteFrames:
	_last_error = message
	return null


func _string_array(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		for item: Variant in value as Array:
			result.append(str(item))
	return result


func _vector2_from_array(value: Variant) -> Vector2:
	if value is Array and (value as Array).size() >= 2:
		return Vector2(float((value as Array)[0]), float((value as Array)[1]))
	return Vector2.ZERO
