extends Node


func _ready() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	get_tree().quit(1)


func _await_hit_finished(player: Node) -> void:
	await Signal(player, &"hit_reaction_finished")
	await get_tree().process_frame


func _run() -> void:
	var game_state: Node = get_node_or_null("/root/GameState")
	if game_state == null:
		_fail("GameState autoload is unavailable.")
		return
	game_state.call("new_game")
	var hero := PlayerCharacter.new()
	hero.character_name = "Тестовый воин"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.abilities["constitution"] = 14
	hero.maximum_health = 30
	hero.current_health = 30
	game_state.set("player_character", hero)
	ClassDataSystem.new().ensure_starting_loadout(hero)

	var scene: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if scene == null:
		_fail("Production game scene failed to load.")
		return
	var game: Node = scene.instantiate()
	add_child(game)
	for _frame: int in range(5):
		await get_tree().process_frame

	var player: CharacterBody2D = game.find_child("Player", true, false) as CharacterBody2D
	var sprite: AnimatedSprite2D = player.find_child("CharacterSprite", true, false) as AnimatedSprite2D if player != null else null
	var runtime_character: PlayerCharacter = game_state.get("player_character") as PlayerCharacter
	if player == null or sprite == null or runtime_character == null:
		_fail("Production human warrior runtime nodes are missing.")
		return
	if sprite.sprite_frames.get_animation_names().size() != 52:
		_fail("Expected 52 directional runtime animations after death integration.")
		return
	for grip: String in ["onehand", "twohand"]:
		for direction: String in ["down", "left", "right", "up"]:
			var animation_name := StringName("hit_01_%s_%s" % [grip, direction])
			if not sprite.sprite_frames.has_animation(animation_name):
				_fail("Missing hit animation: %s" % animation_name)
				return
			if sprite.sprite_frames.get_frame_count(animation_name) != 6:
				_fail("Hit animation %s must contain six frames." % animation_name)
				return
			if not is_equal_approx(sprite.sprite_frames.get_animation_speed(animation_name), 15.0):
				_fail("Hit animation %s must play at 15 FPS." % animation_name)
				return
			if sprite.sprite_frames.get_animation_loop(animation_name):
				_fail("Hit animation %s must be non-looping." % animation_name)
				return

	player.call("set_turn_based_mode", true)
	runtime_character.current_health = 30
	runtime_character.equipped_weapon_id = "longsword"
	player.call("_process", 0.0)
	player.call("set_facing_direction", Vector2.LEFT)
	var onehand_finished := Signal(player, &"hit_reaction_finished")
	var onehand_sequence: int = int(player.call(
		"play_hit_reaction",
		3,
		player.global_position + Vector2.RIGHT * 64.0
	))
	if onehand_sequence <= 0 or sprite.animation != &"hit_01_onehand_left":
		_fail("One-handed left hit reaction did not start.")
		return
	if not bool(player.call("is_action_animation_locked")) or not bool(player.call("is_hit_reaction_active")):
		_fail("Hit reaction did not enable its local action lock.")
		return
	player.call("set_facing_direction", Vector2.RIGHT)
	if Vector2(player.call("get_facing_direction")).dot(Vector2.LEFT) < 0.99:
		_fail("Facing changed while hit reaction was active.")
		return
	player.velocity = Vector2(180.0, 0.0)
	player.call("_physics_process", 1.0 / 60.0)
	if player.velocity != Vector2.ZERO:
		_fail("Movement was not blocked during hit reaction.")
		return
	await onehand_finished
	await get_tree().process_frame
	if bool(player.call("is_action_animation_locked")) or bool(player.call("is_hit_reaction_active")):
		_fail("One-handed hit reaction did not release its lock.")
		return
	if sprite.animation != &"combat_idle_onehand_left":
		_fail("One-handed hit reaction did not return to matching combat idle.")
		return

	runtime_character.equipped_weapon_id = "greatsword"
	player.call("_process", 0.0)
	player.call("set_facing_direction", Vector2.UP)
	var twohand_finished := Signal(player, &"hit_reaction_finished")
	var twohand_sequence: int = int(player.call(
		"play_hit_reaction",
		4,
		player.global_position + Vector2.DOWN * 64.0
	))
	if twohand_sequence <= onehand_sequence or sprite.animation != &"hit_01_twohand_up":
		_fail("Two-handed up hit reaction did not start.")
		return
	await twohand_finished
	await get_tree().process_frame
	if sprite.animation != &"combat_idle_twohand_up":
		_fail("Two-handed hit reaction did not return to matching combat idle.")
		return

	runtime_character.equipped_weapon_id = "mace"
	player.call("_process", 0.0)
	player.call("set_facing_direction", Vector2.RIGHT)
	var fallback_finished := Signal(player, &"hit_reaction_finished")
	var fallback_sequence: int = int(player.call(
		"play_hit_reaction",
		2,
		player.global_position + Vector2.LEFT * 64.0
	))
	if fallback_sequence <= twohand_sequence:
		_fail("Fallback hit reaction did not start for unsupported weapon.")
		return
	await fallback_finished
	await get_tree().process_frame
	if bool(player.call("is_action_animation_locked")):
		_fail("Fallback hit reaction left the player locked.")
		return

	var zero_animation: StringName = sprite.animation
	if int(player.call("play_hit_reaction", 0, Vector2.INF)) != -1:
		_fail("Zero damage incorrectly started a hit reaction.")
		return
	if sprite.animation != zero_animation:
		_fail("Zero damage changed the current visual animation.")
		return

	runtime_character.equipped_weapon_id = "longsword"
	runtime_character.current_health = 30
	player.call("_process", 0.0)
	player.call("set_facing_direction", Vector2.DOWN)
	var started_state: Dictionary = {"count": 0, "last_damage": 0}
	player.hit_reaction_started.connect(func(_sequence_id: int, damage_amount: int) -> void:
		started_state["count"] = int(started_state.get("count", 0)) + 1
		started_state["last_damage"] = damage_amount
	)
	var production_finished := Signal(player, &"hit_reaction_finished")
	var applied: Dictionary = game.call("apply_damage_to_player", 4, "slashing", false, null) as Dictionary
	if int(applied.get("applied", 0)) != 4:
		_fail("Production damage path did not apply the expected nonzero damage.")
		return
	if int(started_state.get("count", 0)) != 1 or int(started_state.get("last_damage", 0)) != 4:
		_fail("Production damage path did not start exactly one matching hit reaction.")
		return
	if sprite.animation != &"hit_01_onehand_down":
		_fail("Production damage path selected the wrong authored hit animation.")
		return
	await production_finished
	await get_tree().process_frame

	var started_before_zero: int = int(started_state.get("count", 0))
	var zero_result: Dictionary = game.call("apply_damage_to_player", 0, "slashing", false, null) as Dictionary
	if int(zero_result.get("applied", 0)) != 0 or int(started_state.get("count", 0)) != started_before_zero:
		_fail("Zero applied damage incorrectly emitted a production hit reaction.")
		return

	runtime_character.current_health = 1
	var started_before_lethal: int = int(started_state.get("count", 0))
	var lethal: Dictionary = game.call(
		"apply_damage_to_player",
		runtime_character.maximum_health + 5,
		"slashing",
		false,
		null
	) as Dictionary
	await get_tree().process_frame
	if not bool(lethal.get("dead", false)):
		_fail("Lethal production damage did not receive death priority.")
		return
	if int(started_state.get("count", 0)) != started_before_lethal:
		_fail("Lethal damage incorrectly started hit instead of preserving death priority.")
		return
	if bool(player.call("is_hit_reaction_active")):
		_fail("Hit reaction remained active after lethal damage.")
		return

	game.queue_free()
	await get_tree().process_frame
	print("Human warrior hit runtime v01 test passed.")
	get_tree().quit(0)
