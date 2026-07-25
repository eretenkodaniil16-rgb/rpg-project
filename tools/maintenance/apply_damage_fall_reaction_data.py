#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ABILITIES_PATH = ROOT / "data/abilities/abilities.json"
CLASSES_PATH = ROOT / "data/classes/classes.json"

HELLISH_REBUKE = {
    "id": "hellish_rebuke",
    "name": "Адское возмездие",
    "kind": "reaction",
    "is_spell": True,
    "spell_level": 1,
    "school": "Воплощение",
    "target": "creature_that_damaged_self",
    "effect": "hellish_rebuke_reaction",
    "resource_key": "pact_slots_1",
    "ability": "charisma",
    "save_ability": "dexterity",
    "damage_dice": [2, 10],
    "damage_type": "fire",
    "range_ft": 60,
    "casting_time_text": "Реакция",
    "casting_time_kind": "reaction",
    "reaction_trigger": "creature_damage_received",
    "components": ["v", "s"],
    "upcast": {"damage_dice_per_level": [1, 10]},
    "description": "Реакция после получения урона от видимого существа в пределах 60 футов. Цель совершает спасбросок Ловкости, получая 2к10 огненного урона при провале или половину при успехе.",
    "button": "АДСКОЕ ВОЗМЕЗДИЕ",
}

SLOW_FALL = {
    "id": "slow_fall",
    "name": "Медленное падение",
    "kind": "reaction",
    "class_id": "monk",
    "required_level": 4,
    "target": "self",
    "effect": "slow_fall_reaction",
    "reaction_trigger": "fall_damage_pending",
    "description": "Монах 4 уровня или выше может реакцией уменьшить урон от падения на величину, равную пятикратному уровню монаха.",
    "button": "МЕДЛЕННОЕ ПАДЕНИЕ",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    abilities = load_json(ABILITIES_PATH)
    abilities["hellish_rebuke"] = HELLISH_REBUKE
    abilities["slow_fall"] = SLOW_FALL
    save_json(ABILITIES_PATH, abilities)

    classes = load_json(CLASSES_PATH)
    for definition in classes.get("classes", []):
        class_id = str(definition.get("id", ""))
        if class_id == "warlock":
            profile = definition.get("spellcasting")
            if isinstance(profile, dict):
                starting_spells = profile.setdefault("starting_spells", [])
                if "hellish_rebuke" not in starting_spells:
                    starting_spells.append("hellish_rebuke")
        elif class_id == "monk":
            level_features = definition.setdefault("level_features", {})
            level_four = level_features.setdefault("4", [])
            if "slow_fall" not in level_four:
                level_four.append("slow_fall")
    save_json(CLASSES_PATH, classes)


if __name__ == "__main__":
    main()
