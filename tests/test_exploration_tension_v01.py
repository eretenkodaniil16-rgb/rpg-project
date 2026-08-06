from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "assets/audio/music/source/exploration_tension_v01_score.json"
PROVENANCE = ROOT / "assets/audio/music/source/exploration_tension_v01_provenance.json"
MANIFEST = ROOT / "assets/audio/music/source/exploration_tension_v01_master_manifest.json"
OGG = ROOT / "assets/audio/music/exports/exploration_tension_v01_master.ogg"
CATALOG = ROOT / "data/audio/music_catalog.json"
RESOLVER = ROOT / "scripts/audio/music_threat_state_resolver.gd"
PROJECT = ROOT / "project.godot"
DOC = ROOT / "docs/EXPLORATION_TENSION_V01.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    score = json.loads(SCORE.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    require(score["composition_id"] == "exploration_tension_v01", "wrong composition_id")
    require(score["arrangement_revision"] == 2, "approved arrangement revision is missing")
    require(score["tempo_bpm"] == 75, "tempo must be 75 BPM")
    require(score["time_signature"] == [6, 8], "time signature must be 6/8")
    require(score["bars"] == 34 and len(score["harmony"]) == 34, "score must contain 34 bars")
    require(math.isclose(34 * 3 * 60 / 75, 81.6), "score duration contract changed")
    require(score["external_samples_used"] is False, "external samples are forbidden")
    require(len(score["danger_density_changes"]) >= 4, "danger-density revision is undocumented")
    require(provenance["original_for_project"] is True, "provenance must mark original asset")
    require(provenance["external_recordings_used"] is False, "external recordings are forbidden")
    require(provenance["arrangement_revision"] == 2, "provenance revision is missing")

    require(OGG.read_bytes().startswith(b"OggS"), "game master is not Ogg Vorbis")
    require(OGG.stat().st_size > 700_000, "game master is unexpectedly small")
    ogg_sha = hashlib.sha256(OGG.read_bytes()).hexdigest()
    require(ogg_sha == manifest["ogg_sha256"], "Ogg SHA-256 does not match manifest")
    require(manifest["duration_seconds"] == 81.6, "manifest duration must be 81.6 seconds")
    require(manifest["renderer"] == "procedural_tension_renderer_v02", "approved renderer revision is missing")
    require(manifest["arrangement_revision"] == 2, "approved manifest revision is missing")
    require(manifest["danger_density_pass"] == "approved_2026-08-06", "approval marker is missing")
    require(manifest["numpy_version"] == "2.3.5", "renderer NumPy version must be pinned")
    require(manifest["pcm_signature_shift_bits"] == 8, "PCM signature shift contract changed")
    require(len(manifest["pcm_signature_sha256"]) == 64, "PCM signature SHA-256 is missing")
    require(manifest["sample_rate"] == 48_000 and manifest["channels"] == 2, "master must be 48 kHz stereo")
    require(-2.2 <= manifest["peak_dbfs"] <= -1.4, "peak is outside the approved danger-pass range")
    require(-18.0 <= manifest["rms_dbfs"] <= -14.0, "RMS is outside the approved danger-pass range")
    require(manifest["boundary_value_delta"] <= 0.002, "loop value boundary is too large")
    require(manifest["boundary_slope_delta"] <= 0.002, "loop slope boundary is too large")

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(OGG)],
        check=True,
        capture_output=True,
        text=True,
    )
    require(abs(float(probe.stdout.strip()) - 81.6) < 0.08, "encoded Ogg duration is incorrect")

    context = catalog["contexts"]["world_tension"]
    track = catalog["tracks"]["exploration_tension"]
    require(context["track_id"] == "exploration_tension", "world_tension uses wrong track")
    require(context["fade_seconds"] == 1.25, "world_tension fade must be 1.25 seconds")
    require(track["enabled"] is True, "exploration_tension must be enabled")
    require(track["path"] == "res://assets/audio/music/exports/exploration_tension_v01_master.ogg", "catalog path is wrong")
    require(track["loop"] is True and track["volume_db"] == -6.0, "track playback contract changed")
    require(track.get("arrangement_revision") == 2, "catalog arrangement revision is missing")
    require(track.get("danger_profile") == "nearby_threat", "catalog danger profile is missing")

    resolver_text = RESOLVER.read_text(encoding="utf-8")
    for contract in (
        "DEFAULT_RELEASE_DELAY_SECONDS: float = 8.0",
        "func set_threat_source(",
        "func clear_threat_source(",
        "func get_effective_threat_level(",
        "STEALTH_ALERT_REGISTRY_FLAG",
        "set_context_override",
        "clear_context_override",
        "is_turn_based_combat_active",
    ):
        require(contract in resolver_text, f"resolver contract is missing: {contract}")
    require(re.search(r'\"suspicious\"\s*:\s*1', resolver_text) is not None, "suspicious state mapping is missing")
    require(re.search(r'\"searching\"\s*:\s*2', resolver_text) is not None, "searching state mapping is missing")

    project_text = PROJECT.read_text(encoding="utf-8")
    require('MusicThreatStateResolver="*res://scripts/audio/music_threat_state_resolver.gd"' in project_text, "resolver autoload is missing")
    require(DOC.is_file(), "music tension documentation is missing")
    print("Exploration tension v01 revision 2 contracts passed.")


if __name__ == "__main__":
    main()
