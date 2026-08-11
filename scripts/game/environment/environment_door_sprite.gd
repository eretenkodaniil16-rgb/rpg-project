class_name EnvironmentDoorSprite
extends Node2D

const MODULE_ROOT: String = "res://assets/environment/approved/cold_ancient_stone_v01/modules/doors"
const MODULE_STEP: float = 64.0

var _door: StealthDoor
var _orientation: String = "y"
var _closed_texture: Texture2D
var _open_texture: Texture2D
var _modules: Array[Sprite2D] = []
var _last_state: String = ""


func configure(door: StealthDoor, orientation: String) -> bool:
	if door == null or orientation not in ["x", "y"]:
		return false
	var closed_path: String = "%s/stone_door_%s_closed.png" % [MODULE_ROOT, orientation]
	var open_path: String = "%s/stone_door_%s_open.png" % [MODULE_ROOT, orientation]
	if not ResourceLoader.exists(closed_path, "Texture2D") or not ResourceLoader.exists(open_path, "Texture2D"):
		return false
	_closed_texture = ResourceLoader.load(closed_path, "Texture2D") as Texture2D
	_open_texture = ResourceLoader.load(open_path, "Texture2D") as Texture2D
	if _closed_texture == null or _open_texture == null:
		return false
	_door = door
	_orientation = orientation
	_build_modules()
	_sync_state(true)
	return true


func activate_replacement() -> void:
	_hide_fallback_door_art()


func _ready() -> void:
	z_as_relative = false
	z_index = 52
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	process_mode = Node.PROCESS_MODE_ALWAYS


func _process(_delta: float) -> void:
	_sync_state()


func get_current_state_for_testing() -> String:
	return _last_state


func get_module_count_for_testing() -> int:
	return _modules.size()


func get_current_texture_for_testing() -> Texture2D:
	return _modules[0].texture if not _modules.is_empty() else null


func _build_modules() -> void:
	for module: Sprite2D in _modules:
		module.queue_free()
	_modules.clear()
	for side: int in [-1, 1]:
		var module := Sprite2D.new()
		module.name = "DoorModuleNegative" if side < 0 else "DoorModulePositive"
		module.centered = true
		module.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		module.position = (
			Vector2(float(side) * MODULE_STEP * 0.5, 0.0)
			if _orientation == "x"
			else Vector2(0.0, float(side) * MODULE_STEP * 0.5)
		)
		add_child(module)
		_modules.append(module)


func _hide_fallback_door_art() -> void:
	if not is_instance_valid(_door):
		return
	for child: Node in _door.get_children():
		if child is StealthDoorVisualDecorator:
			var decorator := child as StealthDoorVisualDecorator
			# Keep the legacy state probe alive for compatibility tests and debug
			# tooling, but make its complete subtree visually inert.
			decorator.modulate = Color(1.0, 1.0, 1.0, 0.0)
	for node_name: String in ["Visual", "StateLabel"]:
		var legacy_item := _door.get_node_or_null(node_name) as CanvasItem
		if legacy_item != null:
			legacy_item.hide()


func _sync_state(force: bool = false) -> void:
	if not is_instance_valid(_door) or _modules.is_empty():
		return
	var state: String = _door.get_door_state()
	if not force and state == _last_state:
		return
	_last_state = state
	var opened: bool = state in ["open", "broken"]
	for module: Sprite2D in _modules:
		module.texture = _open_texture if opened else _closed_texture
		module.modulate = Color(0.72, 0.72, 0.74, 0.82) if state == "broken" else Color.WHITE
