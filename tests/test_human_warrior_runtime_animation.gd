extends Node

const EXPECTED_DIRECTIONS: Array[String] = ["down", "left", "right", "up"]


func _ready() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	get_tree().quit(1)


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
	hero.maximum_health = 12
	hero.current_health = 12
	game_state.set("player_character", hero)
	ClassDataSystem.new().ensure_starting_loadout(hero)

	var scene: PackedScene = load("res://scenes/game/game.tscn") as PackedScene
	if scene == null:
		_fail("Game scene failed to load.")
		return
	var game: Node = scene.instantiate()
	add_child(game)
	await get_tree().process_frame
	await get_tree().process_frame

	var player: CharacterBody2D = game.find_child("Player", true, false) as CharacterBody2D
	if player == null:
		_fail("Player node is missing from the game scene.")
		return
	var body: Polygon2D = player.get_node_or_null("Body") as Polygon2D
	var sprite: AnimatedSprite2D = game.find_child("CharacterSprite", true, false) as AnimatedSprite2D
	if body == null or sprite == null:
		_fail("Authored human warrior runtime visual is missing.")
		return
	if sprite.get_parent() != body or not body.visible or body.color.a > 0.001:
		_fail("Authored sprite is not attached to the transparent shared visual root.")
		return
	if sprite.texture_filter != CanvasItem.TEXTURE_FILTER_NEAREST:
		_fail("Authored sprite must use nearest-neighbor filtering.")
		return
	if sprite.position != Vector2(0.0, -43.0):
		_fail("Authored sprite baseline offset drifted.")
		return

	var frames: SpriteFrames = sprite.sprite_frames
	if frames == null or frames.get_animation_names().size() != 24:
		_fail("Runtime animation library must expose 24 directional animations.")
		return
	var expected_sets: Dictionary = {
		"idle": 1,
		"walk": 6,
		"combat_idle_onehand": 4,
		"combat_idle_twohand": 4,
		"walk_onehand": 6,
		"walk_twohand": 6
	}
	for prefix_value: Variant in expected_sets.keys():
		var prefix: String = str(prefix_value)
		var expected_count: int = int(expected_sets[prefix_value])
		for direction: String in EXPECTED_DIRECTIONS:
			var animation_name := StringName("%s_%s" % [prefix, direction])
			if not frames.has_animation(animation_name):
				_fail("Missing animation: %s" % animation_name)
				return
			if frames.get_frame_count(animation_name) != expected_count:
				_fail("Animation %s has incorrect frame count." % animation_name)
				return
			for frame_index: int in range(expected_count):
				var texture: Texture2D = frames.get_frame_texture(animation_name, frame_index)
				if texture == null or texture.get_width() != 96 or texture.get_height() != 96:
					_fail("Animation %s contains a non-96x96 frame." % animation_name)
					return

	player.call("set_visual_preview_mode", &"unarmed")
	player.call("set_visual_motion", true, Vector2.LEFT)
	if sprite.animation != &"walk_left":
		_fail("Unarmed movement did not select walk_left.")
		return
	player.call("set_visual_motion", false, Vector2.UP)
	if sprite.animation != &"idle_up":
		_fail("Unarmed stop did not select idle_up.")
		return

	player.call("set_visual_preview_mode", &"onehand")
	player.call("set_visual_motion", false, Vector2.DOWN)
	if sprite.animation != &"combat_idle_onehand_down":
		_fail("One-handed preview did not select the combat idle.")
		return
	player.call("set_visual_motion", true, Vector2.RIGHT)
	if sprite.animation != &"walk_onehand_right":
		_fail("One-handed movement did not select walk_onehand_right.")
		return

	player.call("set_visual_preview_mode", &"twohand")
	player.call("set_visual_motion", false, Vector2.LEFT)
	if sprite.animation != &"combat_idle_twohand_left":
		_fail("Two-handed preview did not select the combat idle.")
		return
	player.call("set_visual_motion", true, Vector2.UP)
	if sprite.animation != &"walk_twohand_up":
		_fail("Two-handed movement did not select walk_twohand_up.")
		return

	player.call("set_visual_preview_mode", &"auto")
	player.call("set_visual_combat_mode", false)
	player.call("set_visual_motion", false, Vector2.DOWN)
	if sprite.animation != &"idle_down":
		_fail("Automatic exploration mode did not return to unarmed idle.")
		return

	game_state.set("input_locked", false)
	player.call("clear_mobile_input")
	player.call("set_visual_preview_mode", &"unarmed")
	player.call("set_mobile_direction", &"right", true)
	await get_tree().create_timer(0.08).timeout
	for sample_index: int in range(12):
		if sprite.animation != &"walk_right":
			_fail("Continuous right movement flickered away from walk_right at sample %d." % sample_index)
			return
		await get_tree().create_timer(0.025).timeout
	player.call("set_mobile_direction", &"right", false)
	await get_tree().create_timer(0.03).timeout
	if sprite.animation != &"walk_right":
		_fail("A short zero-motion interval caused an immediate walk-to-idle flicker.")
		return
	await get_tree().create_timer(0.12).timeout
	if sprite.animation != &"idle_right":
		_fail("The visual controller did not settle to idle_right after the stop grace period.")
		return

	hero.race_id = "elf"
	player.call("apply_character_appearance")
	if sprite.visible or body.color.a < 0.9:
		_fail("Unsupported character did not fall back to the procedural visual.")
		return

	game.queue_free()
	await get_tree().process_frame
	print("Human warrior runtime animation integration test passed.")
	get_tree().quit(0)
