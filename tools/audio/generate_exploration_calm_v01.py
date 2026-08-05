#!/usr/bin/env python3
"""Deterministic renderer for the original exploration_calm_v01 track."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BASE_RENDERER = HERE / "generate_main_theme_v01.py"


def load_base():
    spec = importlib.util.spec_from_file_location("main_theme_audio_primitives", BASE_RENDERER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {BASE_RENDERER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CHORDS = {
    "Dm9": ["D2", "A2", "D3", "F3", "E4"],
    "Dm": ["D2", "A2", "D3", "F3", "A3"],
    "BbM7": ["Bb1", "F2", "Bb2", "D3", "A3"],
    "C9": ["C2", "G2", "C3", "E3", "D4"],
    "Gm7": ["G1", "D2", "G2", "Bb2", "F3"],
    "FM7": ["F1", "C2", "F2", "A2", "E3"],
    "EbM7": ["Eb2", "Bb2", "Eb3", "G3", "D4"],
    "As4": ["A1", "E2", "A2", "D3", "E3"],
    "A5b9": ["A1", "E2", "A2", "Bb2", "E3"],
}
HARMONY = (
    "Dm9 Dm9 BbM7 C9 Dm Gm7 BbM7 As4 "
    "Dm9 FM7 C9 Gm7 BbM7 Dm C9 As4 Dm "
    "Gm7 EbM7 BbM7 FM7 C9 Gm7 A5b9 Dm "
    "BbM7 FM7 C9 Dm Gm7 BbM7 C9 Dm Gm7 A5b9 Dm9"
).split()

MELODY = {
    2: [("D4", 0, 2, 59), ("A3", 3, 1, 53), ("C4", 4, 2, 56)],
    3: [("E4", 0, 2, 58), ("D4", 3, 3, 55)],
    5: [("G4", 0, 2, 60), ("F4", 3, 1, 54), ("D4", 4, 2, 56)],
    6: [("F4", 0, 2, 57), ("D4", 3, 3, 54)],
    8: [("D4", 0, 3, 63), ("A3", 3, 1, 55), ("C4", 4, 1, 58), ("E4", 5, 1, 60)],
    9: [("F4", 0, 2, 61), ("E4", 3, 1, 56), ("D4", 4, 2, 58)],
    11: [("G4", 0, 2, 62), ("A4", 3, 1, 59), ("G4", 4, 2, 57)],
    12: [("F4", 0, 2, 60), ("D4", 3, 3, 56)],
    14: [("E4", 0, 1, 57), ("G4", 2, 2, 61), ("E4", 5, 1, 55)],
    15: [("D4", 0, 2, 58), ("C#4", 3, 1, 54), ("A3", 4, 2, 52)],
    16: [("D4", 0, 6, 59)],
    18: [("Eb4", 0, 2, 61), ("D4", 3, 1, 55), ("Bb3", 4, 2, 53)],
    19: [("F4", 0, 2, 59), ("D4", 3, 3, 55)],
    21: [("E4", 0, 2, 58), ("D4", 3, 1, 54), ("C4", 4, 2, 53)],
    22: [("G4", 0, 2, 60), ("F4", 3, 1, 56), ("D4", 4, 2, 54)],
    23: [("E4", 0, 1, 56), ("D4", 2, 1, 54), ("C#4", 3, 1, 55), ("A3", 4, 2, 51)],
    24: [("D4", 0, 6, 58)],
    26: [("A4", 0, 2, 62), ("F4", 3, 1, 57), ("E4", 4, 2, 56)],
    27: [("G4", 0, 2, 60), ("E4", 3, 3, 55)],
    28: [("D4", 0, 2, 63), ("A3", 3, 1, 55), ("C4", 4, 1, 58), ("E4", 5, 1, 60)],
    30: [("G4", 0, 2, 60), ("F4", 3, 1, 55), ("D4", 4, 2, 54)],
    31: [("E4", 0, 2, 58), ("D4", 3, 3, 55)],
    32: [("D4", 0, 6, 57)],
    34: [("E4", 0, 1, 55), ("D4", 2, 1, 53), ("C#4", 3, 1, 54), ("A3", 4, 2, 50)],
    35: [("D4", 0, 6, 55)],
}


def add_room(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    wet = np.zeros_like(audio)
    for seconds, gain, cross in (
        (0.091, 0.105, True), (0.173, 0.083, False), (0.281, 0.064, True),
        (0.427, 0.048, False), (0.653, 0.035, True), (0.941, 0.024, False),
    ):
        shift = round(seconds * sample_rate)
        if cross:
            wet[shift:, 0] += audio[:-shift, 1] * gain
            wet[shift:, 1] += audio[:-shift, 0] * gain
        else:
            wet[shift:] += audio[:-shift] * gain
    return audio + wet


def master(audio: np.ndarray) -> np.ndarray:
    audio -= np.mean(audio, axis=0, keepdims=True)
    mid = (audio[:, 0] + audio[:, 1]) * 0.5
    side = (audio[:, 0] - audio[:, 1]) * 0.48
    audio = np.column_stack((mid + side, mid - side))
    target_rms = 10.0 ** (-19.0 / 20.0)
    rms = math.sqrt(float(np.mean(audio * audio)) + 1e-12)
    audio *= target_rms / max(rms, 1e-9)
    audio = np.tanh(audio * 1.04) / np.tanh(1.04)
    peak_limit = 10.0 ** (-2.2 / 20.0)
    peak = float(np.max(np.abs(audio))) or 1.0
    return (audio * min(1.0, peak_limit / peak)).astype(np.float32)


def render(score_path: Path, output: Path) -> dict:
    base = load_base()
    score = json.loads(score_path.read_text(encoding="utf-8"))
    sample_rate = int(score["sample_rate"])
    bpm = int(score["tempo_bpm"])
    bars = int(score["bars"])
    if bars != 36 or len(HARMONY) != bars:
        raise ValueError("exploration_calm_v01 must contain 36 bars")
    eighth_seconds = (60.0 / bpm) / 2.0
    bar_seconds = (60.0 / bpm) * 3.0
    cycle_samples = round(bars * bar_seconds * sample_rate)
    mix = np.zeros((cycle_samples * 3, 2), dtype=np.float64)
    midi_notes = []

    for repetition in range(3):
        offset = repetition * bars * bar_seconds
        for bar_index, chord_id in enumerate(HARMONY):
            chord = CHORDS[chord_id]
            start = offset + bar_index * bar_seconds
            section_gain = 0.88 if bar_index < 8 else 1.0 if bar_index < 17 else 0.91 if bar_index < 25 else 0.96
            base.add_note(mix, chord[0], start, bar_seconds * 0.98, sample_rate, "bowed", 0.115 * section_gain, -0.18, 10000 + repetition * 1000 + bar_index)
            base.add_note(mix, chord[1], start, bar_seconds * 0.98, sample_rate, "bowed", 0.076 * section_gain, 0.12, 11000 + repetition * 1000 + bar_index)
            if 8 <= bar_index <= 31:
                base.add_note(mix, chord[2], start, bar_seconds * 0.92, sample_rate, "bowed", 0.030 * section_gain, 0.28, 12000 + repetition * 1000 + bar_index)

            pattern = ((0, 0), (3, 2)) if bar_index in (0, 1, 17, 18, 32, 35) else ((0, 0), (2, 2), (3, 1), (5, 3))
            for event_index, (eighth, chord_index) in enumerate(pattern):
                note = chord[chord_index]
                base.add_note(mix, note, start + eighth * eighth_seconds, eighth_seconds * 1.12, sample_rate, "pluck", 0.066 * section_gain, -0.40, 20000 + repetition * 2000 + bar_index * 8 + event_index)
                if repetition == 1:
                    midi_notes.append(base.MidiNote("Dark plucked strings", 1, 46, base.note_number(note), bar_index * 3.0 + eighth * 0.5, 0.48, 38 + event_index * 2))
            if repetition == 1:
                midi_notes.append(base.MidiNote("Low bowed strings", 0, 42, base.note_number(chord[0]), bar_index * 3.0, 2.92, 46))
                midi_notes.append(base.MidiNote("Low bowed strings", 0, 42, base.note_number(chord[1]), bar_index * 3.0, 2.92, 38))

        for bar_index, events in MELODY.items():
            for event_index, (note, eighth, duration, velocity) in enumerate(events):
                start = offset + bar_index * bar_seconds + eighth * eighth_seconds
                base.add_note(mix, note, start, duration * eighth_seconds * 0.92, sample_rate, "flute", 0.095 + max(0, velocity - 50) / 260.0, 0.31, 30000 + repetition * 3000 + bar_index * 12 + event_index)
                if repetition == 1:
                    midi_notes.append(base.MidiNote("Wooden flute", 2, 73, base.note_number(note), bar_index * 3.0 + eighth * 0.5, duration * 0.46, velocity))

        for bell_index, (bar_index, note) in enumerate(((0, "D5"), (8, "A4"), (17, "Eb5"), (25, "F5"), (35, "D5"))):
            base.add_note(mix, note, offset + bar_index * bar_seconds + (0.08 if bar_index != 35 else 0.0), 1.65, sample_rate, "bell", 0.031, 0.57, 40000 + repetition * 100 + bell_index)
            if repetition == 1:
                midi_notes.append(base.MidiNote("Distant bell", 3, 14, base.note_number(note), bar_index * 3.0, 1.35, 35))

    index = np.arange(cycle_samples, dtype=np.float64)
    phase = 2.0 * math.pi * index / cycle_samples
    rng = np.random.default_rng(72036)
    noise = rng.standard_normal(cycle_samples)
    kernel = np.ones(1024, dtype=np.float64) / 1024.0
    smooth = np.convolve(np.concatenate((noise[-1023:], noise, noise[:1023])), kernel, mode="valid")[:cycle_samples]
    smooth /= float(np.max(np.abs(smooth))) or 1.0
    air = smooth * (0.48 + 0.22 * np.sin(phase * 5.0) + 0.14 * np.sin(phase * 11.0 + 0.7))
    mix += base.pan_mono(np.tile(air, 3), -0.08) * 0.0065

    cycle = master(add_room(mix, sample_rate)[cycle_samples:cycle_samples * 2].copy())
    output.mkdir(parents=True, exist_ok=True)
    wav_path = output / "exploration_calm_v01_master.wav"
    pcm = np.clip(cycle * 32767.0, -32768, 32767).astype("<i2")
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())

    midi_path = output / "exploration_calm_v01.mid"
    base.write_midi(midi_path, bpm, midi_notes)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required")
    ogg_path = output / "exploration_calm_v01_master.ogg"
    mp3_path = output / "exploration_calm_v01_preview.mp3"
    subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path), "-c:a", "libvorbis", "-q:a", "6", str(ogg_path)], check=True)
    subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path), "-c:a", "libmp3lame", "-b:a", "224k", str(mp3_path)], check=True)

    peak = float(np.max(np.abs(cycle)))
    rms = math.sqrt(float(np.mean(cycle * cycle)) + 1e-12)
    manifest = {
        "schema_version": 1,
        "composition_id": score["composition_id"],
        "render_id": "exploration_calm_v01_master_candidate_01",
        "status": "integrated_master_candidate",
        "renderer": "procedural_exploration_renderer_v01",
        "external_samples_used": False,
        "sample_rate": sample_rate,
        "channels": 2,
        "tempo_bpm": bpm,
        "time_signature": score["time_signature"],
        "bars": bars,
        "duration_seconds": round(len(cycle) / sample_rate, 6),
        "midi_note_count": len(midi_notes),
        "peak_dbfs": round(20.0 * math.log10(max(peak, 1e-12)), 3),
        "rms_dbfs": round(20.0 * math.log10(max(rms, 1e-12)), 3),
        "boundary_value_delta": round(float(np.max(np.abs(cycle[0] - cycle[-1]))), 8),
        "boundary_slope_delta": round(float(np.max(np.abs((cycle[1] - cycle[0]) - (cycle[-1] - cycle[-2])))), 8),
        "ogg_bytes": ogg_path.stat().st_size,
        "ogg_sha256": hashlib.sha256(ogg_path.read_bytes()).hexdigest(),
        "wav_sha256": hashlib.sha256(wav_path.read_bytes()).hexdigest(),
        "source_score_sha256": hashlib.sha256(json.dumps(score, sort_keys=True).encode("utf-8")).hexdigest(),
    }
    (output / "exploration_calm_v01_master_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(args.score, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
