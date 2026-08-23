extends "res://scripts/game/game_party_stealth_v3_runtime.gd"


func _refresh_alert_indicator() -> void:
	super._refresh_alert_indicator()
	if _alert_indicator == null:
		return
	# Глобальный HUD сообщает только состояние скрытности управляемого сейчас
	# участника отряда. Числовой результат проверки остаётся внутренним DC NPC.
	var active_actor: Node = get_active_player_controlled_actor()
	if is_instance_valid(active_actor) and _is_party_target_hidden_v3(active_actor):
		_alert_indicator.text = "СКРЫТ"


# Keep the existing AI/Stealth v2 smoke hook compatible with the final runtime.
# The production source of truth is Party Stealth v3; routing the legacy test
# setter through it prevents the old helper from creating a split stealth state.
func set_exploration_stealth_total_v2_for_testing(total: int) -> void:
	if is_instance_valid(player):
		_set_party_target_stealth_v3(player, total > 0, maxi(total, 0))
		return
	super.set_exploration_stealth_total_v2_for_testing(total)
