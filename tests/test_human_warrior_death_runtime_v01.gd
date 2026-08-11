extends SceneTree

const GAME_SCENE_PATH: String = "res://scenes/game/game.tscn"
const EXPECTED_DEATH_VARIANTS: Array[String] = [
	"death_01_base",
	"death_02_base",
	"death_03_base"
]
const EXPECTED_DIRECTIONS: Array[String] = ["down", "left", "right", "up"]
const AUTHORED_SPRITE_OFFSET: Vector2 = Vector2(0.0, -43.0)


func _init() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	push_error(message)
	quit(1)


func _run() -> void:
	var game_state: Node = root.get_node_or_null("GameState")
	if game_state == null:
		_fail("GameState autoload is unavailable.")
		return
	game_state.call("new_game")
	var character := _build_character("human", 1)
	game_state.set("player_character", character)

	var packed: PackedScene = load(GAME_SCENE_PATH) as PackedScene
	if packed == null:
		_fail("Production game scene failed to load.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(14):
		await process_frame

	if str(game.get_script().resource_path) != "res://scripts/game/game_death_runtime_v1.gd":
		_fail("Production scene is not connected to Death Runtime v1.")
		return
	if not game.has_method("get_coordination_plan_v1_for_testing"):
		_fail("Death Runtime v1 bypassed the current Combat AI Coordination v1 stack.")
		return
	var player: CharacterBody2D = game.get_node_or_null("Player") as CharacterBody2D
	var sprite: AnimatedSprite2D = (
		player.find_child("CharacterSprite", true, false) as AnimatedSprite2D
		if player != null
		else null
	)
	if player == null or sprite == null:
		_fail("Production human-warrior visual is missing.")
		return
	if sprite.sprite_frames.get_animation_names().size() != 52:
		_fail("Death integration must expose 52 directional animations.")
		return
	for death_variant_id: String in EXPECTED_DEATH_VARIANTS:
		for direction_id: String in EXPECTED_DIRECTIONS:
			var animation_name := StringName("%s_%s" % [death_variant_id, direction_id])
			if not sprite.sprite_frames.has_animation(animation_name):
				_fail("Missing death animation: %s" % animation_name)
				return
			if sprite.sprite_frames.get_frame_count(animation_name) != 8:
				_fail("Death animation %s must contain eight frames." % animation_name)
				return
			if not is_equal_approx(sprite.sprite_frames.get_animation_speed(animation_name), 10.0):
				_fail("Death animation %s must play at 10 FPS." % animation_name)
				return
			if sprite.sprite_frames.get_animation_loop(animation_name):
				_fail("Death animation %s must be non-looping." % animation_name)
				return

	var ally: Node = game.find_child("ControllableAllyIrna", true, false)
	if ally != null and ally.has_method("start_confirmed_death_animation"):
		_fail("Hero death runtime was incorrectly attached to Irina.")
		return

	var cycle_library: HumanWarriorAnimationLibrary = player.get(
		"_animation_library"
	) as HumanWarriorAnimationLibrary
	for cycle_variant_id: String in EXPECTED_DEATH_VARIANTS:
		for cycle_direction_id: String in EXPECTED_DIRECTIONS:
			character.current_health = 0
			player.call("clear_death_visual_state")
			var cycle_sequence_id: int = int(player.call(
				"start_confirmed_death_animation",
				{
					"death_variant_id": cycle_variant_id,
					"direction_id": cycle_direction_id,
					"corpse_state": "playing",
					"frame_index": 0
				}
			))
			if cycle_sequence_id <= 0 or not bool(player.call("is_death_animation_active")):
				_fail("Death cycle did not start: %s/%s" % [cycle_variant_id, cycle_direction_id])
				return
			if sprite.animation != StringName("%s_%s" % [cycle_variant_id, cycle_direction_id]):
				_fail("Death cycle selected the wrong animation: %s/%s" % [cycle_variant_id, cycle_direction_id])
				return
			var expected_cycle_position: Vector2 = (
				AUTHORED_SPRITE_OFFSET
				+ cycle_library.get_death_anchor_offset(
					cycle_variant_id,
					StringName(cycle_direction_id)
				)
			)
			if sprite.position.distance_to(expected_cycle_position) > 0.001:
				_fail("Death cycle anchor is incorrect: %s/%s" % [cycle_variant_id, cycle_direction_id])
				return
	player.call("clear_death_visual_state")
	character.current_health = 1
	character.last_death_variant_id = ""
	character.death_visual_state.clear()

	player.call("set_facing_direction", Vector2.LEFT)
	var zero_hp_result: Dictionary = game.call(
		"apply_damage_to_player",
		1,
		"slashing",
		false,
		null
	) as Dictionary
	await process_frame
	var combat_state: CombatantState = game.call("get_player_combat_state") as CombatantState
	if character.current_health != 0 or bool(zero_hp_result.get("dead", false)):
		_fail("Ordinary zero HP must enter dying state without final death.")
		return
	if combat_state == null or combat_state.dead or not combat_state.has_condition("unconscious"):
		_fail("Zero HP did not retain the SRD unconscious/dying state.")
		return
	if bool(game.call("is_death_presentation_started_for_testing")):
		_fail("Death presentation started at zero HP before death was confirmed.")
		return
	if bool(player.call("is_death_animation_active")) or bool(player.call("is_corpse_hold_active")):
		_fail("Player entered a death visual while merely unconscious.")
		return

	combat_state.stable = true
	if bool(game.call("_begin_confirmed_death_presentation")):
		_fail("A stabilized zero-HP player was treated as finally dead.")
		return
	combat_state.stable = false
	combat_state.death_save_failures = 2
	var interrupted_attack_id: int = int(player.call(
		"start_melee_attack_animation",
		player.global_position + Vector2.LEFT * 64.0,
		{"id": "longsword", "properties": ["versatile"]},
		Callable()
	))
	if interrupted_attack_id <= 0:
		_fail("Attack interruption fixture did not start.")
		return
	var reaction_prompt: ReactionChoicePrompt = game.call(
		"get_reaction_choice_prompt_for_testing"
	) as ReactionChoicePrompt
	var death_reaction_options: Array[Dictionary] = [{
		"id": "death_runtime_test_reaction",
		"label": "ТЕСТОВАЯ РЕАКЦИЯ",
		"details": "Death Runtime должен закрыть это окно."
	}]
	reaction_prompt.request_reaction(
		"ТЕСТ ПРИОРИТЕТА СМЕРТИ",
		"Ожидается подтверждённая смерть.",
		death_reaction_options
	)
	await process_frame
	if not reaction_prompt.is_waiting_for_decision():
		_fail("Reaction prompt fixture did not enter its pending state.")
		return
	var finished_signal := Signal(player, &"death_animation_finished")
	var final_result: Dictionary = game.call(
		"apply_damage_to_player",
		1,
		"slashing",
		false,
		null
	) as Dictionary
	if not bool(final_result.get("dead", false)) or not combat_state.dead:
		_fail("Third death-save failure did not confirm final death.")
		return
	if not bool(game.call("is_death_presentation_started_for_testing")):
		_fail("Confirmed final death did not start Death Runtime v1.")
		return
	await process_frame
	if reaction_prompt.is_waiting_for_decision() or reaction_prompt.visible:
		_fail("Confirmed death did not close the pending reaction prompt.")
		return
	if not bool(player.call("is_death_animation_active")):
		_fail("Confirmed final death did not start an authored death animation.")
		return
	if int(player.get("_active_attack_sequence_id")) != 0:
		_fail("Confirmed death did not cancel the active attack animation.")
		return
	if not bool(game_state.get("input_locked")) or not bool(player.call("is_action_animation_locked")):
		_fail("Confirmed death did not lock game and player input.")
		return

	var playing_state: Dictionary = player.call("get_death_visual_state") as Dictionary
	var death_variant_id: String = str(playing_state.get("death_variant_id", ""))
	if death_variant_id not in EXPECTED_DEATH_VARIANTS:
		_fail("Death selector returned an unknown variant: %s" % death_variant_id)
		return
	if str(playing_state.get("direction_id", "")) != "left":
		_fail("Death animation did not preserve the player's last look direction.")
		return
	if sprite.animation != StringName("%s_left" % death_variant_id):
		_fail("Selected death variant and visible animation disagree.")
		return

	player.call("set_facing_direction", Vector2.RIGHT)
	if Vector2(player.call("get_facing_direction")).dot(Vector2.LEFT) < 0.99:
		_fail("Facing changed after death took priority.")
		return
	if int(player.call(
		"start_melee_attack_animation",
		player.global_position + Vector2.RIGHT * 64.0,
		{"id": "longsword", "properties": ["versatile"]},
		Callable()
	)) != -1:
		_fail("Attack animation was accepted while death had priority.")
		return
	player.velocity = Vector2(200.0, 0.0)
	player.call("_physics_process", 1.0 / 60.0)
	if player.velocity != Vector2.ZERO:
		_fail("Movement continued while death animation was active.")
		return

	await finished_signal
	await process_frame
	var minimum_seconds: float = float(
		game.call("get_minimum_death_presentation_seconds_for_testing")
	)
	var elapsed_seconds: float = float(
		game.call("get_death_presentation_elapsed_seconds_for_testing")
	)
	if elapsed_seconds + 0.05 < minimum_seconds:
		_fail(
			"Death animation completed before the %.1f-second transition gate: %.3f"
			% [minimum_seconds, elapsed_seconds]
		)
		return
	if not game.is_inside_tree():
		_fail("Death/load transition replaced the scene before the death animation completed.")
		return
	if not bool(player.call("is_corpse_hold_active")) or sprite.frame != 7:
		_fail("Death animation did not hold its eighth frame as the corpse pose.")
		return
	var corpse_state: Dictionary = player.call("get_death_visual_state") as Dictionary
	if str(corpse_state.get("corpse_state", "")) != "corpse_hold":
		_fail("Completed death state was not persisted as corpse_hold.")
		return
	if character.death_visual_state != corpse_state:
		_fail("Runtime corpse state and serialized player state diverged.")
		return
	if character.last_death_variant_id != death_variant_id:
		_fail("Last death variant was not persisted for no-repeat selection.")
		return
	var library: HumanWarriorAnimationLibrary = player.get("_animation_library") as HumanWarriorAnimationLibrary
	var expected_position: Vector2 = AUTHORED_SPRITE_OFFSET + library.get_death_anchor_offset(
		death_variant_id,
		&"left"
	)
	if sprite.position.distance_to(expected_position) > 0.001:
		_fail("Directional death anchor compensation was not applied.")
		return

	game.queue_free()
	await process_frame
	game_state.call("new_game")
	var restored_character := _build_character("human", 0)
	restored_character.last_death_variant_id = "death_03_base"
	restored_character.death_visual_state = {
		"death_variant_id": "death_03_base",
		"direction_id": "up",
		"corpse_state": "corpse_hold",
		"frame_index": 7
	}
	game_state.set("player_character", restored_character)
	var restored_game: Node = packed.instantiate()
	root.add_child(restored_game)
	for _frame: int in range(8):
		await process_frame
	var restored_player: CharacterBody2D = restored_game.get_node_or_null("Player") as CharacterBody2D
	var restored_sprite: AnimatedSprite2D = (
		restored_player.find_child("CharacterSprite", true, false) as AnimatedSprite2D
		if restored_player != null
		else null
	)
	if (
		restored_player == null
		or restored_sprite == null
		or not bool(restored_player.call("is_corpse_hold_active"))
		or restored_sprite.animation != &"death_03_base_up"
		or restored_sprite.frame != 7
	):
		_fail("Saved corpse variant, direction and held frame were not restored exactly.")
		return
	if (
		not bool(restored_game.call("is_death_presentation_started_for_testing"))
		or not bool(game_state.get("input_locked"))
	):
		_fail("Loaded confirmed corpse did not resume the protected death transition.")
		return
	var restored_combat_state: CombatantState = restored_game.call(
		"get_player_combat_state"
	) as CombatantState
	if restored_combat_state == null or not restored_combat_state.dead:
		_fail("Loaded confirmed corpse did not restore the transient dead combat state.")
		return
	var restored_library: HumanWarriorAnimationLibrary = restored_player.get(
		"_animation_library"
	) as HumanWarriorAnimationLibrary
	var restored_position: Vector2 = AUTHORED_SPRITE_OFFSET + restored_library.get_death_anchor_offset(
		"death_03_base",
		&"up"
	)
	if restored_sprite.position.distance_to(restored_position) > 0.001:
		_fail("Restored corpse did not retain its directional anchor compensation.")
		return
	restored_game.queue_free()
	await process_frame

	game_state.call("new_game")
	var massive_character := _build_character("human", 12)
	game_state.set("player_character", massive_character)
	var massive_game: Node = packed.instantiate()
	root.add_child(massive_game)
	for _frame: int in range(8):
		await process_frame
	var massive_player: CharacterBody2D = massive_game.get_node_or_null("Player") as CharacterBody2D
	if massive_player == null:
		_fail("Massive-damage production player is missing.")
		return
	massive_player.call("set_facing_direction", Vector2.UP)
	var massive_result: Dictionary = massive_game.call(
		"apply_damage_to_player",
		30,
		"slashing",
		false,
		null
	) as Dictionary
	var massive_state: CombatantState = massive_game.call(
		"get_player_combat_state"
	) as CombatantState
	await process_frame
	if (
		not bool(massive_result.get("dead", false))
		or massive_state == null
		or not massive_state.dead
	):
		_fail("Massive damage did not confirm instant final death.")
		return
	if (
		not bool(massive_game.call("is_death_presentation_started_for_testing"))
		or not bool(massive_player.call("is_death_animation_active"))
	):
		_fail("Massive instant death did not start Death Runtime v1.")
		return
	var massive_visual_state: Dictionary = massive_player.call(
		"get_death_visual_state"
	) as Dictionary
	if str(massive_visual_state.get("direction_id", "")) != "up":
		_fail("Massive instant death did not preserve the last look direction.")
		return
	massive_game.queue_free()
	await process_frame

	game_state.call("new_game")
	var fallback_character := _build_character("elf", 0)
	game_state.set("player_character", fallback_character)
	var fallback_game: Node = packed.instantiate()
	root.add_child(fallback_game)
	for _frame: int in range(8):
		await process_frame
	var fallback_player: CharacterBody2D = fallback_game.get_node_or_null("Player") as CharacterBody2D
	if fallback_player == null:
		_fail("Static fallback production player is missing.")
		return
	var fallback_body: Polygon2D = fallback_player.get_node_or_null("Body") as Polygon2D
	var fallback_sprite: AnimatedSprite2D = fallback_player.find_child(
		"CharacterSprite",
		true,
		false
	) as AnimatedSprite2D
	if fallback_body == null or fallback_sprite == null or fallback_sprite.visible:
		_fail("Unsupported character did not retain the static procedural visual.")
		return
	var fallback_started_at_msec: int = Time.get_ticks_msec()
	var fallback_finished := Signal(fallback_player, &"death_animation_finished")
	if int(fallback_player.call("start_confirmed_death_animation", {}, 0.0)) <= 0:
		_fail("Static death fallback did not start.")
		return
	if fallback_body.color.a < 0.9 or not bool(fallback_player.call("is_death_animation_active")):
		_fail("Static death fallback hid the old visual or skipped its presentation interval.")
		return
	await fallback_finished
	if float(Time.get_ticks_msec() - fallback_started_at_msec) / 1000.0 < 0.75:
		_fail("Static death fallback completed before the 0.8-second minimum.")
		return
	if not bool(fallback_player.call("is_corpse_hold_active")):
		_fail("Static death fallback did not enter persistent corpse hold.")
		return

	fallback_game.queue_free()
	await process_frame
	print("Human warrior Death Runtime v1 integration tests passed.")
	quit(0)


func _build_character(race_id: String, current_health: int) -> PlayerCharacter:
	var character := PlayerCharacter.new()
	character.character_name = "Тестовый воин"
	character.character_class_id = "fighter"
	character.character_class_name = "Воин"
	character.race_id = race_id
	character.race_name = "Человек" if race_id == "human" else "Эльф"
	character.maximum_health = 12
	character.current_health = current_health
	character.abilities["constitution"] = 14
	ClassDataSystem.new().ensure_starting_loadout(character)
	return character
