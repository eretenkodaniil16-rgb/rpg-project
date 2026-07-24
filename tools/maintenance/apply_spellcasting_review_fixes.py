from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one match in {path}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


spell_path = ROOT / "scripts/systems/spellcasting_system.gd"
replace_once(
    spell_path,
    '''\t\tfor spell_id: String in _string_array(profile.get("starting_spells", [])):
\t\t\tchanged = _append_unique(character.known_features, spell_id) or changed
\t\tvar profile_prepared: Array[String] = get_prepared_spell_ids(character)
\t\tfor spell_id: String in _string_array(profile.get("starting_prepared", [])):
\t\t\tif spell_id not in profile_prepared:
\t\t\t\tprofile_prepared.append(spell_id)
\t\t\t\tchanged = true
\t\t_store_prepared_spell_ids(character, profile_prepared)
''',
    '''\t\tfor spell_id: String in _string_array(profile.get("starting_spells", [])):
\t\t\tchanged = _append_unique(character.known_features, spell_id) or changed
\t\tvar had_prepared_state: bool = character.class_resources.has(PREPARED_SPELLS_STATE_KEY)
\t\tvar profile_prepared: Array[String] = get_prepared_spell_ids(character)
\t\tif not had_prepared_state:
\t\t\tfor spell_id: String in _string_array(profile.get("starting_prepared", [])):
\t\t\t\tif spell_id not in profile_prepared:
\t\t\t\t\tprofile_prepared.append(spell_id)
\t\t\t\t\tchanged = true
\t\t_store_prepared_spell_ids(character, profile_prepared)
\t\tchanged = changed or not had_prepared_state
''',
)
replace_once(
    spell_path,
    '''func begin_concentration(character: PlayerCharacter, spell_id: String) -> String:
\tif character == null:
\t\treturn ""
\tvar previous: String = str(character.class_resources.get(CONCENTRATION_STATE_KEY, ""))
\tcharacter.class_resources[CONCENTRATION_STATE_KEY] = spell_id
\treturn previous


func end_concentration(character: PlayerCharacter) -> String:
\tif character == null:
\t\treturn ""
\tvar previous: String = str(character.class_resources.get(CONCENTRATION_STATE_KEY, ""))
\tcharacter.class_resources.erase(CONCENTRATION_STATE_KEY)
\treturn previous


func get_concentration_spell_id(character: PlayerCharacter) -> String:
\treturn "" if character == null else str(character.class_resources.get(CONCENTRATION_STATE_KEY, ""))
''',
    '''func begin_concentration(character: PlayerCharacter, spell_id: String) -> String:
\tif character == null:
\t\treturn ""
\tvar previous: String = str(character.class_resources.get(CONCENTRATION_STATE_KEY, ""))
\tif not previous.is_empty() and previous != spell_id:
\t\t_clear_concentration_bound_effect(character, previous)
\tcharacter.class_resources[CONCENTRATION_STATE_KEY] = spell_id
\treturn previous


func end_concentration(character: PlayerCharacter) -> String:
\tif character == null:
\t\treturn ""
\tvar previous: String = str(character.class_resources.get(CONCENTRATION_STATE_KEY, ""))
\tcharacter.class_resources.erase(CONCENTRATION_STATE_KEY)
\t_clear_concentration_bound_effect(character, previous)
\treturn previous


func get_concentration_spell_id(character: PlayerCharacter) -> String:
\treturn "" if character == null else str(character.class_resources.get(CONCENTRATION_STATE_KEY, ""))


func sync_concentration_to_combat_state(character: PlayerCharacter, combat_state: CombatantState, source_id: int = 0) -> void:
\tif combat_state == null:
\t\treturn
\tvar spell_id: String = get_concentration_spell_id(character)
\tif spell_id.is_empty():
\t\tcombat_state.clear_concentration()
\telse:
\t\tcombat_state.set_concentration(spell_id, source_id)


func _clear_concentration_bound_effect(character: PlayerCharacter, spell_id: String) -> void:
\tif character == null or spell_id.is_empty():
\t\treturn
\tmatch spell_id:
\t\t"detect_magic":
\t\t\tcharacter.active_effects.erase(DETECT_MAGIC_UNTIL_KEY)
\t\t"hunters_mark":
\t\t\tcharacter.active_effects.erase("hunters_mark_hits")
''',
)

game_path = ROOT / "scripts/game/game_final_v017.gd"
replace_once(
    game_path,
    '''\tsuper._ready()
\tif _attack_popup != null:
''',
    '''\tsuper._ready()
\tvar concentration_source_id: int = player.get_instance_id() if player != null else 0
\t_spellcasting_runtime.sync_concentration_to_combat_state(
\t\tGameState.player_character,
\t\t_player_combat_state,
\t\tconcentration_source_id
\t)
\tif _attack_popup != null:
''',
)

test_path = ROOT / "tests/test_spellcasting_and_rituals.gd"
replace_once(
    test_path,
    '''\tif not bool(unprepare_result.get("success", false)) or spells.is_prepared(wizard, "magic_missile"):
\t\t_fail("Prepared spell could not be removed from preparation.")
\t\treturn
\tif spells.can_cast_spell(wizard, magic_missile):
''',
    '''\tif not bool(unprepare_result.get("success", false)) or spells.is_prepared(wizard, "magic_missile"):
\t\t_fail("Prepared spell could not be removed from preparation.")
\t\treturn
\tspells.ensure_character(wizard, false)
\tif spells.is_prepared(wizard, "magic_missile"):
\t\t_fail("Starting preparation was incorrectly re-applied after an explicit unprepare.")
\t\treturn
\tif spells.can_cast_spell(wizard, magic_missile):
''',
)
replace_once(
    test_path,
    '''\tspells.cleanup_expired_effects(wizard, 500)
\tif not spells.get_concentration_spell_id(wizard).is_empty():
\t\t_fail("Expired concentration ritual was not cleaned up.")
\t\treturn

\tvar comprehend: Dictionary = spells.get_spell_definition("comprehend_languages")
''',
    '''\tspells.cleanup_expired_effects(wizard, 500)
\tif not spells.get_concentration_spell_id(wizard).is_empty():
\t\t_fail("Expired concentration ritual was not cleaned up.")
\t\treturn

\twizard.active_effects[SpellcastingSystem.DETECT_MAGIC_UNTIL_KEY] = 520
\tspells.begin_concentration(wizard, "detect_magic")
\tvar combat_state := CombatantState.new()
\tspells.sync_concentration_to_combat_state(wizard, combat_state, 77)
\tif combat_state.concentrating_on != "detect_magic" or combat_state.concentration_source_id != 77:
\t\t_fail("Saved ritual concentration was not synchronized to CombatantState.")
\t\treturn
\tspells.end_concentration(wizard)
\tif spells.has_detect_magic(wizard, 501):
\t\t_fail("Ending concentration did not remove the concentration-bound Detect Magic effect.")
\t\treturn

\tvar comprehend: Dictionary = spells.get_spell_definition("comprehend_languages")
''',
)

print("Spellcasting review fixes applied.")
