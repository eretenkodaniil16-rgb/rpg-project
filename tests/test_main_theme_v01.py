from __future__ import annotations

import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "assets/audio/music/source/main_theme_v01_score.json"
GENERATOR = ROOT / "tools/audio/generate_main_theme_v01.py"
OUTPUT = ROOT / "build/audio/main_theme_v01"


def main() -> None:
    score = json.loads(SCORE.read_text(encoding="utf-8"))
    assert score["schema_version"] == 1
    assert score["composition_id"] == "main_theme_v01"
    assert score["status"] == "approved_composition"
    assert score["original_composition"] is True
    assert score["time_signature"] == [6, 8]
    assert score["tempo_bpm"] == 76
    assert score["bars"] == 32
    assert len(score["harmony"]) == 32
    assert score["motif"]["notes"] == ["D4", "A3", "C4", "Eb4", "D4"]

    shutil.rmtree(OUTPUT, ignore_errors=True)
    subprocess.run(
        [sys.executable, str(GENERATOR), "--score", str(SCORE), "--output", str(OUTPUT)],
        check=True,
    )
    midi = OUTPUT / "main_theme_v01.mid"
    wav_path = OUTPUT / "main_theme_v01_mockup.wav"
    assert midi.read_bytes()[:4] == b"MThd"
    with wave.open(str(wav_path), "rb") as wav_file:
        assert wav_file.getframerate() == 48_000
        assert wav_file.getnchannels() == 2
        assert wav_file.getsampwidth() == 2
        duration = wav_file.getnframes() / wav_file.getframerate()
        assert 75.78 <= duration <= 75.80
    manifest = json.loads((OUTPUT / "main_theme_v01_manifest.json").read_text(encoding="utf-8"))
    assert manifest["midi_note_count"] >= 400
    assert manifest["peak_pcm"] < 32767
    if shutil.which("ffmpeg"):
        assert (OUTPUT / "main_theme_v01.ogg").stat().st_size > 100_000
    print("Main theme v01 composition pipeline passed.")


if __name__ == "__main__":
    main()
