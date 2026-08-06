from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "assets/audio/music/source/aftermath_v01_score.json"
PROVENANCE = ROOT / "assets/audio/music/source/aftermath_v01_provenance.json"
MANIFEST = ROOT / "assets/audio/music/source/aftermath_v01_master_manifest.json"
OGG = ROOT / "assets/audio/music/exports/aftermath_v01_master.ogg"
CATALOG = ROOT / "data/audio/music_catalog.json"
PROJECT = ROOT / "project.godot"
RESOLVER = ROOT / "scripts/audio/music_aftermath_resolver.gd"
REGISTRY = ROOT / "scripts/systems/combat_outcome_registry.gd"


def fail(message: str) -> None:
    raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    for path in (SCORE, PROVENANCE, MANIFEST, OGG, CATALOG, PROJECT, RESOLVER, REGISTRY):
        if not path.is_file():
            fail(f"missing aftermath asset: {path.relative_to(ROOT)}")
    score = json.loads(SCORE.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if score.get("composition_id") != "aftermath_v01":
        fail("unexpected composition id")
    if manifest.get("renderer") != "procedural_aftermath_renderer_v01":
        fail("unexpected renderer id")
    if manifest.get("numpy_version") != "2.3.5":
        fail("NumPy version must stay pinned")
    if manifest.get("duration_seconds") != 22.5:
        fail("aftermath duration changed")
    if manifest.get("peak_dbfs") != -2.0 or manifest.get("rms_dbfs") != -16.277:
        fail("aftermath master level changed")
    if manifest.get("final_100ms_peak_dbfs", 0.0) > -60.0:
        fail("aftermath tail is not quiet enough for the return crossfade")
    if manifest.get("external_samples_used") is not False:
        fail("external samples are forbidden")
    if provenance.get("third_party_melodies_used") is not False:
        fail("third-party melodies are forbidden")
    if sha256(OGG) != manifest.get("ogg_sha256"):
        fail("committed Ogg does not match manifest")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,sample_rate,channels:format=duration", "-of", "json", str(OGG)],
        check=True,
        capture_output=True,
        text=True,
    )
    info = json.loads(probe.stdout)
    stream = info["streams"][0]
    if stream.get("codec_name") != "vorbis" or int(stream.get("sample_rate", 0)) != 48000 or int(stream.get("channels", 0)) != 2:
        fail("aftermath Ogg format changed")
    if abs(float(info["format"]["duration"]) - 22.5) > 0.002:
        fail("aftermath Ogg duration changed")
    track = catalog["tracks"]["aftermath"]
    if not track.get("enabled") or track.get("path") != "res://assets/audio/music/exports/aftermath_v01_master.ogg":
        fail("aftermath catalog entry is not enabled")
    if track.get("loop") is not False:
        fail("aftermath track must not loop")
    project_text = PROJECT.read_text(encoding="utf-8")
    for autoload in ("CombatOutcomeRegistry", "MusicAftermathResolver"):
        if f'{autoload}="*res://' not in project_text:
            fail(f"missing autoload: {autoload}")
    resolver_text = RESOLVER.read_text(encoding="utf-8")
    for outcome_id in ("victory", "escape", "defeat", "scripted_end"):
        if outcome_id not in resolver_text:
            fail(f"resolver outcome contract missing: {outcome_id}")
    print("Aftermath v01 static contracts passed.")


if __name__ == "__main__":
    main()
