extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const MAGE_SCENE: String = "res://scenes/game/combat_ai_training_mage.tscn"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path("user://savegame.json")
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	state.call("new_game")
	state.set("player_character", _make_hero())

	var packed: PackedScene = load(GAME_SCENE) as PackedScene
	if packed == null:
		_fail("Game scene could not be loaded.")
		return
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame: int in range(18):
		await process_frame
	game.set_process(false)

	var mage_packed: PackedScene = load(MAGE_SCENE) as PackedScene
	var mage: Node = mage_packed.instantiate() if mage_packed != null else null
	if mage == null:
		_fail("Training mage scene could not be instantiated.")
		return
	game.add_child(mage)
	mage.global_position = Vector2(560.0, 360.0)
	if not bool(mage.call("activate_combat_participant")):
		_fail("Training mage could not become a combat participant.")
		return
	var mage_profile: Dictionary = game.call("get_combat_ai_profile_for_testing", "training_mage") as Dictionary
	if str(mage_profile.get("role", "")) != AdvancedNpcCombatAiSystem.ROLE_CASTER:
		_fail("Training mage does not use caster profile.")
		return

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var caretaker: Node2D = game.get_node_or_null("Caretaker") as Node2D
	var guard: Node2D = game.get_node_or_null("StealthTestRoom/ServiceGuard") as Node2D
	if player == null or caretaker == null or guard == null:
		_fail("Required runtime actors are missing.")
		return
	var defeat := AttackResult.new()
	defeat.hit = true
	defeat.damage = 99
	defeat.damage_before_mitigation = 99
	guard.call("receive_player_attack", defeat, false)
	await process_frame
	if not bool(guard.call("is_dead_body")):
		_fail("Service guard did not become a dead body for casualty awareness.")
		return

	caretaker.global_position = guard.global_position + Vector2(80.0, 0.0)
	var profile: Dictionary = game.call("get_combat_ai_profile_for_testing", "caretaker") as Dictionary
	var observation: Dictionary = game.call("_observe_allied_bodies", caretaker, "caretaker", profile) as Dictionary
	if not bool(observation.get("new", false)):
		_fail("Caretaker did not acknowledge a visible allied corpse.")
		return
	var repeated: Dictionary = game.call("_observe_allied_bodies", caretaker, "caretaker", profile) as Dictionary
	if bool(repeated.get("new", false)):
		_fail("The same corpse triggered a second new-casualty event.")
		return
	var casualty_context: Dictionary = game.call("get_casualty_context_for_testing", "caretaker") as Dictionary
	if int(casualty_context.get("casualty_count", 0)) != 1:
		_fail("Squad casualty blackboard did not store the observed body.")
		return

	player.global_position = Vector2(320.0, 360.0)
	mage.global_position = Vector2(560.0, 360.0)
	var safe_plan: Dictionary = game.call("evaluate_spell_plan_for_testing", mage, "training_mage", mage.global_position) as Dictionary
	if safe_plan.is_empty():
		_fail("Caster could not select any legal spell.")
		return
	var chosen_spell: String = str(safe_plan.get("spell_id", ""))
	if chosen_spell not in mage.call("get_combat_spell_ids"):
		_fail("Caster selected a spell outside its data-driven list: %s" % chosen_spell)
		return

	guard.global_position = Vector2(440.0, 360.0)
	var blocked_area_plan: Dictionary = game.call("evaluate_spell_plan_for_testing", mage, "training_mage", mage.global_position) as Dictionary
	if str(blocked_area_plan.get("spell_id", "")) in ["burning_hands", "thunderwave"]:
		_fail("Caster selected an area spell through a living ally.")
		return

	var corpse_system := CorpseInteractionSystem.new()
	if corpse_system.get_profile("training_mage").is_empty():
		_fail("Training mage has no corpse and loot profile.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Advanced runtime corpse awareness, caster role and safe spell planning passed.")
	quit(0)


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель тактики"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 1
	hero.maximum_health = 20
	hero.current_health = 20
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
