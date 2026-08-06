from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    data = json.loads((ROOT / "data/audio/encounter_music_phase_events.json").read_text(encoding="utf-8"))
    require(data["schema_version"] == 1, "Unexpected phase data schema.")
    phases = data["encounters"]["vault_inner_watch_01"]["phases"]
    require(len(phases) == 1, "Inner watch must expose exactly one initial music phase.")
    phase = phases[0]
    require(phase["phase_id"] == "rune_overload", "Stable rune overload phase id missing.")
    require(phase["event_id"] == "enemy_spell_committed", "Phase must use the committed-spell event.")
    require(phase["source_actor_id"] == "training_mage", "Wrong phase source actor.")
    require(phase["minimum_round"] == 2, "Opening round must stay standard.")
    require(phase["trigger_id"] == "dangerous_ability", "Wrong climax trigger contract.")

    mage = (ROOT / "scripts/game/combat_ai_training_mage.gd").read_text(encoding="utf-8")
    require("signal combat_spell_committed" in mage, "Mage committed-spell signal missing.")
    decrement = mage.index("_remaining_level_one_slots -= 1")
    emission = mage.index("combat_spell_committed.emit")
    require(emission > decrement, "Signal must be emitted only after the slot is consumed.")

    runtime = (ROOT / "scripts/game/game_vault_inner_watch_climax_runtime.gd").read_text(encoding="utf-8")
    require("extends \"res://scripts/game/game_party_medicine_recovery_runtime.gd\"" in runtime, "Runtime must extend the current integration head.")
    require("get_active_combat_encounter_id()" in runtime, "Runtime is not scoped to the active encounter.")
    require("request_combat_music_climax" in runtime, "Runtime does not request the existing climax profile.")
    require("GameState.save_game()" in runtime, "Triggered phase must be persisted.")

    scene = (ROOT / "scenes/game/game.tscn").read_text(encoding="utf-8")
    require("game_vault_inner_watch_climax_runtime.gd" in scene, "Game scene does not use the phase adapter.")
    require("game_party_medicine_recovery_runtime.gd" not in scene, "Old root runtime remains wired directly.")

    print("Vault inner watch music phase static contracts passed.")


if __name__ == "__main__":
    main()
