class_name ClassAbilitySubclassSystem
extends ClassAbilitySystem


func use_self_ability(
	character: PlayerCharacter,
	ability: Dictionary,
	casting_context: Dictionary = {}
) -> Dictionary:
	var effect: String = str(ability.get("effect", ""))
	if effect not in ["guardian_stance", "tactical_focus"]:
		return super.use_self_ability(character, ability, casting_context)
	if character == null:
		return {"success": false, "message": "Персонаж недоступен."}
	var resource_key: String = str(ability.get("resource_key", ""))
	if resource_key.is_empty() or not character.consume_resource(resource_key, 1):
		return {"success": false, "message": "Применения способности закончились."}
	match effect:
		"guardian_stance":
			character.active_effects[FighterSubclassSystem.GUARDIAN_ACTIVE_KEY] = true
			return {
				"success": true,
				"message": "Опорная стойка активна до начала следующего хода.",
				"healing": 0
			}
		"tactical_focus":
			character.active_effects[FighterSubclassSystem.TACTICAL_READY_KEY] = true
			return {
				"success": true,
				"message": "Следующая оружейная атака подготовлена.",
				"healing": 0
			}
	return {"success": false, "message": "Способность не поддерживается."}
