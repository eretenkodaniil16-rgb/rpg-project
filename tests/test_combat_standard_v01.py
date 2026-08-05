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
    require(score["arrangement_revision"] == 1, "wrong arrangement revision")
    require(score["tempo_bpm"] == 84, "tempo must be 84 BPM")
    require(score["time_signature"] == [6, 8], "time signature must be 6/8")
    require(score["bars"] == 36 and len(score["harmony"]) == 36, "score must contain 36 bars")
    require(math.isclose(36 * 3 * 60 / 84, 77.14285714285714), "duration formula changed")
    require(score["external_samples_used"] is False, "external samples are forbidden")
    require(len(score["sections"]) == 6, "combat structure is incomplete")

    require(provenance["original_for_project"] is True, "asset must be original")
    require(provenance["external_recordings_used"] is False, "external recordings are forbidden")
    require(provenance["imported_midi_used"] is False, "imported MIDI is forbidden")

    require(OGG.read_bytes().startswith(b"OggS"), "game master is not Ogg Vorbis")
    require(OGG.stat().st_size > 800_000, "game master is unexpectedly small")
    require(hashlib.sha256(OGG.read_bytes()).hexdigest() == manifest["ogg_sha256"], "Ogg SHA-256 mismatch")
    require(manifest["renderer"] == "procedural_combat_renderer_v01", "wrong renderer")
    require(manifest["render_id"] == "combat_standard_v01_master_candidate_01", "wrong render ID")
    require(manifest["numpy_version"] == "2.3.5", "NumPy version must be pinned")
    require(manifest["sample_rate"] == 48_000 and manifest["channels"] == 2, "master must be 48 kHz stereo")
    require(abs(manifest["duration_seconds"] - 77.142854) < 0.00001, "manifest duration changed")
    require(manifest["midi_note_count"] >= 300, "MIDI event coverage is unexpectedly small")
    require(-1.7 <= manifest["peak_dbfs"] <= -1.1, "peak is outside combat range")
    require(-17.0 <= manifest["rms_dbfs"] <= -13.5, "RMS is outside combat range")
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
    require(track["combat_profile"] == "standard_turn_based", "combat profile is missing")

    manager_text = MANAGER.read_text(encoding="utf-8")
    require('return &"combat_standard"' in manager_text, "automatic combat context mapping is missing")
    require('is_turn_based_combat_active' in manager_text, "combat state probe is missing")
    resolver_text = RESOLVER.read_text(encoding="utf-8")
    require('is_turn_based_combat_active' in resolver_text, "threat resolver combat release contract is missing")
    require(DOC.is_file(), "combat music documentation is missing")
    print("Combat standard v01 contracts passed.")


if __name__ == "__main__":
    main()
