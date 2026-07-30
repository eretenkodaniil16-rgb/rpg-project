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
	var caretaker_profile: Dictionary = system.get_profile("caretaker")
	assert(str(caretaker_profile.get("defeat_outcome", "")) == CorpseInteractionSystem.BODY_DEAD)

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

	var unconscious: Dictionary = system.mark_defeated(
		state,
		"caretaker",
		Vector2(900.0, 360.0),
		CorpseInteractionSystem.BODY_UNCONSCIOUS
	)
	assert(str(unconscious.get("body_state", "")) == CorpseInteractionSystem.BODY_UNCONSCIOUS)
	var illegal_loot: Dictionary = system.take_item(state, "caretaker", "gold_coin", 1)
	assert(not bool(illegal_loot.get("success", false)))

	state.call("add_item", "explorer_pack", 1, false)
	var sources: Array[Dictionary] = system.get_available_restraint_sources(state, "caretaker")
	var explorer_source: Dictionary = {}
	for source: Dictionary in sources:
		if str(source.get("item_id", "")) == "explorer_pack":
			explorer_source = source
			break
	assert(not explorer_source.is_empty())
	var bind_result: Dictionary = system.bind_unconscious(state, "caretaker", "explorer_pack")
	assert(bool(bind_result.get("success", false)))
	assert(system.is_bound(state, "caretaker"))
	assert(str(system.get_binding_context(state, "caretaker").get("item_id", "")) == "explorer_pack")

	var second_unconscious: Dictionary = system.mark_defeated(
		state,
		"service_guard",
		Vector2(760.0, 505.0),
		CorpseInteractionSystem.BODY_UNCONSCIOUS
	)
	assert(str(second_unconscious.get("body_state", "")) == CorpseInteractionSystem.BODY_UNCONSCIOUS)
	var second_sources: Array[Dictionary] = system.get_available_restraint_sources(state, "service_guard")
	for source: Dictionary in second_sources:
		assert(str(source.get("item_id", "")) != "explorer_pack")

	state.call("save_game")
	state.set("story_flags", {})
	assert(bool(state.call("load_game")))
	assert(system.is_bound(state, "caretaker"))
	var release_result: Dictionary = system.release_restraint(state, "caretaker")
	assert(bool(release_result.get("success", false)))
	assert(not system.is_bound(state, "caretaker"))
	var freed_sources: Array[Dictionary] = system.get_available_restraint_sources(state, "service_guard")
	var explorer_available_again: bool = false
	for source: Dictionary in freed_sources:
		if str(source.get("item_id", "")) == "explorer_pack":
			explorer_available_again = true
	assert(explorer_available_again)

	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	print("Corpse death, nonlethal override, restraint reservation and save/load passed.")
	quit(0)


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
