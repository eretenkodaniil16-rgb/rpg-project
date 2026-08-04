extends SceneTree

const SYSTEM_SCRIPT: Script = preload("res://scripts/systems/throwable_prop_system.gd")


func _init() -> void:
	var system: ThrowablePropSystem = SYSTEM_SCRIPT.new() as ThrowablePropSystem
	var initial: Array[Dictionary] = [
		{"prop_id": "mug_01", "prop_type_id": "ceramic_mug", "position": Vector2(100.0, 200.0)},
		{"prop_id": "candlestick_01", "prop_type_id": "iron_candlestick", "position": Vector2(300.0, 200.0)}
	]
	var registry: Dictionary = system.normalize_registry({}, initial)
	if int(registry.get("schema_version", 0)) != ThrowablePropSystem.SCHEMA_VERSION:
		_fail("Throwable prop registry schema was not initialized.")
		return
	if system.get_world_records(registry).size() != 2:
		_fail("Initial world props were not restored.")
		return

	var pickup: Dictionary = system.pickup(registry, "mug_01")
	if not bool(pickup.get("success", false)):
		_fail("Ceramic mug could not be picked up.")
		return
	registry = pickup.get("registry", {}) as Dictionary
	if str(registry.get("held_prop_id", "")) != "mug_01":
		_fail("Held prop id was not stored.")
		return
	var second_pickup: Dictionary = system.pickup(registry, "candlestick_01")
	if bool(second_pickup.get("success", false)) or str(second_pickup.get("code", "")) != "hands_occupied":
		_fail("The system allowed two interior props to be held simultaneously.")
		return

	var mug_throw: Dictionary = system.throw_held(registry, Vector2(420.0, 220.0))
	if not bool(mug_throw.get("success", false)) or not bool(mug_throw.get("broken", false)):
		_fail("Breakable mug did not break on impact.")
		return
	registry = mug_throw.get("registry", {}) as Dictionary
	if not str(registry.get("held_prop_id", "")).is_empty():
		_fail("Hands remained occupied after throwing the mug.")
		return
	var mug_record: Dictionary = (registry.get("props", {}) as Dictionary).get("mug_01", {}) as Dictionary
	if str(mug_record.get("state", "")) != ThrowablePropSystem.STATE_BROKEN:
		_fail("Broken prop state was not persisted.")
		return

	pickup = system.pickup(registry, "candlestick_01")
	if not bool(pickup.get("success", false)):
		_fail("Candlestick could not be picked up after hands became free.")
		return
	registry = pickup.get("registry", {}) as Dictionary
	var metal_throw: Dictionary = system.throw_held(registry, Vector2(500.0, 260.0))
	if not bool(metal_throw.get("success", false)) or bool(metal_throw.get("broken", true)):
		_fail("Reusable iron prop was incorrectly destroyed.")
		return
	registry = metal_throw.get("registry", {}) as Dictionary
	var metal_record: Dictionary = (registry.get("props", {}) as Dictionary).get("candlestick_01", {}) as Dictionary
	if str(metal_record.get("state", "")) != ThrowablePropSystem.STATE_WORLD:
		_fail("Reusable thrown prop did not return to the world state.")
		return
	if system.vector_from_value(metal_record.get("position", [])) != Vector2(500.0, 260.0):
		_fail("Thrown prop landing position was not persisted.")
		return

	print("Throwable prop registry, one-item carry limit, breakage and reusable landing passed.")
	quit(0)


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
