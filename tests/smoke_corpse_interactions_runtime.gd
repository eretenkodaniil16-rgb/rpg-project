extends SceneTree

const GAME_SCENE: String = "res://scenes/game/game.tscn"
const EXPECTED_RUNTIME: String = "res://scripts/game/game_guard_post_polish_runtime.gd"


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
	for _frame: int in range(16):
		await process_frame
	var script: Script = game.get_script() as Script
	if script == null or script.resource_path != EXPECTED_RUNTIME:
		_fail("Game scene does not use nonlethal restraint runtime.")
		return
	game.set_process(false)

	var player: Node2D = game.get_node_or_null("Player") as Node2D
	var guard: Node2D = game.get_node_or_null("StealthTestRoom/ServiceGuard") as Node2D
	var loot_panel: LootContainerPanel = game.call("get_loot_container_panel_for_testing") as LootContainerPanel
	if player == null or guard == null or loot_panel == null:
		_fail("Player, service guard or common loot panel is missing.")
		return

	var lethal := AttackResult.new()
	lethal.hit = true
	lethal.melee_attack = true
	lethal.damage = 99
	lethal.damage_before_mitigation = 99
	guard.call("receive_player_attack", lethal, false)
	await process_frame
	if not bool(guard.call("is_dead_body")):
		_fail("Normal zero-HP defeat did not become a dead body.")
		return
	if not guard.is_in_group("corpse_targets") or guard.is_in_group("combat_targets"):
		_fail("Dead body groups are invalid.")
		return

	player.global_position = guard.global_position + Vector2(48.0, 0.0)
	game.call("_set_selected_target", guard)
	var entries: Dictionary = game.call("_build_catalog_entries") as Dictionary
	var action_ids: Array[String] = _action_ids(entries)
	if "open_selected_body_loot" not in action_ids or "corpse_drag_toggle" not in action_ids or "inspect_target" not in action_ids:
		_fail("Corpse action catalog is incomplete: %s" % JSON.stringify(action_ids))
		return
	if "corpse_loot_all" in action_ids:
		_fail("Legacy Take All corpse action remained beside the common loot panel: %s" % JSON.stringify(action_ids))
		return
	for action_id: String in action_ids:
		if action_id.begins_with("corpse_loot_item__"):
			_fail("Legacy per-item corpse action remained beside the common loot panel: %s" % JSON.stringify(action_ids))
			return

	game.call("_on_feedback_catalog_action_requested", "open_selected_body_loot")
	if not loot_panel.is_open():
		_fail("Common corpse loot panel did not open.")
		return
	var loot_labels: Array[String] = loot_panel.get_item_action_labels_for_testing()
	if "ПОДОБРАТЬ: КОРОТКИЙ МЕЧ" not in loot_labels:
		_fail("Common corpse panel does not expose the Russian shortsword pickup action: %s" % JSON.stringify(loot_labels))
		return
	game.call("take_active_loot_item_for_testing", "shortsword")
	if int(state.call("get_item_count", "shortsword")) != 1:
		_fail("Common loot panel did not transfer the shortsword.")
		return
	loot_panel.close_panel()
	await process_frame
	if bool(state.get("input_locked")):
		_fail("Closing the common corpse panel did not restore input.")
		return

	game.call("_on_catalog_action_requested", "corpse_drag_toggle")
	if game.call("get_dragged_body_for_testing") != guard:
		_fail("Body drag did not start.")
		return
	var initial_body_position: Vector2 = guard.global_position
	player.global_position += Vector2(160.0, 0.0)
	for _frame: int in range(12):
		guard.call("_process", 0.1)
	if guard.global_position.distance_to(initial_body_position) < 20.0:
		_fail("Dragged body did not follow the player.")
		return
	game.call("_on_catalog_action_requested", "corpse_drag_toggle")
	if game.call("get_dragged_body_for_testing") != null:
		_fail("Body drag did not stop.")
		return

	guard.call("reset_combat_state", true)
	await process_frame
	if bool(guard.call("is_body_interactable")) or not guard.is_in_group("context_action_targets") or guard.is_in_group("combat_targets"):
		_fail("Full reset did not restore the living non-combat patrol observer.")
		return
	state.call("add_item", "explorer_pack", 1, false)
	game.call("_set_selected_target", guard)
	game.call("_on_catalog_action_requested", "toggle_nonlethal_attack")
	if not bool(game.call("is_nonlethal_mode_enabled_for_testing")):
		_fail("Nonlethal mode did not enable through the action catalog handler.")
		return

	var knockout := AttackResult.new()
	knockout.hit = true
	knockout.melee_attack = true
	knockout.damage = 99
	knockout.damage_before_mitigation = 99
	game.call("_prepare_nonlethal_knockout", knockout, guard)
	if not knockout.nonlethal_knockout:
		_fail("Eligible lethal melee damage was not converted to a nonlethal knockout.")
		return
	guard.call("receive_player_attack", knockout, false)
	await process_frame
	if not bool(guard.call("is_unconscious_body")) or bool(guard.call("is_dead_body")):
		_fail("Nonlethal melee defeat did not create a living unconscious body.")
		return
	if int(guard.call("get_current_health")) != 1:
		_fail("2024 SRD knockout did not leave the target at 1 HP.")
		return

	player.global_position = guard.global_position + Vector2(48.0, 0.0)
	game.call("_set_selected_target", guard)
	entries = game.call("_build_catalog_entries") as Dictionary
	action_ids = _action_ids(entries)
	if "bind_unconscious__explorer_pack" not in action_ids:
		_fail("Binding action is missing for an available restraint source: %s" % JSON.stringify(action_ids))
		return
	game.call("_on_catalog_action_requested", "bind_unconscious__explorer_pack")
	if not bool(guard.call("is_bound_body")):
		_fail("Unconscious target was not bound.")
		return
	var binding: Dictionary = guard.call("get_binding_context") as Dictionary
	if str(binding.get("item_id", "")) != "explorer_pack" or int(binding.get("escape_dc", 0)) <= 0:
		_fail("Binding context is incomplete: %s" % JSON.stringify(binding))
		return

	entries = game.call("_build_catalog_entries") as Dictionary
	action_ids = _action_ids(entries)
	if "release_body_restraint" not in action_ids:
		_fail("Release restraint action is missing.")
		return
	game.call("_on_catalog_action_requested", "release_body_restraint")
	if bool(guard.call("is_bound_body")):
		_fail("Release action did not free the restraint source.")
		return

	var ranged := AttackResult.new()
	ranged.hit = true
	ranged.melee_attack = false
	ranged.damage = 99
	game.call("_prepare_nonlethal_knockout", ranged, guard)
	if ranged.nonlethal_knockout:
		_fail("Ranged damage incorrectly received the nonlethal knockout option.")
		return

	var registry := CorpseInteractionSystem.new()
	var stored: Dictionary = registry.get_record(state, "service_guard")
	if registry.get_body_position(stored).distance_to(guard.global_position) > 1.0:
		_fail("Body position was not persisted.")
		return

	game.queue_free()
	await process_frame
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Lethal default, common corpse loot panel, nonlethal knockout and restraint regression passed.")
	quit(0)


func _action_ids(entries: Dictionary) -> Array[String]:
	var result: Array[String] = []
	for entry_value: Variant in entries.get("action", []) as Array:
		if entry_value is Dictionary:
			result.append(str((entry_value as Dictionary).get("id", "")))
	return result


func _make_hero() -> PlayerCharacter:
	var hero := PlayerCharacter.new()
	hero.character_name = "Испытатель тел"
	hero.character_class_id = "fighter"
	hero.character_class_name = "Воин"
	hero.race_id = "human"
	hero.race_name = "Человек"
	hero.level = 1
	hero.maximum_health = 14
	hero.current_health = 14
	hero.hit_die_size = 10
	hero.hit_dice_maximum = 1
	hero.hit_dice_current = 1
	return hero


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
