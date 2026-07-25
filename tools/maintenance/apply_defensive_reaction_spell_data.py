#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ABILITIES_PATH = ROOT / "data/abilities/abilities.json"
CLASSES_PATH = ROOT / "data/classes/classes.json"

SHIELD = {
    "id": "shield_spell",
    "name": "Щит",
    "kind": "reaction",
    "is_spell": True,
    "spell_level": 1,
    "school": "Ограждение",
    "target": "self",
    "effect": "shield_reaction",
    "resource_key": "spell_slots_1",
    "casting_time_text": "Реакция",
    "casting_time_kind": "reaction",
    "reaction_trigger": "hit_by_attack_roll_or_targeted_by_magic_missile",
    "components": ["v", "s"],
    "duration": "until_start_of_next_turn",
    "armor_class_bonus": 5,
    "blocks_magic_missile": True,
    "description": "Реакция после попадания броском атаки или выбора целью Магической стрелы. До начала следующего хода КД повышается на 5, включая против вызвавшей реакцию атаки; Магическая стрела не наносит урон.",
    "button": "ЩИТ",
}

ABSORB_ELEMENTS = {
    "id": "absorb_elements",
    "name": "Поглощение стихий",
    "kind": "reaction",
    "is_spell": True,
    "spell_level": 1,
    "school": "Ограждение",
    "target": "self",
    "effect": "absorb_elements_reaction",
    "resource_key": "spell_slots_1",
    "casting_time_text": "Реакция",
    "casting_time_kind": "reaction",
    "reaction_trigger": "take_elemental_damage",
    "components": ["s"],
    "duration": "1 round",
    "damage_types": ["acid", "cold", "fire", "lightning", "thunder"],
    "bonus_damage_dice": [1, 6],
    "upcast": {"bonus_damage_dice_per_level": [1, 6]},
    "description": "Реакция при получении урона кислотой, холодом, огнём, электричеством или звуком. Даёт сопротивление этому типу до начала следующего хода и добавляет 1к6 этого типа к первому попаданию рукопашной атакой на следующем ходу.",
    "button": "ПОГЛОЩЕНИЕ СТИХИЙ",
}

CLASS_SPELLS = {
    "druid": ["absorb_elements"],
    "ranger": ["absorb_elements"],
    "sorcerer": ["shield_spell", "absorb_elements"],
    "wizard": ["shield_spell", "absorb_elements"],
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    abilities = load_json(ABILITIES_PATH)
    abilities["shield_spell"] = SHIELD
    abilities["absorb_elements"] = ABSORB_ELEMENTS
    save_json(ABILITIES_PATH, abilities)

    classes = load_json(CLASSES_PATH)
    for class_definition in classes.get("classes", []):
        class_id = str(class_definition.get("id", ""))
        additions = CLASS_SPELLS.get(class_id, [])
        if not additions:
            continue
        profile = class_definition.get("spellcasting")
        if not isinstance(profile, dict):
            continue
        starting_spells = profile.setdefault("starting_spells", [])
        for spell_id in additions:
            if spell_id not in starting_spells:
                starting_spells.append(spell_id)
    save_json(CLASSES_PATH, classes)


if __name__ == "__main__":
    main()
