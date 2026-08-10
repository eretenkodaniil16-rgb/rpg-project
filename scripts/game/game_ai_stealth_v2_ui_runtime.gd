extends "res://scripts/game/game_ai_stealth_v2_runtime.gd"


func _refresh_alert_indicator() -> void:
	super._refresh_alert_indicator()
	if _alert_indicator == null:
		return
	# Глобальный HUD сообщает только собственное состояние героя. Числовой
	# результат Скрытности остаётся внутренним DC восприятия NPC и не превращает
	# интерфейс в диагностическую панель.
	if _exploration_hidden:
		_alert_indicator.text = "СКРЫТ"
