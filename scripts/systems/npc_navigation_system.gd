class_name NpcNavigationSystem
extends RefCounted

const AGENT_NODE_NAME: String = "NpcNavigationAgent"
const DEFAULT_PATH_DISTANCE: float = 8.0
const DEFAULT_TARGET_DISTANCE: float = 10.0


func ensure_agent(actor: Node2D) -> NavigationAgent2D:
	if actor == null:
		return null
	var existing: NavigationAgent2D = actor.get_node_or_null(AGENT_NODE_NAME) as NavigationAgent2D
	if existing != null:
		return existing
	var agent := NavigationAgent2D.new()
	agent.name = AGENT_NODE_NAME
	agent.path_desired_distance = DEFAULT_PATH_DISTANCE
	agent.target_desired_distance = DEFAULT_TARGET_DISTANCE
	agent.avoidance_enabled = false
	agent.navigation_layers = 1
	actor.add_child(agent)
	return agent


func move_actor(actor: Node2D, target_position: Vector2, speed_pixels: float, delta: float) -> Dictionary:
	if actor == null or not is_instance_valid(actor):
		return {"moved": false, "reached": false, "used_navigation": false, "direction": Vector2.ZERO}
	var safe_speed: float = maxf(speed_pixels, 0.0)
	var safe_delta: float = maxf(delta, 0.0)
	var agent: NavigationAgent2D = ensure_agent(actor)
	if agent == null:
		return {"moved": false, "reached": actor.global_position.distance_to(target_position) <= DEFAULT_TARGET_DISTANCE, "used_navigation": false, "direction": Vector2.ZERO}
	if agent.target_position.distance_squared_to(target_position) > 1.0:
		agent.target_position = target_position
	var next_position: Vector2 = target_position
	var used_navigation: bool = false
	if actor.is_inside_tree() and not agent.is_navigation_finished():
		var path_position: Vector2 = agent.get_next_path_position()
		if path_position != Vector2.ZERO and path_position.distance_squared_to(actor.global_position) > 0.01:
			next_position = path_position
			used_navigation = true
	var direction: Vector2 = next_position - actor.global_position
	if direction.length_squared() <= 0.0001:
		direction = target_position - actor.global_position
	var previous_position: Vector2 = actor.global_position
	if direction.length_squared() > 0.0001 and safe_speed > 0.0 and safe_delta > 0.0:
		actor.global_position = actor.global_position.move_toward(next_position, safe_speed * safe_delta)
	var reached: bool = actor.global_position.distance_to(target_position) <= maxf(agent.target_desired_distance, 1.0)
	return {
		"moved": actor.global_position.distance_squared_to(previous_position) > 0.0001,
		"reached": reached,
		"used_navigation": used_navigation,
		"direction": direction.normalized() if direction.length_squared() > 0.0001 else Vector2.ZERO,
		"next_position": next_position
	}


func clear_target(actor: Node2D) -> void:
	if actor == null:
		return
	var agent: NavigationAgent2D = actor.get_node_or_null(AGENT_NODE_NAME) as NavigationAgent2D
	if agent != null:
		agent.target_position = actor.global_position
