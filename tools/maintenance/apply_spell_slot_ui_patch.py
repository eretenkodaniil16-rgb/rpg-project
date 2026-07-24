from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


path = ROOT / "scripts/ui/character_hub.gd"
text = path.read_text(encoding="utf-8")
text = replace_once(text, "var _spell_prepare: Button\nvar _ritual: Button\n", "var _spell_prepare: Button\nvar _slot_level: OptionButton\nvar _ritual: Button\n", "slot field")
text = replace_once(
    text,
    '''\t_spell_prepare.hide()
\tright.add_child(_spell_prepare)
\t_ritual = Button.new()
''',
    '''\t_spell_prepare.hide()
\tright.add_child(_spell_prepare)
\t_slot_level = OptionButton.new()
\t_slot_level.name = "SpellSlotLevel"
\t_slot_level.custom_minimum_size = Vector2(0.0, 52.0)
\t_slot_level.item_selected.connect(_slot_level_selected)
\t_slot_level.hide()
\tright.add_child(_slot_level)
\t_ritual = Button.new()
''',
    "slot build",
)
text = replace_once(
    text,
    '''\telse:
\t\t_prepare.hide()
\t\t_spell_prepare.hide()
\t\t_ritual.hide()
''',
    '''\telse:
\t\t_prepare.hide()
\t\t_spell_prepare.hide()
\t\t_slot_level.hide()
\t\t_ritual.hide()
''',
    "empty powers hide",
)
text = replace_once(
    text,
    '''func _refresh_spell_buttons(ability: Dictionary) -> void:
\t_spell_prepare.hide()
\t_ritual.hide()
\tif not _is_spell(ability):
\t\treturn
\tvar spell_level: int = maxi(int(ability.get("spell_level", 0)), 0)
\tvar always_prepared: bool = spell_level == 0 or bool(ability.get("always_prepared", false))
\tif spell_level > 0 and not always_prepared:
\t\t_spell_prepare.show()
\t\tvar prepared: bool = _spellcasting.is_prepared(_hero, _selected_power)
\t\t_spell_prepare.text = "СНЯТЬ С ПОДГОТОВКИ" if prepared else "ПОДГОТОВИТЬ ЗАКЛИНАНИЕ"
\tif bool(ability.get("ritual", false)):
\t\t_ritual.show()
\t\t_ritual.disabled = not _spellcasting.can_cast_spell(_hero, ability, true, _is_combat_active())
\t\t_ritual.text = "РИТУАЛ НЕДОСТУПЕН" if _ritual.disabled else "СОТВОРИТЬ КАК РИТУАЛ"
''',
    '''func _refresh_spell_buttons(ability: Dictionary) -> void:
\t_spell_prepare.hide()
\t_slot_level.hide()
\t_ritual.hide()
\tif not _is_spell(ability):
\t\treturn
\tvar spell_level: int = maxi(int(ability.get("spell_level", 0)), 0)
\tvar always_prepared: bool = spell_level == 0 or bool(ability.get("always_prepared", false))
\tif spell_level > 0:
\t\t_refresh_slot_level_selector(ability, spell_level)
\tif spell_level > 0 and not always_prepared:
\t\t_spell_prepare.show()
\t\tvar prepared: bool = _spellcasting.is_prepared(_hero, _selected_power)
\t\t_spell_prepare.text = "СНЯТЬ С ПОДГОТОВКИ" if prepared else "ПОДГОТОВИТЬ ЗАКЛИНАНИЕ"
\tif bool(ability.get("ritual", false)):
\t\t_ritual.show()
\t\t_ritual.disabled = not _spellcasting.can_cast_spell(_hero, ability, true, _is_combat_active())
\t\t_ritual.text = "РИТУАЛ НЕДОСТУПЕН" if _ritual.disabled else "СОТВОРИТЬ КАК РИТУАЛ"


func _refresh_slot_level_selector(ability: Dictionary, spell_level: int) -> void:
\tvar levels: Array[int] = _spellcasting.get_available_slot_levels(_hero, spell_level, false)
\tif levels.is_empty():
\t\treturn
\tvar selected_level: int = _spellcasting.get_selected_slot_level(_hero, _selected_power)
\tif selected_level not in levels:
\t\tselected_level = levels[0]
\t\t_spellcasting.set_selected_slot_level(_hero, _selected_power, selected_level)
\t_slot_level.set_block_signals(true)
\t_slot_level.clear()
\tvar selected_index: int = 0
\tfor index: int in range(levels.size()):
\t\tvar level: int = levels[index]
\t\tvar resource_key: String = _spellcasting.slot_resource_key(_hero, level)
\t\t_slot_level.add_item("ЯЧЕЙКА %d УРОВНЯ · %d/%d" % [level, _hero.get_resource(resource_key), _hero.get_resource_maximum(resource_key)])
\t\t_slot_level.set_item_metadata(index, level)
\t\tif level == selected_level:
\t\t\tselected_index = index
\t_slot_level.select(selected_index)
\t_slot_level.set_block_signals(false)
\t_slot_level.show()


func _slot_level_selected(index: int) -> void:
\tif _hero == null or _selected_power.is_empty() or index < 0 or index >= _slot_level.item_count:
\t\treturn
\tvar level: int = int(_slot_level.get_item_metadata(index))
\tvar response: Dictionary = _spellcasting.set_selected_slot_level(_hero, _selected_power, level)
\tif not bool(response.get("success", false)):
\t\t_details.text = str(response.get("message", "Уровень ячейки недоступен."))
\t\treturn
\tvar state: Node = _game_state()
\tif state != null:
\t\tstate.call("save_game")
\tvar ability: Dictionary = _class_data.get_ability_definition(_selected_power)
\t_select_power(ability)
''',
    "refresh spell buttons",
)
path.write_text(text, encoding="utf-8")

