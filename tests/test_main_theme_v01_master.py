from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "assets/audio/music/source/main_theme_v01_score.json"
MANIFEST = ROOT / "assets/audio/music/source/main_theme_v01_master_manifest.json"
MASTER = ROOT / "assets/audio/music/exports/main_theme_v01_master.ogg"
RENDERER = ROOT / "tools/audio/render_main_theme_v01_master.py"
CATALOG = ROOT / "data/audio/music_catalog.json"


def main() -> None:
    score = json.loads(SCORE.read_text(encoding="utf-8"))
    assert score["status"] == "approved_composition"
    assert score["tempo_bpm"] == 76
    assert score["time_signature"] == [6, 8]
    assert score["bars"] == 32
    assert score["motif"]["notes"] == ["D4", "A3", "C4", "Eb4", "D4"]

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["composition_id"] == "main_theme_v01"
    assert manifest["status"] == "integrated_master_candidate"
    assert manifest["external_samples_used"] is False
    assert manifest["sample_rate"] == 48_000
    assert manifest["channels"] == 2
    assert 75.78 <= float(manifest["duration_seconds"]) <= 75.80
    assert float(manifest["peak_dbfs"]) <= -1.0
    assert float(manifest["boundary_value_delta"]) <= 0.01
    assert float(manifest["boundary_slope_delta"]) <= 0.01

    assert MASTER.is_file()
    assert 500_000 < MASTER.stat().st_size < 2_500_000
    assert MASTER.read_bytes()[:4] == b"OggS"
    assert hashlib.sha256(MASTER.read_bytes()).hexdigest() == manifest["ogg_sha256"]

    track = json.loads(CATALOG.read_text(encoding="utf-8"))["tracks"]["main_theme"]
    assert track["path"] == "res://assets/audio/music/exports/main_theme_v01_master.ogg"
    assert track["enabled"] is True
    assert track["loop"] is True

    with tempfile.TemporaryDirectory(prefix="main-theme-master-") as temp_dir:
        output = Path(temp_dir)
        subprocess.run(
            [sys.executable, str(RENDERER), "--score", str(SCORE), "--output", str(output)],
            check=True,
        )
        rendered_wav = output / "main_theme_v01_master_candidate.wav"
        rendered_ogg = output / "main_theme_v01_master_candidate.ogg"
        assert rendered_wav.is_file() and rendered_ogg.is_file()
        with wave.open(str(rendered_wav), "rb") as wav_file:
            assert wav_file.getframerate() == 48_000
            assert wav_file.getnchannels() == 2
            duration = wav_file.getnframes() / wav_file.getframerate()
            assert abs(duration - float(manifest["duration_seconds"])) <= 0.001

    print("Main theme v01 master and menu integration contracts passed.")


if __name__ == "__main__":
    main()
