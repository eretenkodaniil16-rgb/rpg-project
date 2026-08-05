from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "assets/audio/music/source/combat_standard_v01_score.json"
PROVENANCE = ROOT / "assets/audio/music/source/combat_standard_v01_provenance.json"
MANIFEST = ROOT / "assets/audio/music/source/combat_standard_v01_master_manifest.json"
OGG = ROOT / "assets/audio/music/exports/combat_standard_v01_master.ogg"
CATALOG = ROOT / "data/audio/music_catalog.json"
MANAGER = ROOT / "scripts/audio/music_manager.gd"
RESOLVER = ROOT / "scripts/audio/music_threat_state_resolver.gd"
DOC = ROOT / "docs/COMBAT_STANDARD_V01.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    score = json.loads(SCORE.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    require(score["composition_id"] == "combat_standard_v01", "wrong composition_id")
    require(score["arrangement_revision"] == 2, "approved arrangement revision is missing")
    require(score["tempo_bpm"] == 96, "tempo must be 96 BPM")
    require(score["time_signature"] == [6, 8], "time signature must be 6/8")
    require(score["bars"] == 40 and len(score["harmony"]) == 40, "score must contain 40 bars")
    require(math.isclose(40 * 3 * 60 / 96, 75.0), "duration formula changed")
    require(score["external_samples_used"] is False, "external samples are forbidden")
    require(len(score["sections"]) == 6, "combat structure is incomplete")
    require(len(score["sharpness_pass"]) >= 6, "sharpness pass is undocumented")

    require(provenance["original_for_project"] is True, "asset must be original")
    require(provenance["arrangement_revision"] == 2, "provenance revision is missing")
    require(provenance["renderer"] == "procedural_combat_renderer_v02", "provenance renderer is wrong")
    require(provenance["external_recordings_used"] is False, "external recordings are forbidden")
    require(provenance["imported_midi_used"] is False, "imported MIDI is forbidden")
    require(provenance["third_party_melodies_used"] is False, "third-party melodies are forbidden")

    require(OGG.read_bytes().startswith(b"OggS"), "game master is not Ogg Vorbis")
    require(OGG.stat().st_size > 800_000, "game master is unexpectedly small")
    require(hashlib.sha256(OGG.read_bytes()).hexdigest() == manifest["ogg_sha256"], "Ogg SHA-256 mismatch")
    require(manifest["renderer"] == "procedural_combat_renderer_v02", "wrong renderer")
    require(manifest["render_id"] == "combat_standard_v01_master_candidate_02", "wrong render ID")
    require(manifest["arrangement_revision"] == 2, "manifest revision is missing")
    require(manifest["sharpness_pass"] == "approved_candidate_2026-08-06", "approval marker is missing")
    require(manifest["numpy_version"] == "2.3.5", "NumPy version must be pinned")
    require(manifest["sample_rate"] == 48_000 and manifest["channels"] == 2, "master must be 48 kHz stereo")
    require(abs(manifest["duration_seconds"] - 75.0) < 0.00001, "manifest duration changed")
    require(manifest["midi_note_count"] >= 400, "MIDI event coverage is unexpectedly small")
    require(-1.5 <= manifest["peak_dbfs"] <= -0.9, "peak is outside approved sharp combat range")
    require(-18.0 <= manifest["rms_dbfs"] <= -14.0, "RMS is outside approved sharp combat range")
    require(manifest["boundary_value_delta"] <= 0.0001, "loop value boundary is too large")
    require(manifest["boundary_slope_delta"] <= 0.0001, "loop slope boundary is too large")
    require(manifest["pcm_signature_shift_bits"] == 8, "PCM fingerprint contract changed")
    require(len(manifest["pcm_signature_sha256"]) == 64, "PCM fingerprint is missing")

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(OGG)],
        check=True,
        capture_output=True,
        text=True,
    )
    require(abs(float(probe.stdout.strip()) - manifest["duration_seconds"]) < 0.08, "encoded Ogg duration is incorrect")

    context = catalog["contexts"]["combat_standard"]
    track = catalog["tracks"]["combat_standard"]
    require(context["track_id"] == "combat_standard", "combat context uses wrong track")
    require(context["fade_seconds"] == 0.75, "combat crossfade must be 0.75 seconds")
    require(track["enabled"] is True, "combat track must be enabled")
    require(track["path"] == "res://assets/audio/music/exports/combat_standard_v01_master.ogg", "catalog path is wrong")
    require(track["loop"] is True and track["volume_db"] == -4.5, "playback contract changed")
    require(track["composition_id"] == "combat_standard_v01", "catalog composition ID is wrong")
    require(track["render_id"] == "combat_standard_v01_master_candidate_02", "catalog render ID is wrong")
    require(track["arrangement_revision"] == 2, "catalog revision is missing")
    require(track["combat_profile"] == "sharp_standard_turn_based", "sharp combat profile is missing")
    require(track["tempo_bpm"] == 96, "catalog tempo is missing")

    manager_text = MANAGER.read_text(encoding="utf-8")
    require('return &"combat_standard"' in manager_text, "automatic combat context mapping is missing")
    require('is_turn_based_combat_active' in manager_text, "combat state probe is missing")
    resolver_text = RESOLVER.read_text(encoding="utf-8")
    require('is_turn_based_combat_active' in resolver_text, "threat resolver combat release contract is missing")
    require(DOC.is_file(), "combat music documentation is missing")
    print("Combat standard v01 revision 2 contracts passed.")


if __name__ == "__main__":
    main()
