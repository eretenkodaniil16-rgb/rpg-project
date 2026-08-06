from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "assets/audio/music/source/combat_start_v01_score.json"
PROVENANCE = ROOT / "assets/audio/music/source/combat_start_v01_provenance.json"
MANIFEST = ROOT / "assets/audio/music/source/combat_start_v01_master_manifest.json"
OGG = ROOT / "assets/audio/music/exports/combat_start_v01_master.ogg"
CATALOG = ROOT / "data/audio/music_catalog.json"
PROJECT = ROOT / "project.godot"
TRACKER = ROOT / "scripts/audio/music_combat_transition_tracker.gd"
RESOLVER = ROOT / "scripts/audio/music_combat_start_resolver.gd"
DOC = ROOT / "docs/COMBAT_START_V01.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    score = json.loads(SCORE.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    require(score["composition_id"] == "combat_start_v01", "wrong composition_id")
    require(score["arrangement_revision"] == 1, "wrong arrangement revision")
    require(score["tempo_bpm"] == 96, "stinger must match combat tempo")
    require(score["time_signature"] == [6, 8], "time signature must be 6/8")
    require(math.isclose(score["duration_seconds"], 3.125), "score duration changed")
    require(score["external_samples_used"] is False, "external samples are forbidden")

    require(provenance["original_for_project"] is True, "asset must be original")
    require(provenance["external_recordings_used"] is False, "external recordings are forbidden")
    require(provenance["third_party_melodies_used"] is False, "third-party melodies are forbidden")

    require(OGG.read_bytes().startswith(b"OggS"), "game master is not Ogg Vorbis")
    require(35_000 < OGG.stat().st_size < 250_000, "stinger Ogg size is unexpected")
    require(hashlib.sha256(OGG.read_bytes()).hexdigest() == manifest["ogg_sha256"], "Ogg SHA mismatch")
    require(manifest["renderer"] == "procedural_combat_start_renderer_v01", "wrong renderer")
    require(manifest["render_id"] == "combat_start_v01_master_candidate_01", "wrong render ID")
    require(manifest["numpy_version"] == "2.3.5", "NumPy version must be pinned")
    require(manifest["sample_rate"] == 48_000 and manifest["channels"] == 2, "master must be 48 kHz stereo")
    require(abs(manifest["duration_seconds"] - 3.125) < 0.00001, "manifest duration changed")
    require(manifest["midi_note_count"] >= 15, "MIDI event coverage is too small")
    require(-1.8 <= manifest["peak_dbfs"] <= -1.2, "peak is outside stinger range")
    require(-20.0 <= manifest["rms_dbfs"] <= -12.0, "RMS is outside stinger range")
    require(manifest["final_100ms_peak_dbfs"] <= -45.0, "handoff tail does not clear the spectrum")
    require(len(manifest["pcm_signature_sha256"]) == 64, "PCM fingerprint is missing")

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(OGG)],
        check=True,
        capture_output=True,
        text=True,
    )
    require(abs(float(probe.stdout.strip()) - 3.125) < 0.08, "encoded Ogg duration is incorrect")

    stinger = catalog["stingers"]["combat_start"]
    require(stinger["enabled"] is True, "combat_start must be enabled")
    require(stinger["path"] == "res://assets/audio/music/exports/combat_start_v01_master.ogg", "catalog path is wrong")
    require(stinger["bus"] == "Music" and stinger["volume_db"] == -4.5, "playback mix contract changed")
    require(stinger["composition_id"] == "combat_start_v01", "catalog composition ID is wrong")
    require(stinger["trigger_profile"] == "false_to_true_combat_transition", "trigger profile is missing")
    require(stinger["skip_on_combat_scene_baseline"] is True, "load-in-combat skip contract is missing")

    project_text = PROJECT.read_text(encoding="utf-8")
    require('MusicCombatStartResolver="*res://scripts/audio/music_combat_start_resolver.gd"' in project_text, "autoload is missing")
    tracker_text = TRACKER.read_text(encoding="utf-8")
    require("_required_inactive_samples" in tracker_text and "_pending" in tracker_text, "transition hysteresis is missing")
    resolver_text = RESOLVER.read_text(encoding="utf-8")
    require('COMBAT_START_STINGER_ID: StringName = &"combat_start"' in resolver_text, "stable stinger ID is missing")
    require('music_manager.call("play_context", COMBAT_CONTEXT_ID' in resolver_text, "combat loop handoff is missing")
    require('music_manager.call("play_stinger", COMBAT_START_STINGER_ID)' in resolver_text, "stinger playback is missing")
    require(DOC.is_file(), "combat start documentation is missing")
    print("Combat start v01 contracts passed.")


if __name__ == "__main__":
    main()
