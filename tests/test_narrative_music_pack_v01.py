from __future__ import annotations

import hashlib
import json
import math
import py_compile
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/audio/generate_narrative_music_pack_v01.py"
CATALOG = ROOT / "data/audio/music_catalog.json"
DOC = ROOT / "docs/NARRATIVE_MUSIC_PACK_V01.md"

TRACKS = {
    "mad_wizard_theme": {
        "composition_id": "mad_wizard_theme_v01",
        "tempo_bpm": 70,
        "time_signature": [7, 8],
        "bars": 32,
        "loop": True,
        "volume_db": -7.5,
        "context": "mad_wizard_theme",
        "duration": 96.0,
    },
    "tavern_commonroom": {
        "composition_id": "tavern_commonroom_v01",
        "tempo_bpm": 112,
        "time_signature": [6, 8],
        "bars": 32,
        "loop": True,
        "volume_db": -8.0,
        "context": "tavern_commonroom",
        "duration": 51.428562,
    },
    "elevator_descent_floor01": {
        "composition_id": "elevator_descent_floor01_v01",
        "tempo_bpm": 58,
        "time_signature": [4, 4],
        "bars": 16,
        "loop": False,
        "volume_db": -6.5,
        "context": "elevator_descent_floor01",
        "duration": 66.206896,
    },
    "act01_plan_broken": {
        "composition_id": "act01_plan_broken_v01",
        "tempo_bpm": 68,
        "time_signature": [4, 4],
        "bars": 24,
        "loop": False,
        "volume_db": -5.5,
        "context": "act01_plan_broken",
        "duration": 84.705875,
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    py_compile.compile(str(GENERATOR), doraise=True)
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    require(DOC.is_file(), "narrative music documentation missing")
    require(
        catalog["asset_status"] == "main_theme_exploration_combat_and_narrative_pack_v01_integrated",
        "music catalog status was not advanced",
    )

    for track_id, expected in TRACKS.items():
        cid = expected["composition_id"]
        score_path = ROOT / f"assets/audio/music/source/{cid}_score.json"
        provenance_path = ROOT / f"assets/audio/music/source/{cid}_provenance.json"
        manifest_path = ROOT / f"assets/audio/music/source/{cid}_master_manifest.json"
        ogg_path = ROOT / f"assets/audio/music/exports/{cid}_master.ogg"

        score = json.loads(score_path.read_text(encoding="utf-8"))
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        require(score["composition_id"] == cid, f"{cid}: wrong composition_id")
        require(score["tempo_bpm"] == expected["tempo_bpm"], f"{cid}: tempo mismatch")
        require(score["time_signature"] == expected["time_signature"], f"{cid}: meter mismatch")
        require(score["bars"] == expected["bars"], f"{cid}: bar count mismatch")
        require(score["loop"] is expected["loop"], f"{cid}: loop contract mismatch")
        require(score["external_samples_used"] is False, f"{cid}: external samples forbidden")
        require(score["third_party_melodies_used"] is False, f"{cid}: third-party melodies forbidden")
        require(len(score.get("sections", [])) == 4, f"{cid}: four-section dramatic plan required")

        require(provenance["original_for_project"] is True, f"{cid}: original provenance missing")
        require(provenance["external_recordings_used"] is False, f"{cid}: external recordings forbidden")
        require(provenance["external_samples_used"] is False, f"{cid}: external samples forbidden")
        require(provenance["third_party_melodies_used"] is False, f"{cid}: third-party melodies forbidden")

        require(ogg_path.read_bytes().startswith(b"OggS"), f"{cid}: game master is not Ogg Vorbis")
        require(ogg_path.stat().st_size > 650_000, f"{cid}: game master unexpectedly small")
        require(hashlib.sha256(ogg_path.read_bytes()).hexdigest() == manifest["ogg_sha256"], f"{cid}: Ogg hash mismatch")
        require(hashlib.sha256(score_path.read_bytes()).hexdigest() == manifest["score_sha256"], f"{cid}: score hash mismatch")
        require(manifest["renderer"] == "procedural_narrative_music_renderer_v01", f"{cid}: renderer mismatch")
        require(manifest["arrangement_revision"] == 1, f"{cid}: wrong arrangement revision")
        require(manifest["numpy_version"] == "2.3.5", f"{cid}: NumPy must remain pinned")
        require(manifest["sample_rate"] == 48_000 and manifest["channels"] == 2, f"{cid}: master format mismatch")
        require(manifest["loop"] is expected["loop"], f"{cid}: manifest loop mismatch")
        require(abs(manifest["duration_seconds"] - expected["duration"]) < 0.01, f"{cid}: duration changed")
        require(-1.6 <= manifest["peak_dbfs"] <= -0.7, f"{cid}: peak outside master range")
        require(-17.5 <= manifest["rms_dbfs"] <= -12.0, f"{cid}: RMS outside expected range")
        require(len(manifest["pcm_signature_sha256"]) == 64, f"{cid}: PCM fingerprint missing")
        if expected["loop"]:
            require(manifest["boundary_value_delta"] <= 0.00001, f"{cid}: loop value seam too large")
            require(manifest["boundary_slope_delta"] <= 0.00001, f"{cid}: loop slope seam too large")

        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(ogg_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        require(abs(float(probe.stdout.strip()) - expected["duration"]) < 0.08, f"{cid}: encoded duration mismatch")

        context = catalog["contexts"][expected["context"]]
        track = catalog["tracks"][track_id]
        require(context["track_id"] == track_id, f"{cid}: context points to wrong track")
        require(context["activation"] == "explicit_context_override", f"{cid}: automatic activation is forbidden at this stage")
        require(track["enabled"] is True, f"{cid}: track must be enabled")
        require(track["loop"] is expected["loop"], f"{cid}: catalog loop mismatch")
        require(track["volume_db"] == expected["volume_db"], f"{cid}: catalog mix level changed")
        require(track["path"] == f"res://assets/audio/music/exports/{cid}_master.ogg", f"{cid}: catalog path mismatch")
        require(track["render_status"] == "master_candidate", f"{cid}: premature final status")

    wizard = json.loads((ROOT / "assets/audio/music/source/mad_wizard_theme_v01_provenance.json").read_text(encoding="utf-8"))
    note = wizard["creative_reference_note"].lower()
    require("не транскрибировались" in note and "не копировались" in note, "reference handling must explicitly reject copying")

    manager_text = (ROOT / "scripts/audio/music_manager.gd").read_text(encoding="utf-8")
    require("func set_context_override(" in manager_text, "MusicManager explicit override API missing")
    require("func clear_context_override(" in manager_text, "MusicManager clear override API missing")
    for context_id in TRACKS:
        # New contexts must not be hardwired into the automatic scene resolver yet.
        automatic = manager_text.split("func _resolve_automatic_context()", 1)[1]
        require(f'&"{context_id}"' not in automatic, f"{context_id}: must not be auto-selected before its scene exists")

    print("Narrative music pack v01 static contracts passed.")


if __name__ == "__main__":
    main()
