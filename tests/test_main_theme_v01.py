from __future__ import annotations

import json
import shutil
import subprocess
import sys
import wave
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE_PATH = ROOT / "assets" / "audio" / "music" / "source" / "main_theme_v01_score.json"
GENERATOR_PATH = ROOT / "tools" / "audio" / "generate_main_theme_v01.py"
OUTPUT_PATH = ROOT / "build" / "audio" / "main_theme_v01"


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> None:
    score = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    if score.get("schema_version") != 1:
        fail("main theme score schema_version must be 1")
    if score.get("composition_id") != "main_theme_v01":
        fail("unexpected composition_id")
    if score.get("status") != "prototype":
        fail("main theme must remain a prototype until user approval")
    if score.get("original_composition") is not True:
        fail("original composition provenance flag is missing")
    if score.get("time_signature") != [6, 8]:
        fail("main theme must use the approved 6/8 meter")
    if int(score.get("tempo_bpm", 0)) != 76:
        fail("main theme tempo must be 76 BPM")
    if int(score.get("bars", 0)) != 32:
        fail("main theme must contain 32 bars")
    if len(score.get("harmony", [])) != 32:
        fail("harmony must define one chord per bar")
    motif = score.get("motif", {})
    if len(motif.get("notes", [])) != 5:
        fail("the Wanderer leitmotif must contain five notes")

    if not GENERATOR_PATH.is_file():
        fail("main theme generator is missing")
    shutil.rmtree(OUTPUT_PATH, ignore_errors=True)
    subprocess.run(
        [sys.executable, str(GENERATOR_PATH), "--score", str(SCORE_PATH), "--output", str(OUTPUT_PATH)],
        check=True,
    )

    midi_path = OUTPUT_PATH / "main_theme_v01.mid"
    wav_path = OUTPUT_PATH / "main_theme_v01_mockup.wav"
    manifest_path = OUTPUT_PATH / "main_theme_v01_manifest.json"
    for path in (midi_path, wav_path, manifest_path):
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"generated output is missing: {path.name}")
    if midi_path.read_bytes()[:4] != b"MThd":
        fail("generated MIDI has an invalid header")

    with wave.open(str(wav_path), "rb") as wav:
        if wav.getframerate() != 48_000:
            fail("WAV sample rate must be 48 kHz")
        if wav.getnchannels() != 2:
            fail("WAV must be stereo")
        if wav.getsampwidth() != 2:
            fail("WAV must use 16-bit PCM")
        duration = wav.getnframes() / wav.getframerate()
        if not 75.78 <= duration <= 75.80:
            fail(f"unexpected loop duration: {duration}")
        first = array("h", wav.readframes(128))
        wav.setpos(max(0, wav.getnframes() - 128))
        last = array("h", wav.readframes(128))
    if max(abs(sample) for sample in first) > 512:
        fail("loop head must enter near a zero crossing")
    if max(abs(sample) for sample in last) > 512:
        fail("loop tail must leave near a zero crossing")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("midi_note_count", 0) < 400:
        fail("generated arrangement is unexpectedly sparse")
    if int(manifest.get("peak_pcm", 0)) >= 32767:
        fail("generated WAV is clipping")

    if shutil.which("ffmpeg"):
        ogg_path = OUTPUT_PATH / "main_theme_v01.ogg"
        if not ogg_path.is_file() or ogg_path.stat().st_size < 100_000:
            fail("Ogg Vorbis preview was not generated")

    print("Main theme v01 composition pipeline passed.")


if __name__ == "__main__":
    main()
