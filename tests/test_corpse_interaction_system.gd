extends SceneTree

const SAVE_PATH: String = "user://savegame.json"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	if state == null:
		_fail("GameState autoload is missing.")
		return
	var save_path: String = ProjectSettings.globalize_path(SAVE_PATH)
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	state.call("new_game")
	var system := CorpseInteractionSystem.new()
	var guard_profile: Dictionary = system.get_profile("service_guard")
	assert(str(guard_profile.get("defeat_outcome", "")) == CorpseInteractionSystem.BODY_DEAD)
	var record: Dictionary = system.mark_defeated(state, "service_guard", Vector2(410.0, 275.0))
	assert(str(record.get("body_state", "")) == CorpseInteractionSystem.BODY_DEAD)
	assert(system.get_remaining_loot(state, "service_guard").size() == 3)

	var sword_result: Dictionary = system.take_item(state, "service_guard", "shortsword", 1)
	assert(bool(sword_result.get("success", false)))
	assert(int(state.call("get_item_count", "shortsword")) == 1)
	var duplicate_sword: Dictionary = system.take_item(state, "service_guard", "shortsword", 1)
	assert(not bool(duplicate_sword.get("success", false)))

	var all_result: Dictionary = system.take_all(state, "service_guard")
	assert(bool(all_result.get("success", false)))
	assert(int(state.call("get_item_count", "leather_armor")) == 1)
	assert(int(state.call("get_item_count", "gold_coin")) == 4)
	assert(system.get_remaining_loot(state, "service_guard").is_empty())

	assert(system.update_body_position(state, "service_guard", Vector2(700.0, 505.0), true))
	state.set("story_flags", {})
	state.set("inventory", {})
	assert(bool(state.call("load_game")))
	var loaded_record: Dictionary = system.get_record(state, "service_guard")
	assert(system.get_body_position(loaded_record) == Vector2(700.0, 505.0))
	assert(int(state.call("get_item_count", "gold_coin")) == 4)
	assert(system.get_remaining_loot(state, "service_guard").is_empty())

	var unconscious: Dictionary = system.mark_defeated(state, "caretaker", Vector2(900.0, 360.0))
	assert(str(unconscious.get("body_state", "")) == CorpseInteractionSystem.BODY_UNCONSCIOUS)
	var illegal_loot: Dictionary = system.take_item(state, "caretaker", "gold_coin", 1)
	assert(not bool(illegal_loot.get("success", false)))

	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Corpse registry, loot transfer, body position and save/load passed.")
	quit(0)


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
