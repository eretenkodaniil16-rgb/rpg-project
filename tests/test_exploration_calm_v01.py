from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "assets/audio/music/source/exploration_calm_v01_score.json"
PROVENANCE = ROOT / "assets/audio/music/source/exploration_calm_v01_provenance.json"
MANIFEST = ROOT / "assets/audio/music/source/exploration_calm_v01_master_manifest.json"
MASTER = ROOT / "assets/audio/music/exports/exploration_calm_v01_master.ogg"
GENERATOR = ROOT / "tools/audio/generate_exploration_calm_v01.py"
CATALOG = ROOT / "data/audio/music_catalog.json"


def main() -> None:
    score = json.loads(SCORE.read_text(encoding="utf-8"))
    assert score["schema_version"] == 1
    assert score["composition_id"] == "exploration_calm_v01"
    assert score["status"] == "review_candidate"
    assert score["original_composition"] is True
    assert score["related_leitmotif"] == "main_theme_v01"
    assert score["tempo_bpm"] == 72
    assert score["time_signature"] == [6, 8]
    assert score["bars"] == 36
    assert score["sample_rate"] == 48_000
    motif = score["motif_variation"]
    assert motif["source_notes"] == ["D4", "A3", "C4", "Eb4", "D4"]
    assert motif["exploration_notes"] == ["D4", "A3", "C4", "E4", "D4"]
    instrumentation = set(score["instrumentation"])
    assert "wordless_low_choir" not in instrumentation
    assert "frame_drum" not in instrumentation

    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    assert provenance["external_audio_samples_embedded"] is False
    assert provenance["external_midi_or_score_imported"] is False
    assert provenance["lyrics_or_voice_recordings_used"] is False

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["composition_id"] == "exploration_calm_v01"
    assert manifest["status"] == "integrated_master_candidate"
    assert manifest["external_samples_used"] is False
    assert manifest["sample_rate"] == 48_000
    assert manifest["channels"] == 2
    assert manifest["tempo_bpm"] == 72
    assert manifest["time_signature"] == [6, 8]
    assert manifest["bars"] == 36
    assert abs(float(manifest["duration_seconds"]) - 90.0) <= 0.001
    assert int(manifest["midi_note_count"]) >= 250
    assert float(manifest["peak_dbfs"]) <= -2.0
    assert float(manifest["boundary_value_delta"]) <= 0.01
    assert float(manifest["boundary_slope_delta"]) <= 0.01

    assert MASTER.is_file()
    assert 500_000 < MASTER.stat().st_size < 2_500_000
    assert MASTER.read_bytes()[:4] == b"OggS"
    assert hashlib.sha256(MASTER.read_bytes()).hexdigest() == manifest["ogg_sha256"]

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    context = catalog["contexts"]["world_exploration"]
    assert context["track_id"] == "exploration_calm"
    assert float(context["fade_seconds"]) == 2.0
    track = catalog["tracks"]["exploration_calm"]
    assert track["path"] == "res://assets/audio/music/exports/exploration_calm_v01_master.ogg"
    assert track["enabled"] is True
    assert track["loop"] is True
    assert track["composition_id"] == "exploration_calm_v01"

    with tempfile.TemporaryDirectory(prefix="exploration-calm-") as temp_dir:
        output = Path(temp_dir)
        subprocess.run(
            [sys.executable, str(GENERATOR), "--score", str(SCORE), "--output", str(output)],
            check=True,
        )
        rendered_wav = output / "exploration_calm_v01_master.wav"
        rendered_midi = output / "exploration_calm_v01.mid"
        assert rendered_midi.read_bytes()[:4] == b"MThd"
        with wave.open(str(rendered_wav), "rb") as wav_file:
            assert wav_file.getframerate() == 48_000
            assert wav_file.getnchannels() == 2
            assert wav_file.getsampwidth() == 2
            assert abs(wav_file.getnframes() / wav_file.getframerate() - 90.0) <= 0.001
        rendered_manifest = json.loads(
            (output / "exploration_calm_v01_master_manifest.json").read_text(encoding="utf-8")
        )
        assert rendered_manifest["wav_sha256"] == manifest["wav_sha256"]
        assert float(rendered_manifest["boundary_value_delta"]) <= 0.01

    print("Exploration calm v01 contracts passed.")


if __name__ == "__main__":
    main()
