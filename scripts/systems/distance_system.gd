class_name DistanceSystem
extends RefCounted

const PIXELS_PER_5_FEET: float = 64.0
const MELEE_REACH_FEET: int = 5


static func distance_feet(from_position: Vector2, to_position: Vector2) -> int:
	var pixels: float = from_position.distance_to(to_position)
	if pixels <= 0.0:
		return 0
	return ceili(pixels / PIXELS_PER_5_FEET) * 5


static func weapon_range_state(weapon: Dictionary, distance: int) -> String:
	var properties: Array = weapon.get("properties", []) as Array
	var normal_range: int = int(weapon.get("range_normal_ft", 0))
	var long_range: int = int(weapon.get("range_long_ft", normal_range))
	if normal_range <= 0:
		return "melee" if distance <= int(weapon.get("reach_ft", MELEE_REACH_FEET)) else "out_of_range"
	if "thrown" in properties and not "ranged" in properties and distance <= MELEE_REACH_FEET:
		return "melee"
	if distance <= normal_range:
		return "normal"
	if distance <= long_range:
		return "long"
	return "out_of_range"


static func is_ranged_attack(weapon: Dictionary, distance: int) -> bool:
	return weapon_range_state(weapon, distance) in ["normal", "long"]


static func is_ranged_weapon(weapon: Dictionary) -> bool:
	var properties: Array = weapon.get("properties", []) as Array
	return "ranged" in properties or "thrown" in properties


static func format_distance(distance: int) -> String:
	return "%d футов" % maxi(distance, 0)
