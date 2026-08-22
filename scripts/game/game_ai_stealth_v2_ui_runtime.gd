extends "res://scripts/game/game_party_stealth_v3_combat_bridge_runtime.gd"


func _refresh_alert_indicator() -> void:
	super._refresh_alert_indicator()
	if _alert_indicator == null:
		return
	# Глобальный HUD сообщает только состояние скрытности управляемого сейчас
	# участника отряда. Числовой результат проверки остаётся внутренним DC NPC.
	var active_actor: Node = get_active_player_controlled_actor()
	if is_instance_valid(active_actor) and _is_party_target_hidden_v3(active_actor):
		_alert_indicator.text = "СКРЫТ"
