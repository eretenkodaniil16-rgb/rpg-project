from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "audio" / "music_catalog.json"
MANAGER_PATH = ROOT / "scripts" / "audio" / "music_manager.gd"
PROJECT_PATH = ROOT / "project.godot"
DOC_PATH = ROOT / "docs" / "AUDIO_SYSTEM.md"
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
ALLOWED_BUSES = {"Music", "Ambience", "SFX", "UI", "Voice"}


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if catalog.get("schema_version") != 1:
        fail("music catalog schema_version must be 1")

    contexts = catalog.get("contexts")
    tracks = catalog.get("tracks")
    stingers = catalog.get("stingers")
    if not isinstance(contexts, dict) or not isinstance(tracks, dict) or not isinstance(stingers, dict):
        fail("contexts, tracks and stingers must be JSON objects")

    for section_name, section in (("context", contexts), ("track", tracks), ("stinger", stingers)):
        for audio_id in section:
            if not ID_PATTERN.fullmatch(audio_id):
                fail(f"invalid stable {section_name} id: {audio_id}")

    for context_id, context in contexts.items():
        track_id = context.get("track_id", "")
        if track_id and track_id not in tracks:
            fail(f"context {context_id} references missing track {track_id}")
        fade_seconds = context.get("fade_seconds", 0.0)
        if not isinstance(fade_seconds, (int, float)) or fade_seconds < 0:
            fail(f"context {context_id} has invalid fade_seconds")

    for section_name, section in (("track", tracks), ("stinger", stingers)):
        for audio_id, definition in section.items():
            path = definition.get("path", "")
            enabled = definition.get("enabled", False)
            bus = definition.get("bus", "")
            volume_db = definition.get("volume_db", 0.0)
            if bus not in ALLOWED_BUSES:
                fail(f"{section_name} {audio_id} uses unknown bus {bus}")
            if not isinstance(volume_db, (int, float)) or not math.isfinite(volume_db):
                fail(f"{section_name} {audio_id} has invalid volume_db")
            if path:
                if not path.startswith("res://assets/audio/"):
                    fail(f"{section_name} {audio_id} points outside assets/audio")
                disk_path = ROOT / path.removeprefix("res://")
                if enabled and not disk_path.is_file():
                    fail(f"enabled {section_name} {audio_id} is missing: {path}")
            elif enabled:
                fail(f"{section_name} {audio_id} is enabled without a resource path")

    project_text = PROJECT_PATH.read_text(encoding="utf-8")
    if 'MusicManager="*res://scripts/audio/music_manager.gd"' not in project_text:
        fail("MusicManager autoload is not registered")

    manager_text = MANAGER_PATH.read_text(encoding="utf-8")
    required_contracts = (
        "func play_context(",
        "func play_music(",
        "func play_stinger(",
        "func set_context_override(",
        "func set_bus_volume_linear(",
        "AudioStreamPlayer.new()",
        "AutomaticContextTimer",
    )
    for contract in required_contracts:
        if contract not in manager_text:
            fail(f"music manager contract is missing: {contract}")

    if not DOC_PATH.is_file():
        fail("audio system documentation is missing")

    print("Music system static contracts passed.")


if __name__ == "__main__":
    main()
