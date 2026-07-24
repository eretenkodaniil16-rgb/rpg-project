class_name WorldTimeSystem
extends RefCounted

const WORLD_MINUTES_FLAG: String = "world_minutes_elapsed"
const DEFAULT_START_MINUTES: int = 8 * 60
const MINUTES_PER_HOUR: int = 60
const MINUTES_PER_DAY: int = 24 * MINUTES_PER_HOUR


func get_minutes(state: Node) -> int:
	if state == null or not state.has_method("get_flag"):
		return DEFAULT_START_MINUTES
	return maxi(int(state.call("get_flag", WORLD_MINUTES_FLAG, DEFAULT_START_MINUTES)), 0)


func advance(state: Node, minutes: int, save_after: bool = true) -> int:
	var safe_minutes: int = maxi(minutes, 0)
	var updated: int = get_minutes(state) + safe_minutes
	if state != null and state.has_method("set_flag"):
		state.call("set_flag", WORLD_MINUTES_FLAG, updated)
		if save_after and state.has_method("save_game"):
			state.call("save_game")
	return updated


func format_time(total_minutes: int) -> String:
	var safe_minutes: int = maxi(total_minutes, 0)
	var day: int = floori(float(safe_minutes) / float(MINUTES_PER_DAY)) + 1
	var minutes_in_day: int = safe_minutes % MINUTES_PER_DAY
	var hour: int = floori(float(minutes_in_day) / float(MINUTES_PER_HOUR))
	var minute: int = minutes_in_day % MINUTES_PER_HOUR
	return "День %d, %02d:%02d" % [day, hour, minute]


func format_current(state: Node) -> String:
	return format_time(get_minutes(state))