smoke_path = ROOT / "tests/smoke_spellcasting_ritual_ui.gd"
smoke = smoke_path.read_text(encoding="utf-8")
smoke = replace_once(smoke, 'wizard.character_class_name = "Волшебник"\n', 'wizard.character_class_name = "Волшебник"\n\twizard.level = 5\n', "smoke wizard level")
smoke = replace_once(
    smoke,
    '''\tvar ritual_button: Button = hub.get("_ritual") as Button
\tvar spell_prepare_button: Button = hub.get("_spell_prepare") as Button
\tvar quick_button: Button = hub.get("_prepare") as Button
\tif ritual_button == null or spell_prepare_button == null or quick_button == null:
\t\t_fail("Spell preparation, ritual or quick-action button was not built.")
''',
    '''\tvar ritual_button: Button = hub.get("_ritual") as Button
\tvar spell_prepare_button: Button = hub.get("_spell_prepare") as Button
\tvar slot_level_selector: OptionButton = hub.get("_slot_level") as OptionButton
\tvar quick_button: Button = hub.get("_prepare") as Button
\tif ritual_button == null or spell_prepare_button == null or slot_level_selector == null or quick_button == null:
\t\t_fail("Spell preparation, slot level, ritual or quick-action control was not built.")
''',
    "smoke controls",
)
smoke = replace_once(
    smoke,
    '''\tif not spell_prepare_button.is_visible_in_tree():
\t\t_fail("Level-one spell preparation control was not visible.")
\t\treturn

\tprint("spell-ui checkpoint 6: inspect character summary")
''',
    '''\tif not spell_prepare_button.is_visible_in_tree():
\t\t_fail("Level-one spell preparation control was not visible.")
\t\treturn
\tif not slot_level_selector.is_visible_in_tree() or slot_level_selector.item_count != 3:
\t\t_fail("Level-five Wizard did not receive three selectable spell-slot levels.")
\t\treturn
\tvar level_two_index: int = -1
\tfor index: int in range(slot_level_selector.item_count):
\t\tif int(slot_level_selector.get_item_metadata(index)) == 2:
\t\t\tlevel_two_index = index
\t\t\tbreak
\tif level_two_index < 0:
\t\t_fail("Level-two spell slot was absent from the selector.")
\t\treturn
\thub.call("_slot_level_selected", level_two_index)
\tawait process_frame
\tif SpellcastingSystem.new().get_selected_slot_level(wizard, "magic_missile") != 2:
\t\t_fail("Selected spell-slot level was not persisted on the character.")
\t\treturn

\tprint("spell-ui checkpoint 6: inspect character summary")
''',
    "smoke slot selection",
)
smoke_path.write_text(smoke, encoding="utf-8")
print("Spell slot UI patch applied.")
