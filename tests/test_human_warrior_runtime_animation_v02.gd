extends Node

const EXPECTED_DIRECTIONS: Array[String] = ["down", "left", "right", "up"]
const EXPECTED_SETS: Dictionary = {
	"idle": 1,
	"walk": 6,
	"combat_idle_onehand": 4,
	"combat_idle_twohand": 4,
	"walk_onehand": 6,
	"walk_twohand": 6,
	"attack_sword_01_onehand": 8,
	"attack_sword_01_twohand": 8,
	"hit_01_onehand": 6,
	"hit_01_twohand": 6
}


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
	for _frame: int in range(4):
		await get_tree().process_frame

	var player: CharacterBody2D = game.find_child("Player", true, false) as CharacterBody2D
	if player == null:
		_fail("Player node is missing from the production game scene.")
		return
	var runtime_character: PlayerCharacter = game_state.get("player_character") as PlayerCharacter
	if runtime_character == null:
		_fail("Production scene has no runtime player character.")
		return
	var body: Polygon2D = player.get_node_or_null("Body") as Polygon2D
	var sprite: AnimatedSprite2D = player.find_child("CharacterSprite", true, false) as AnimatedSprite2D
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
	if frames == null or frames.get_animation_names().size() != 40:
		_fail("Runtime animation library must expose 40 directional animations.")
		return
	for prefix_value: Variant in EXPECTED_SETS.keys():
		var prefix: String = str(prefix_value)
		var expected_count: int = int(EXPECTED_SETS[prefix_value])
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
		_fail("One-handed state did not select combat_idle_onehand_down.")
		return
	player.call("set_visual_motion", true, Vector2.RIGHT)
	if sprite.animation != &"walk_onehand_right":
		_fail("One-handed movement did not select walk_onehand_right.")
		return

	player.call("set_visual_preview_mode", &"twohand")
	player.call("set_visual_motion", false, Vector2.LEFT)
	if sprite.animation != &"combat_idle_twohand_left":
		_fail("Two-handed state did not select combat_idle_twohand_left.")
		return
	player.call("set_visual_motion", true, Vector2.UP)
	if sprite.animation != &"walk_twohand_up":
		_fail("Two-handed movement did not select walk_twohand_up.")
		return

	player.call("set_visual_preview_mode", &"auto")
	player.call("set_turn_based_mode", true)
	runtime_character.equipped_weapon_id = "longsword"
	player.call("_process", 0.0)
	player.call("set_facing_direction", Vector2.LEFT)
	var onehand_contact: Dictionary = {"called": false, "frame": -1}
	var onehand_callback := func() -> void:
		onehand_contact["called"] = true
		onehand_contact["frame"] = sprite.frame
	var onehand_contact_signal := Signal(player, &"melee_attack_contact")
	var onehand_finished_signal := Signal(player, &"melee_attack_finished")
	var onehand_weapon: Dictionary = {
		"id": "longsword",
		"properties": ["versatile"]
	}
	var onehand_sequence: int = int(player.call(
		"start_melee_attack_animation",
		player.global_position + Vector2.LEFT * 64.0,
		onehand_weapon,
		onehand_callback
	))
	if onehand_sequence <= 0 or sprite.animation != &"attack_sword_01_onehand_left":
		_fail("One-handed attack did not start in the left direction.")
		return
	if not bool(player.call("is_action_animation_locked")):
		_fail("Movement/action lock was not enabled for the one-handed attack.")
		return
	if int(player.call(
		"start_melee_attack_animation",
		player.global_position + Vector2.LEFT * 64.0,
		onehand_weapon,
		Callable()
	)) != -1:
		_fail("A repeated attack was accepted while the first animation was active.")
		return
	player.call("set_facing_direction", Vector2.RIGHT)
	if Vector2(player.call("get_facing_direction")).dot(Vector2.LEFT) < 0.99:
		_fail("Facing changed while the one-handed attack lock was active.")
		return
	player.velocity = Vector2(120.0, 0.0)
	player.call("_physics_process", 1.0 / 60.0)
	if player.velocity != Vector2.ZERO:
		_fail("Player movement was not blocked during the attack animation.")
		return
	await onehand_contact_signal
	if not bool(onehand_contact.get("called", false)) or int(onehand_contact.get("frame", -1)) != 3:
		_fail("One-handed contact callback was not fired by f04.")
		return
	if not bool(player.call("is_action_animation_locked")):
		_fail("Attack lock was released before the recovery frames finished.")
		return
	await onehand_finished_signal
	await get_tree().process_frame
	if bool(player.call("is_action_animation_locked")):
		_fail("One-handed attack lock was not released after f08.")
		return
	if sprite.animation != &"combat_idle_onehand_left":
		_fail(
			"One-handed post-attack mismatch: animation=%s playing=%s frame=%d weapon=%s debug=%s"
			% [
				str(sprite.animation),
				str(sprite.is_playing()),
				sprite.frame,
				runtime_character.equipped_weapon_id,
				str(player.call("get_visual_debug_state"))
			]
		)
		return

	runtime_character.equipped_weapon_id = "greatsword"
	player.call("_process", 0.0)
	player.call("set_facing_direction", Vector2.UP)
	var twohand_contact: Dictionary = {"called": false, "frame": -1}
	var twohand_callback := func() -> void:
		twohand_contact["called"] = true
		twohand_contact["frame"] = sprite.frame
	var twohand_contact_signal := Signal(player, &"melee_attack_contact")
	var twohand_finished_signal := Signal(player, &"melee_attack_finished")
	var twohand_weapon: Dictionary = {
		"id": "greatsword",
		"properties": ["heavy", "two_handed"]
	}
	var twohand_sequence: int = int(player.call(
		"start_melee_attack_animation",
		player.global_position + Vector2.UP * 64.0,
		twohand_weapon,
		twohand_callback
	))
	if twohand_sequence <= onehand_sequence or sprite.animation != &"attack_sword_01_twohand_up":
		_fail("Two-handed attack did not start in the up direction.")
		return
	await twohand_contact_signal
	if not bool(twohand_contact.get("called", false)) or int(twohand_contact.get("frame", -1)) != 3:
		_fail("Two-handed contact callback was not fired by f04.")
		return
	await twohand_finished_signal
	await get_tree().process_frame
	if bool(player.call("is_action_animation_locked")):
		_fail("Two-handed attack lock was not released after f08.")
		return
	if sprite.animation != &"combat_idle_twohand_up":
		_fail(
			"Two-handed post-attack mismatch: animation=%s playing=%s frame=%d weapon=%s debug=%s"
			% [
				str(sprite.animation),
				str(sprite.is_playing()),
				sprite.frame,
				runtime_character.equipped_weapon_id,
				str(player.call("get_visual_debug_state"))
			]
		)
		return

	runtime_character.equipped_weapon_id = "mace"
	player.call("_process", 0.0)
	var fallback_contact: Dictionary = {"called": false}
	var fallback_callback := func() -> void:
		fallback_contact["called"] = true
	var fallback_contact_signal := Signal(player, &"melee_attack_contact")
	var fallback_finished_signal := Signal(player, &"melee_attack_finished")
	var fallback_sequence: int = int(player.call(
		"start_melee_attack_animation",
		player.global_position + Vector2.RIGHT * 64.0,
		{"id": "mace", "properties": []},
		fallback_callback
	))
	if fallback_sequence <= twohand_sequence:
		_fail("Fallback melee attack did not start.")
		return
	await fallback_contact_signal
	if not bool(fallback_contact.get("called", false)):
		_fail("Fallback melee contact event was not fired.")
		return
	await fallback_finished_signal
	await get_tree().process_frame
	if bool(player.call("is_action_animation_locked")):
		_fail("Fallback melee action left the player locked.")
		return

	runtime_character.race_id = "elf"
	player.call("apply_character_appearance")
	if sprite.visible or body.color.a < 0.9:
		_fail("Unsupported character did not fall back to the procedural visual.")
		return

	game.queue_free()
	await get_tree().process_frame
	print("Human warrior runtime animation v02 test passed.")
	get_tree().quit(0)
