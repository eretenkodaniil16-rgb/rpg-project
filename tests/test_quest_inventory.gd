extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var state: Node = root.get_node_or_null("GameState")
	assert(state != null)
	state.call("new_game")

	var active: Array = state.call("get_quests_by_status", "active") as Array
	assert(active.size() == 1)
	assert(str((active[0] as Dictionary).get("id", "")) == "first_steps")
	assert(int((active[0] as Dictionary).get("stage_index", -1)) == 0)

	state.call("report_quest_event", "talked_to_caretaker")
	active = state.call("get_quests_by_status", "active") as Array
	assert(int((active[0] as Dictionary).get("stage_index", -1)) == 1)

	state.call("report_quest_event", "hit_training_dummy")
	active = state.call("get_quests_by_status", "active") as Array
	assert(int((active[0] as Dictionary).get("stage_index", -1)) == 2)

	state.call("report_quest_event", "talked_to_caretaker")
	active = state.call("get_quests_by_status", "active") as Array
	var completed: Array = state.call("get_quests_by_status", "completed") as Array
	assert(active.is_empty())
	assert(completed.size() == 1)
	assert(int(state.call("get_item_count", "apprentice_token")) == 1)
	assert(int((state.get("player_character") as PlayerCharacter).experience) == 300)
	assert(bool(state.call("has_claimed_experience_reward", "quest_first_steps_complete")))
	state.call("report_quest_event", "talked_to_caretaker")
	assert(int((state.get("player_character") as PlayerCharacter).experience) == 300)

	state.call("add_item", "straw_scrap", 3, false)
	assert(int(state.call("get_item_count", "straw_scrap")) == 3)
	assert(bool(state.call("has_item", "straw_scrap", 2)))
	assert(bool(state.call("remove_item", "straw_scrap", 1, false)))
	assert(int(state.call("get_item_count", "straw_scrap")) == 2)

	var entries: Array = state.call("get_inventory_entries") as Array
	assert(entries.size() == 2)
	print("Quest, experience reward and inventory tests passed.")
	quit(0)
