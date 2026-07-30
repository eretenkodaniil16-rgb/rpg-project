extends SceneTree


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var selector := NpcSpellSelectionSystem.new()
	var policy: Dictionary = {
		"friendly_fire_tolerance": 0,
		"slot_reserve": 1,
		"slot_conservation": 0.6
	}
	var safe_burning: Dictionary = {
		"available": true,
		"line_of_sight": true,
		"distance_feet": 10,
		"slots_remaining": 3,
		"target_health_ratio": 0.8,
		"hostile_hits": 1,
		"friendly_hits": 0,
		"caster_hit": false
	}
	var unsafe_burning: Dictionary = safe_burning.duplicate(true)
	unsafe_burning["friendly_hits"] = 1
	var burning: Dictionary = selector.get_spell("burning_hands")
	assert(selector.score_spell_option(burning, safe_burning, policy) > NpcSpellSelectionSystem.BLOCKED_SCORE * 0.5)
	assert(selector.score_spell_option(burning, unsafe_burning, policy) == NpcSpellSelectionSystem.BLOCKED_SCORE)

	var contexts: Dictionary = {
		"burning_hands": unsafe_burning,
		"magic_missile": {
			"available": true,
			"line_of_sight": true,
			"distance_feet": 35,
			"slots_remaining": 3,
			"target_health_ratio": 0.22,
			"hostile_hits": 1,
			"friendly_hits": 0,
			"caster_hit": false
		},
		"sorcerous_burst": {
			"available": true,
			"line_of_sight": true,
			"distance_feet": 35,
			"slots_remaining": 0,
			"target_health_ratio": 0.22,
			"hostile_hits": 1,
			"friendly_hits": 0,
			"caster_hit": false
		}
	}
	var finisher: Dictionary = selector.choose_spell(["burning_hands", "magic_missile", "sorcerous_burst"], contexts, policy)
	assert(str(finisher.get("spell_id", "")) == "magic_missile")

	contexts["magic_missile"]["slots_remaining"] = 1
	contexts["magic_missile"]["target_health_ratio"] = 0.9
	contexts["sorcerous_burst"]["target_health_ratio"] = 0.9
	var conserve: Dictionary = selector.choose_spell(["magic_missile", "sorcerous_burst"], contexts, policy)
	assert(str(conserve.get("spell_id", "")) == "sorcerous_burst")

	var thunder: Dictionary = selector.get_spell("thunderwave")
	var control_score: float = selector.score_spell_option(thunder, {
		"available": true,
		"line_of_sight": true,
		"distance_feet": 5,
		"slots_remaining": 3,
		"target_health_ratio": 1.0,
		"hostile_hits": 1,
		"friendly_hits": 0,
		"caster_hit": false
	}, policy)
	assert(control_score > 0.0)

	print("NPC spell selection, friendly-fire rejection, slot conservation and finisher choice passed.")
	quit(0)
