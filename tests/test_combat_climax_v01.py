from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "assets/audio/music/source/combat_climax_v01_score.json"
PROVENANCE = ROOT / "assets/audio/music/source/combat_climax_v01_provenance.json"
MANIFEST = ROOT / "assets/audio/music/source/combat_climax_v01_master_manifest.json"
OGG = ROOT / "assets/audio/music/exports/combat_climax_v01_master.ogg"
CATALOG = ROOT / "data/audio/music_catalog.json"
PROFILE_CATALOG = ROOT / "data/audio/combat_music_profiles.json"
PROJECT = ROOT / "project.godot"
REGISTRY = ROOT / "scripts/systems/combat_music_profile_registry.gd"
RESOLVER = ROOT / "scripts/audio/music_combat_climax_resolver.gd"
TRACKER = ROOT / "scripts/audio/music_combat_climax_transition_tracker.gd"
GAME_RUNTIME = ROOT / "scripts/game/game_encounters_runtime.gd"
DOC = ROOT / "docs/COMBAT_CLIMAX_V01.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    score = json.loads(SCORE.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    profiles = json.loads(PROFILE_CATALOG.read_text(encoding="utf-8"))

    require(score["composition_id"] == "combat_climax_v01", "wrong composition_id")
    require(score["tempo_bpm"] == 96, "climax must share 96 BPM with combat standard")
    require(score["time_signature"] == [6, 8], "climax must remain in 6/8")
    require(score["bars"] == 40 and len(score["harmony"]) == 40, "score must contain 40 bars")
    require(math.isclose(score["duration_seconds"], 75.0), "duration contract changed")
    require(score["external_samples_used"] is False, "external samples are forbidden")
    require("health" not in json.dumps(score, ensure_ascii=False).lower(), "score must not encode HP triggers")
    require(len(score["trigger_contract"]) == 4, "explicit climax trigger contract is incomplete")

    require(provenance["original_for_project"] is True, "provenance must mark original asset")
    require(provenance["external_recordings_used"] is False, "external recordings are forbidden")
    require(provenance["third_party_melodies_used"] is False, "third-party melodies are forbidden")

    require(OGG.read_bytes().startswith(b"OggS"), "game master is not Ogg Vorbis")
    require(OGG.stat().st_size > 800_000, "game master is unexpectedly small")
    ogg_sha = hashlib.sha256(OGG.read_bytes()).hexdigest()
    require(ogg_sha == manifest["ogg_sha256"], "Ogg SHA-256 does not match manifest")
    require(manifest["renderer"] == "procedural_combat_climax_renderer_v01", "wrong renderer")
    require(manifest["arrangement_revision"] == 1, "wrong arrangement revision")
    require(manifest["numpy_version"] == "2.3.5", "NumPy must be pinned")
    require(manifest["duration_seconds"] == 75.0, "manifest duration must be 75 seconds")
    require(manifest["tempo_bpm"] == 96 and manifest["time_signature"] == [6, 8], "tempo/meter mismatch")
    require(manifest["sample_rate"] == 48_000 and manifest["channels"] == 2, "master must be 48 kHz stereo")
    require(-1.4 <= manifest["peak_dbfs"] <= -0.6, "peak is outside climax master range")
    require(-15.2 <= manifest["rms_dbfs"] <= -12.5, "RMS is outside climax master range")
    require(manifest["boundary_value_delta"] <= 0.002, "loop value boundary is too large")
    require(manifest["boundary_slope_delta"] <= 0.002, "loop slope boundary is too large")
    require(len(manifest["pcm_signature_sha256"]) == 64, "PCM fingerprint is missing")

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(OGG)],
        check=True,
        capture_output=True,
        text=True,
    )
    require(abs(float(probe.stdout.strip()) - 75.0) < 0.08, "encoded Ogg duration is incorrect")

    context = catalog["contexts"]["combat_climax"]
    track = catalog["tracks"]["combat_climax"]
    require(context["track_id"] == "combat_climax", "combat_climax context uses wrong track")
    require(context["fade_seconds"] == 0.75, "climax transition must use 0.75 seconds")
    require(track["enabled"] is True, "combat_climax must be enabled")
    require(track["path"] == "res://assets/audio/music/exports/combat_climax_v01_master.ogg", "catalog path is wrong")
    require(track["loop"] is True and track["volume_db"] == -5.5, "playback contract changed")
    require(track["tempo_bpm"] == 96, "catalog tempo mismatch")
    require(track["trigger_contract"] == "explicit_phase_event_only", "HP-independent trigger marker is missing")

    require(profiles["default_profile"] == "standard", "default combat profile must be standard")
    require(profiles["valid_profiles"] == ["standard", "climax", "scripted"], "stable profile IDs changed")
    for encounter_id in ("training_construct", "vault_guard_post_01", "vault_inner_watch_01"):
        definition = profiles["encounters"][encounter_id]
        require(definition["initial_profile"] == "standard", f"{encounter_id} must remain standard")
        require("climax" in definition["allowed_profiles"], f"{encounter_id} lacks explicit climax capability")

    project_text = PROJECT.read_text(encoding="utf-8")
    require('CombatMusicProfileRegistry="*res://scripts/systems/combat_music_profile_registry.gd"' in project_text, "profile registry autoload missing")
    require('MusicCombatClimaxResolver="*res://scripts/audio/music_combat_climax_resolver.gd"' in project_text, "climax resolver autoload missing")

    registry_text = REGISTRY.read_text(encoding="utf-8")
    resolver_text = RESOLVER.read_text(encoding="utf-8")
    tracker_text = TRACKER.read_text(encoding="utf-8")
    runtime_text = GAME_RUNTIME.read_text(encoding="utf-8")
    for contract in (
        "PROFILE_STANDARD",
        "PROFILE_CLIMAX",
        "PROFILE_SCRIPTED",
        "func request_climax(",
        "func set_profile(",
        "STATE_FLAG",
    ):
        require(contract in registry_text, f"registry contract missing: {contract}")
    for contract in (
        "CLIMAX_CONTEXT_ID",
        "set_context_override",
        "MusicAftermathResolver",
        "get_active_combat_encounter_id",
        "PROFILE_SCRIPTED",
    ):
        require(contract in resolver_text, f"resolver contract missing: {contract}")
    require("current_health" not in resolver_text and "health_ratio" not in resolver_text, "resolver must not use HP thresholds")
    require("func request_combat_music_climax(" in runtime_text, "scene climax API missing")
    require("func set_combat_music_profile(" in runtime_text, "scene profile API missing")
    require("func sample(" in tracker_text and "func mark_applied(" in tracker_text, "transition tracker contract missing")
    require(DOC.is_file(), "combat climax documentation missing")
    print("Combat climax v01 contracts passed.")


if __name__ == "__main__":
    main()
