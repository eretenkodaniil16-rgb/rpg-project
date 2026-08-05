#!/usr/bin/env python3
"""Render the original exploration_calm_v01 track for Chronicles of the Wanderer.

The score and synthesis are deterministic and use no downloaded samples,
recordings, imported MIDI, or third-party musical material.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import struct
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

PPQ = 480
NOTE_TO_SEMITONE = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}
CHORDS: dict[str, list[str]] = {
    "Dm(add9)": ["D2", "A2", "D3", "F3", "E4"],
    "Dm": ["D2", "A2", "D3", "F3", "A3"],
    "Bbmaj7": ["Bb1", "F2", "Bb2", "D3", "A3"],
    "C(add9)": ["C2", "G2", "C3", "E3", "D4"],
    "Gm7": ["G1", "D2", "G2", "Bb2", "F3"],
    "Fmaj7": ["F1", "C2", "F2", "A2", "E3"],
    "Am7": ["A1", "E2", "A2", "C3", "G3"],
    "Ebmaj7": ["Eb2", "Bb2", "Eb3", "G3", "D4"],
    "Asus4": ["A1", "E2", "A2", "D3", "E3"],
    "A5(b9)": ["A1", "E2", "A2", "Bb2", "E3"],
}

HARMONY = [
    "Dm(add9)", "Dm(add9)", "Bbmaj7", "C(add9)", "Dm", "Gm7", "Bbmaj7", "Asus4",
    "Dm(add9)", "Fmaj7", "C(add9)", "Gm7", "Bbmaj7", "Dm", "C(add9)", "Asus4", "Dm",
    "Gm7", "Ebmaj7", "Bbmaj7", "Fmaj7", "C(add9)", "Gm7", "A5(b9)", "Dm",
    "Bbmaj7", "Fmaj7", "C(add9)", "Dm", "Gm7", "Bbmaj7", "C(add9)", "Dm",
    "Gm7", "A5(b9)", "Dm(add9)",
]

# (note, start eighth, duration eighths, velocity)
MELODY: list[list[tuple[str, int, int, int]]] = [
    [], [],
    [("D4", 0, 2, 59), ("A3", 3, 1, 53), ("C4", 4, 2, 56)],
    [("E4", 0, 2, 58), ("D4", 3, 3, 55)],
    [], [("G4", 0, 2, 60), ("F4", 3, 1, 54), ("D4", 4, 2, 56)],
    [("F4", 0, 2, 57), ("D4", 3, 3, 54)], [],
    [("D4", 0, 3, 63), ("A3", 3, 1, 55), ("C4", 4, 1, 58), ("E4", 5, 1, 60)],
    [("F4", 0, 2, 61), ("E4", 3, 1, 56), ("D4", 4, 2, 58)],
    [], [("G4", 0, 2, 62), ("A4", 3, 1, 59), ("G4", 4, 2, 57)],
    [("F4", 0, 2, 60), ("D4", 3, 3, 56)], [],
    [("E4", 0, 1, 57), ("G4", 2, 2, 61), ("E4", 5, 1, 55)],
    [("D4", 0, 2, 58), ("C#4", 3, 1, 54), ("A3", 4, 2, 52)],
    [("D4", 0, 6, 59)], [],
    [("Eb4", 0, 2, 61), ("D4", 3, 1, 55), ("Bb3", 4, 2, 53)],
    [("F4", 0, 2, 59), ("D4", 3, 3, 55)],
    [], [("E4", 0, 2, 58), ("D4", 3, 1, 54), ("C4", 4, 2, 53)],
    [("G4", 0, 2, 60), ("F4", 3, 1, 56), ("D4", 4, 2, 54)],
    [("E4", 0, 1, 56), ("D4", 2, 1, 54), ("C#4", 3, 1, 55), ("A3", 4, 2, 51)],
    [("D4", 0, 6, 58)], [],
    [("A4", 0, 2, 62), ("F4", 3, 1, 57), ("E4", 4, 2, 56)],
    [("G4", 0, 2, 60), ("E4", 3, 3, 55)],
    [("D4", 0, 2, 63), ("A3", 3, 1, 55), ("C4", 4, 1, 58), ("E4", 5, 1, 60)],
    [], [("G4", 0, 2, 60), ("F4", 3, 1, 55), ("D4", 4, 2, 54)],
    [("E4", 0, 2, 58), ("D4", 3, 3, 55)],
    [("D4", 0, 6, 57)], [],
    [("E4", 0, 1, 55), ("D4", 2, 1, 53), ("C#4", 3, 1, 54), ("A3", 4, 2, 50)],
    [("D4", 0, 6, 55)],
]


@dataclass(frozen=True)
class MidiNote:
    track: str
    channel: int
    program: int
    note: int
    start_beat: float
    duration_beats: float
    velocity: int


def note_number(name: str) -> int:
    if name[1] in ("#", "b"):
        pitch_name, octave_text = name[:2], name[2:]
    else:
        pitch_name, octave_text = name[:1], name[1:]
    return 12 * (int(octave_text) + 1) + NOTE_TO_SEMITONE[pitch_name]


def frequency(name: str) -> float:
    return 440.0 * (2.0 ** ((note_number(name) - 69) / 12.0))


def envelope(length: int, sample_rate: int, attack: float, release: float, sustain: float = 1.0) -> np.ndarray:
    env = np.full(length, sustain, dtype=np.float64)
    attack_samples = min(length, max(1, round(attack * sample_rate)))
    release_samples = min(length, max(1, round(release * sample_rate)))
    env[:attack_samples] *= np.sin(np.linspace(0.0, math.pi / 2.0, attack_samples, endpoint=False)) ** 2
    env[-release_samples:] *= np.cos(np.linspace(0.0, math.pi / 2.0, release_samples, endpoint=False)) ** 2
    return env


def oscillator(freq: float, seconds: float, sample_rate: int, kind: str, seed: int) -> np.ndarray:
    length = max(1, round(seconds * sample_rate))
    time = np.arange(length, dtype=np.float64) / sample_rate
    rng = np.random.default_rng(seed)
    if kind == "bowed":
        vibrato = 0.0027 * np.sin(2.0 * math.pi * 4.7 * time)
        phase = 2.0 * math.pi * freq * time + vibrato
        signal = np.sin(phase) + 0.32 * np.sin(2.0 * phase + 0.12) + 0.11 * np.sin(3.0 * phase + 0.27)
        signal += 0.007 * rng.standard_normal(length)
        signal *= envelope(length, sample_rate, 0.28, 0.55, 0.82)
    elif kind == "pluck":
        phase = 2.0 * math.pi * freq * time
        signal = (
            np.sin(phase)
            + 0.43 * np.sin(2.0 * phase + 0.08)
            + 0.18 * np.sin(3.0 * phase + 0.19)
            + 0.07 * np.sin(5.0 * phase)
        )
        signal *= np.exp(-time * (2.1 + freq * 0.0015))
        signal *= envelope(length, sample_rate, 0.006, min(0.19, seconds * 0.42), 1.0)
    elif kind == "flute":
        phase = 2.0 * math.pi * freq * time + 0.009 * np.sin(2.0 * math.pi * 5.0 * time)
        breath = rng.standard_normal(length)
        breath = np.convolve(breath, np.ones(64) / 64.0, mode="same")
        signal = np.sin(phase) + 0.11 * np.sin(2.0 * phase) + 0.025 * breath
        signal *= envelope(length, sample_rate, 0.12, 0.30, 0.90)
    elif kind == "bell":
        signal = np.zeros(length, dtype=np.float64)
        for ratio, gain in ((1.0, 1.0), (2.03, 0.31), (3.17, 0.16), (4.41, 0.08)):
            signal += gain * np.sin(2.0 * math.pi * freq * ratio * time) * np.exp(-time * (1.15 + ratio * 0.22))
        signal *= envelope(length, sample_rate, 0.004, 0.45, 1.0)
    else:
        raise ValueError(f"Unknown oscillator kind: {kind}")
    peak = float(np.max(np.abs(signal))) or 1.0
    return signal / peak


def pan_mono(signal: np.ndarray, pan: float) -> np.ndarray:
    angle = (max(-1.0, min(1.0, pan)) + 1.0) * math.pi / 4.0
    return np.column_stack((signal * math.cos(angle), signal * math.sin(angle)))


def add_audio(target: np.ndarray, start: int, stereo: np.ndarray, gain: float) -> None:
    if start >= target.shape[0]:
        return
    end = min(target.shape[0], start + stereo.shape[0])
    if end > start:
        target[start:end] += stereo[: end - start] * gain


def add_note(target: np.ndarray, note: str, start_seconds: float, duration_seconds: float, sample_rate: int, kind: str, gain: float, pan: float, seed: int) -> None:
    tail = {"bowed": 0.65, "pluck": 0.22, "flute": 0.42, "bell": 1.10}[kind]
    mono = oscillator(frequency(note), duration_seconds + tail, sample_rate, kind, seed)
    add_audio(target, round(start_seconds * sample_rate), pan_mono(mono, pan), gain)


def add_room(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    wet = np.zeros_like(audio)
    for delay_seconds, gain, cross in (
        (0.091, 0.105, True), (0.173, 0.083, False), (0.281, 0.064, True),
        (0.427, 0.048, False), (0.653, 0.035, True), (0.941, 0.024, False),
    ):
        shift = round(delay_seconds * sample_rate)
        if cross:
            wet[shift:, 0] += audio[:-shift, 1] * gain
            wet[shift:, 1] += audio[:-shift, 0] * gain
        else:
            wet[shift:] += audio[:-shift] * gain
    return audio + wet


def soft_master(audio: np.ndarray) -> np.ndarray:
    audio -= np.mean(audio, axis=0, keepdims=True)
    mid = (audio[:, 0] + audio[:, 1]) * 0.5
    side = (audio[:, 0] - audio[:, 1]) * 0.48
    audio = np.column_stack((mid + side, mid - side))
    rms = math.sqrt(float(np.mean(audio * audio)) + 1e-12)
    target_rms = 10.0 ** (-19.0 / 20.0)
    audio *= target_rms / max(rms, 1e-9)
    audio = np.tanh(audio * 1.04) / np.tanh(1.04)
    peak_limit = 10.0 ** (-2.2 / 20.0)
    peak = float(np.max(np.abs(audio))) or 1.0
    if peak > peak_limit:
        audio *= peak_limit / peak
    return audio.astype(np.float32)


def encode_varlen(value: int) -> bytes:
    buffer = value & 0x7F
    output = bytearray([buffer])
    while value > 0x7F:
        value >>= 7
        output.insert(0, (value & 0x7F) | 0x80)
    return bytes(output)


def midi_track(name: str, events: list[tuple[int, bytes]]) -> bytes:
    payload = bytearray()
    name_bytes = name.encode("utf-8")
    payload += b"\x00\xFF\x03" + encode_varlen(len(name_bytes)) + name_bytes
    previous_tick = 0
    for tick, event in sorted(events, key=lambda item: (item[0], 0 if item[1][0] == 0x80 else 1)):
        payload += encode_varlen(max(0, tick - previous_tick)) + event
        previous_tick = tick
    payload += b"\x00\xFF\x2F\x00"
    return b"MTrk" + struct.pack(">I", len(payload)) + bytes(payload)


def write_midi(path: Path, bpm: int, notes: Iterable[MidiNote]) -> None:
    tempo = round(60_000_000 / bpm)
    conductor = bytearray()
    conductor += b"\x00\xFF\x51\x03" + tempo.to_bytes(3, "big")
    conductor += b"\x00\xFF\x58\x04\x06\x03\x18\x08"
    conductor += b"\x00\xFF\x59\x02\xFF\x00"
    conductor += b"\x00\xFF\x2F\x00"
    chunks = [b"MTrk" + struct.pack(">I", len(conductor)) + bytes(conductor)]
    grouped: dict[tuple[str, int, int], list[MidiNote]] = {}
    for item in notes:
        grouped.setdefault((item.track, item.channel, item.program), []).append(item)
    for (track_name, channel, program), track_notes in grouped.items():
        events: list[tuple[int, bytes]] = [(0, bytes([0xC0 | channel, program]))]
        for item in track_notes:
            start_tick = round(item.start_beat * PPQ)
            end_tick = round((item.start_beat + item.duration_beats) * PPQ)
            events.append((start_tick, bytes([0x90 | channel, item.note, item.velocity])))
            events.append((end_tick, bytes([0x80 | channel, item.note, 0])))
        chunks.append(midi_track(track_name, events))
    path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQ) + b"".join(chunks))


def render(score_path: Path, output_dir: Path) -> dict:
    score = json.loads(score_path.read_text(encoding="utf-8"))
    sample_rate = int(score["sample_rate"])
    bpm = int(score["tempo_bpm"])
    bars = int(score["bars"])
    if bars != len(HARMONY) or bars != len(MELODY):
        raise ValueError("Score bar count does not match the renderer arrangement.")
    eighth_seconds = (60.0 / bpm) / 2.0
    bar_seconds = (60.0 / bpm) * 3.0
    cycle_seconds = bars * bar_seconds
    cycle_samples = round(cycle_seconds * sample_rate)
    render_samples = cycle_samples * 3
    mix = np.zeros((render_samples, 2), dtype=np.float64)
    midi_notes: list[MidiNote] = []

    for repetition in range(3):
        cycle_offset = repetition * cycle_seconds
        for bar_index, chord_name in enumerate(HARMONY):
            chord = CHORDS[chord_name]
            start = cycle_offset + bar_index * bar_seconds
            section_gain = 0.88 if bar_index < 8 else 1.0 if bar_index < 17 else 0.91 if bar_index < 25 else 0.96
            add_note(mix, chord[0], start, bar_seconds * 0.98, sample_rate, "bowed", 0.115 * section_gain, -0.18, 10000 + repetition * 1000 + bar_index)
            add_note(mix, chord[1], start, bar_seconds * 0.98, sample_rate, "bowed", 0.076 * section_gain, 0.12, 11000 + repetition * 1000 + bar_index)
            if 8 <= bar_index <= 31:
                add_note(mix, chord[2], start, bar_seconds * 0.92, sample_rate, "bowed", 0.030 * section_gain, 0.28, 12000 + repetition * 1000 + bar_index)

            pluck_steps = ((0, 0), (2, 2), (3, 1), (5, 3))
            if bar_index in (0, 1, 17, 18, 32, 35):
                pluck_steps = ((0, 0), (3, 2))
            for event_index, (eighth, chord_index) in enumerate(pluck_steps):
                note = chord[min(chord_index, len(chord) - 1)]
                add_note(mix, note, start + eighth * eighth_seconds, eighth_seconds * 1.12, sample_rate, "pluck", 0.066 * section_gain, -0.40, 20000 + repetition * 2000 + bar_index * 8 + event_index)
                if repetition == 1:
                    midi_notes.append(MidiNote("Dark plucked strings", 1, 46, note_number(note), bar_index * 3.0 + eighth * 0.5, 0.48, 38 + event_index * 2))

            if repetition == 1:
                midi_notes.append(MidiNote("Low bowed strings", 0, 42, note_number(chord[0]), bar_index * 3.0, 2.92, 46))
                midi_notes.append(MidiNote("Low bowed strings", 0, 42, note_number(chord[1]), bar_index * 3.0, 2.92, 38))

        for bar_index, events in enumerate(MELODY):
            for event_index, (note, eighth, duration_eighths, velocity) in enumerate(events):
                start = cycle_offset + bar_index * bar_seconds + eighth * eighth_seconds
                gain = 0.095 + max(0, velocity - 50) / 260.0
                add_note(mix, note, start, duration_eighths * eighth_seconds * 0.92, sample_rate, "flute", gain, 0.31, 30000 + repetition * 3000 + bar_index * 12 + event_index)
                if repetition == 1:
                    midi_notes.append(MidiNote("Wooden flute", 2, 73, note_number(note), bar_index * 3.0 + eighth * 0.5, duration_eighths * 0.46, velocity))

        for bell_index, (bar_index, note) in enumerate(((0, "D5"), (8, "A4"), (17, "Eb5"), (25, "F5"), (35, "D5"))):
            start = cycle_offset + bar_index * bar_seconds + (0.08 if bar_index != 35 else 0.0)
            add_note(mix, note, start, 1.65, sample_rate, "bell", 0.031, 0.57, 40000 + repetition * 100 + bell_index)
            if repetition == 1:
                midi_notes.append(MidiNote("Distant bell", 3, 14, note_number(note), bar_index * 3.0, 1.35, 35))

    sample_index = np.arange(cycle_samples, dtype=np.float64)
    phase = 2.0 * math.pi * sample_index / cycle_samples
    rng = np.random.default_rng(72036)
    noise = rng.standard_normal(cycle_samples)
    kernel = np.ones(1024, dtype=np.float64) / 1024.0
    smooth = np.convolve(np.concatenate((noise[-1023:], noise, noise[:1023])), kernel, mode="valid")[:cycle_samples]
    smooth /= float(np.max(np.abs(smooth))) or 1.0
    air_cycle = smooth * (0.48 + 0.22 * np.sin(phase * 5.0) + 0.14 * np.sin(phase * 11.0 + 0.7))
    mix += pan_mono(np.tile(air_cycle, 3), -0.08) * 0.0065

    mix = add_room(mix, sample_rate)
    cycle = soft_master(mix[cycle_samples: cycle_samples * 2].copy())

    output_dir.mkdir(parents=True, exist_ok=True)
    wav_path = output_dir / "exploration_calm_v01_master.wav"
    pcm = np.clip(cycle * 32767.0, -32768, 32767).astype("<i2")
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())

    midi_path = output_dir / "exploration_calm_v01.mid"
    write_midi(midi_path, bpm, midi_notes)

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to create the game export.")
    ogg_path = output_dir / "exploration_calm_v01_master.ogg"
    mp3_path = output_dir / "exploration_calm_v01_preview.mp3"
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
        "external_samples_used": false,
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
    (output_dir / "exploration_calm_v01_master_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
