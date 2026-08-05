#!/usr/bin/env python3
"""Render the original exploration tension cue for Chronicles of the Wanderer.

The renderer is deterministic and uses only procedural synthesis. It produces a
48 kHz stereo WAV, Ogg Vorbis game master, MP3 listening preview, MIDI guide and
machine-readable manifest. No external recordings or sample packs are used.
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

REQUIRED_NUMPY_VERSION = "2.3.5"

PPQ = 480
NOTE_TO_SEMITONE = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}
CHORDS: dict[str, list[str]] = {
    "Dm(add9)": ["D2", "A2", "D3", "F3", "E4"],
    "Dm": ["D2", "A2", "D3", "F3", "A3"],
    "Eb5": ["Eb2", "Bb2", "Eb3", "Bb3", "Eb4"],
    "Bbmaj7": ["Bb1", "F2", "Bb2", "D3", "A3"],
    "A5(b9)": ["A1", "E2", "A2", "Bb2", "E3"],
    "C/D": ["D2", "G2", "C3", "D3", "G3"],
    "Gm/D": ["D2", "G2", "Bb2", "D3", "G3"],
    "Eb": ["Eb2", "Bb2", "Eb3", "G3", "Bb3"],
    "Bb": ["Bb1", "F2", "Bb2", "D3", "F3"],
    "Csus2": ["C2", "G2", "C3", "D3", "G3"],
    "Dm/F": ["F1", "A2", "D3", "F3", "A3"],
    "Gm": ["G1", "D2", "G2", "Bb2", "D3"],
}

# duration is in eighth notes; deliberate gaps keep the cue watchful rather than lyrical.
MELODY: dict[int, list[tuple[str, int, int, int]]] = {
    2: [("D4", 2, 54, 0), ("A3", 1, 47, 3), ("C4", 1, 50, 5)],
    4: [("Eb4", 1, 55, 1), ("D4", 2, 51, 3)],
    6: [("D4", 1, 50, 0), ("C4", 1, 47, 2), ("A3", 2, 49, 4)],
    8: [("E4", 1, 49, 1), ("Eb4", 1, 52, 3), ("D4", 1, 48, 5)],
    10: [("D4", 2, 57, 0), ("A3", 1, 49, 3), ("C4", 1, 53, 5)],
    12: [("F4", 1, 55, 0), ("Eb4", 1, 53, 2), ("D4", 2, 51, 4)],
    14: [("D4", 1, 52, 1), ("C4", 1, 50, 3), ("A3", 1, 48, 5)],
    16: [("Bb3", 1, 50, 0), ("C4", 1, 52, 2), ("D4", 2, 56, 4)],
    18: [("D4", 1, 59, 0), ("Eb4", 1, 61, 2), ("F4", 1, 58, 4)],
    20: [("A4", 1, 60, 0), ("G4", 1, 57, 2), ("Eb4", 2, 55, 4)],
    22: [("D4", 1, 58, 0), ("A3", 1, 52, 2), ("C4", 1, 56, 4)],
    24: [("E4", 1, 56, 0), ("Eb4", 1, 59, 2), ("D4", 2, 55, 4)],
    26: [("F4", 1, 57, 1), ("Eb4", 1, 55, 3), ("D4", 1, 52, 5)],
    28: [("D4", 2, 53, 0), ("C4", 1, 49, 3), ("A3", 1, 47, 5)],
    30: [("Bb3", 1, 49, 1), ("C4", 1, 51, 3), ("D4", 1, 52, 5)],
    32: [("Eb4", 1, 52, 0), ("D4", 2, 49, 3)],
}

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
    pitch = name[:2] if len(name) > 2 and name[1] in "#b" else name[:1]
    octave = int(name[len(pitch):])
    return 12 * (octave + 1) + NOTE_TO_SEMITONE[pitch]


def frequency(name: str) -> float:
    return 440.0 * 2.0 ** ((note_number(name) - 69) / 12.0)


def envelope(length: int, sr: int, attack: float, release: float, sustain: float = 1.0) -> np.ndarray:
    env = np.full(length, sustain, dtype=np.float32)
    a = min(length, max(1, int(attack * sr)))
    r = min(length, max(1, int(release * sr)))
    env[:a] *= np.sin(np.linspace(0.0, math.pi / 2.0, a, endpoint=False, dtype=np.float32)) ** 2
    env[-r:] *= np.cos(np.linspace(0.0, math.pi / 2.0, r, endpoint=False, dtype=np.float32)) ** 2
    return env


def oscillator(freq: float, seconds: float, sr: int, kind: str, seed: int) -> np.ndarray:
    n = max(1, round(seconds * sr))
    t = np.arange(n, dtype=np.float32) / sr
    rng = np.random.default_rng(seed)
    if kind == "low_bow":
        phase = 2.0 * math.pi * freq * t + 0.0025 * np.sin(2.0 * math.pi * 4.7 * t)
        sig = np.sin(phase) + 0.38 * np.sin(2.0 * phase + 0.13) + 0.13 * np.sin(3.0 * phase)
        noise = rng.standard_normal(n).astype(np.float32)
        noise = np.convolve(noise, np.ones(32, dtype=np.float32) / 32.0, mode="same")
        sig = sig + 0.018 * noise
        sig *= envelope(n, sr, 0.28, 0.55, 0.78)
    elif kind == "pluck":
        phase = 2.0 * math.pi * freq * t
        sig = (np.sin(phase) + 0.42 * np.sin(2.0 * phase) + 0.17 * np.sin(3.0 * phase))
        sig *= np.exp(-t * (3.2 + freq * 0.002)).astype(np.float32)
        sig *= envelope(n, sr, 0.004, min(0.12, seconds * 0.35), 1.0)
    elif kind == "flute":
        phase = 2.0 * math.pi * freq * t + 0.009 * np.sin(2.0 * math.pi * 5.2 * t)
        breath = rng.standard_normal(n).astype(np.float32)
        breath = np.convolve(breath, np.ones(64, dtype=np.float32) / 64.0, mode="same")
        sig = np.sin(phase) + 0.12 * np.sin(2.0 * phase) + 0.028 * breath
        sig *= envelope(n, sr, 0.11, 0.32, 0.84)
    elif kind == "metal":
        sig = np.zeros(n, dtype=np.float32)
        for ratio, gain, decay in ((1.0, 1.0, 1.4), (1.71, 0.37, 1.8), (2.63, 0.21, 2.2), (4.07, 0.11, 2.8)):
            sig += gain * np.sin(2.0 * math.pi * freq * ratio * t) * np.exp(-t * decay)
        sig *= envelope(n, sr, 0.002, min(0.7, seconds * 0.45), 1.0)
    else:
        raise ValueError(kind)
    peak = float(np.max(np.abs(sig))) or 1.0
    return (sig / peak).astype(np.float32)


def frame_drum(seconds: float, sr: int, seed: int) -> np.ndarray:
    n = max(1, round(seconds * sr))
    t = np.arange(n, dtype=np.float32) / sr
    rng = np.random.default_rng(seed)
    freq_curve = 72.0 * np.exp(-t * 5.0) + 38.0
    phase = 2.0 * math.pi * np.cumsum(freq_curve) / sr
    body = np.sin(phase) * np.exp(-t * 6.2)
    skin = rng.standard_normal(n).astype(np.float32)
    skin = np.convolve(skin, np.ones(12, dtype=np.float32) / 12.0, mode="same") * np.exp(-t * 19.0)
    sig = body + 0.16 * skin
    return (sig / (float(np.max(np.abs(sig))) or 1.0)).astype(np.float32)


def pan(signal: np.ndarray, position: float) -> np.ndarray:
    p = max(-1.0, min(1.0, position))
    angle = (p + 1.0) * math.pi / 4.0
    return np.column_stack((signal * math.cos(angle), signal * math.sin(angle))).astype(np.float32)


def add(target: np.ndarray, start: int, stereo: np.ndarray, gain: float) -> None:
    if start >= target.shape[0]:
        return
    end = min(target.shape[0], start + stereo.shape[0])
    if end > start:
        target[start:end] += stereo[:end-start] * gain


def add_note(target: np.ndarray, name: str, start_s: float, duration_s: float, sr: int,
             kind: str, gain: float, position: float, seed: int) -> None:
    tail = {"low_bow": 0.75, "flute": 0.5, "metal": 1.6, "pluck": 0.2}[kind]
    add(target, round(start_s * sr), pan(oscillator(frequency(name), duration_s + tail, sr, kind, seed), position), gain)


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
    previous = 0
    for tick, event in sorted(events, key=lambda item: (item[0], 0 if item[1][0] & 0xF0 == 0x80 else 1)):
        payload += encode_varlen(max(0, tick - previous)) + event
        previous = tick
    payload += b"\x00\xFF\x2F\x00"
    return b"MTrk" + struct.pack(">I", len(payload)) + bytes(payload)


def write_midi(path: Path, bpm: int, notes: Iterable[MidiNote]) -> None:
    tempo = round(60_000_000 / bpm)
    conductor = bytearray(b"\x00\xFF\x51\x03") + tempo.to_bytes(3, "big")
    conductor += b"\x00\xFF\x58\x04\x06\x03\x18\x08\x00\xFF\x59\x02\xFF\x00\x00\xFF\x2F\x00"
    chunks = [b"MTrk" + struct.pack(">I", len(conductor)) + bytes(conductor)]
    grouped: dict[tuple[str, int, int], list[MidiNote]] = {}
    for note in notes:
        grouped.setdefault((note.track, note.channel, note.program), []).append(note)
    for (track_name, channel, program), track_notes in grouped.items():
        events: list[tuple[int, bytes]] = [(0, bytes([0xC0 | channel, program]))]
        for item in track_notes:
            start = round(item.start_beat * PPQ)
            end = round((item.start_beat + item.duration_beats) * PPQ)
            events.append((start, bytes([0x90 | channel, item.note, item.velocity])))
            events.append((end, bytes([0x80 | channel, item.note, 0])))
        chunks.append(midi_track(track_name, events))
    path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQ) + b"".join(chunks))


def render(score_path: Path, output: Path) -> dict:
    score = json.loads(score_path.read_text(encoding="utf-8"))
    sr = int(score["sample_rate"])
    bpm = int(score["tempo_bpm"])
    bars = int(score["bars"])
    beat_s = 60.0 / bpm
    eighth_s = beat_s / 2.0
    bar_s = beat_s * 3.0
    cycle_s = bars * bar_s
    cycle_samples = round(cycle_s * sr)
    total_samples = cycle_samples * 3
    mix = np.zeros((total_samples, 2), dtype=np.float32)
    notes: list[MidiNote] = []
    harmony = score["harmony"]

    for cycle in range(3):
        cycle_offset_s = cycle * cycle_s
        for bar, chord_name in enumerate(harmony):
            chord = CHORDS[chord_name]
            start = cycle_offset_s + bar * bar_s
            pressure = 1.0 + (0.10 if 17 <= bar <= 25 else 0.0)
            add_note(mix, chord[0], start, bar_s * 0.98, sr, "low_bow", 0.115 * pressure, -0.17, 1000 + bar)
            add_note(mix, chord[1], start, bar_s * 0.98, sr, "low_bow", 0.072 * pressure, 0.13, 1100 + bar)
            if cycle == 1:
                notes += [
                    MidiNote("Low bowed strings", 0, 43, note_number(chord[0]), bar * 3.0, 2.92, 42),
                    MidiNote("Low bowed strings", 0, 43, note_number(chord[1]), bar * 3.0, 2.92, 34),
                ]

            pattern = [0, 2, 1, 3, 1, 2]
            active_steps = (0, 3) if bar < 8 or bar >= 27 else (0, 2, 3, 5)
            if 17 <= bar <= 25:
                active_steps = (0, 1, 3, 4, 5)
            for step in active_steps:
                chord_index = pattern[step]
                name = chord[min(chord_index, len(chord) - 1)]
                event_start = start + step * eighth_s
                gain = 0.063 if step in (0, 3) else 0.047
                add_note(mix, name, event_start, eighth_s * 0.68, sr, "pluck", gain, -0.43, 2000 + bar * 8 + step)
                if cycle == 1:
                    notes.append(MidiNote("Muted plucked strings", 1, 45, note_number(name), bar * 3.0 + step * 0.5, 0.31, 32 + (step % 3) * 4))

        for bar, events in MELODY.items():
            for idx, (name, duration_eighths, velocity, offset_eighths) in enumerate(events):
                start = cycle_offset_s + bar * bar_s + offset_eighths * eighth_s
                duration = duration_eighths * eighth_s
                add_note(mix, name, start, duration * 0.88, sr, "flute", 0.085 + (velocity - 45) / 360.0, 0.31, 3000 + bar * 10 + idx)
                if cycle == 1:
                    notes.append(MidiNote("Breathy wooden flute", 2, 73, note_number(name), bar * 3.0 + offset_eighths * 0.5, duration_eighths * 0.44, velocity))

        metal_events = {1: ("D5", 0.25), 7: ("Eb5", 0.45), 12: ("A4", 0.1), 17: ("D5", 0.55), 21: ("Bb4", 0.25), 25: ("Eb5", 0.6), 30: ("A4", 0.0), 33: ("D5", 0.4)}
        for bar, (name, pos) in metal_events.items():
            start = cycle_offset_s + bar * bar_s + (0.5 if bar % 2 else 0.0) * beat_s
            add_note(mix, name, start, 1.2, sr, "metal", 0.043, pos, 4000 + bar)
            if cycle == 1:
                notes.append(MidiNote("Distant metal", 3, 14, note_number(name), bar * 3.0, 1.1, 31))

        for bar in (9, 11, 14, 17, 19, 21, 23, 25):
            for pulse, gain in ((0.0, 0.057), (1.5, 0.038)):
                start = cycle_offset_s + bar * bar_s + pulse * beat_s
                add(mix, round(start * sr), pan(frame_drum(0.58, sr, 5000 + bar * 4 + round(pulse * 2)), -0.05), gain)
                if cycle == 1:
                    notes.append(MidiNote("Sparse frame drum", 9, 0, 36, bar * 3.0 + pulse, 0.22, 30 if pulse else 36))

    # Deterministic repeating air layer. Build one cycle, tile it, then low-pass by a short moving average.
    rng = np.random.default_rng(75034)
    air_cycle = rng.standard_normal(cycle_samples).astype(np.float32)
    air_cycle = np.convolve(air_cycle, np.ones(384, dtype=np.float32) / 384.0, mode="same")
    phase = np.linspace(0.0, 2.0 * math.pi, cycle_samples, endpoint=False, dtype=np.float32)
    air_cycle *= (0.35 + 0.65 * (0.5 + 0.5 * np.sin(phase * 5.0 + 0.4))).astype(np.float32)
    air = np.tile(air_cycle, 3)
    mix += pan(air, -0.12) * 0.013

    # Room reflections are allowed to spill from the previous cycle into the exported middle cycle.
    dry = mix.copy()
    for delay_s, gain, cross in ((0.113, 0.13, True), (0.227, 0.095, False), (0.421, 0.064, True), (0.733, 0.038, False)):
        shift = round(delay_s * sr)
        if cross:
            mix[shift:, 0] += dry[:-shift, 1] * gain
            mix[shift:, 1] += dry[:-shift, 0] * gain
        else:
            mix[shift:] += dry[:-shift] * gain

    cycle = mix[cycle_samples:2 * cycle_samples].copy()
    cycle -= np.mean(cycle, axis=0, keepdims=True)

    # Short symmetric edge taper prevents a discontinuity in native Ogg looping.
    # The 80 ms window is masked by the persistent room layer and does not alter form.
    edge_samples = round(0.08 * sr)
    edge = np.sin(np.linspace(0.0, math.pi / 2.0, edge_samples, endpoint=True, dtype=np.float32)) ** 2
    cycle[:edge_samples] *= edge[:, None]
    cycle[-edge_samples:] *= edge[::-1, None]

    # Gentle saturating master, normalized below clipping.
    pre_peak = float(np.max(np.abs(cycle))) or 1.0
    cycle = np.tanh(cycle / max(pre_peak, 0.82) * 1.12).astype(np.float32)
    peak = float(np.max(np.abs(cycle))) or 1.0
    cycle *= np.float32(0.69 / peak)  # about -3.22 dBFS

    output.mkdir(parents=True, exist_ok=True)
    wav_path = output / "exploration_tension_v01_master.wav"
    pcm = np.clip(cycle * 32767.0, -32768, 32767).astype("<i2")
    # Supported Linux runners may differ by one final int16 LSB
    # in a negligible number of samples. The signed high-byte hash
    # remains a strict and stable cross-platform waveform fingerprint.
    pcm_signature_shift_bits = 8
    pcm_signature = (pcm.astype(np.int32) >> pcm_signature_shift_bits).astype("<i2")
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sr)
        wav_file.writeframes(pcm.tobytes())

    midi_path = output / "exploration_tension_v01.mid"
    write_midi(midi_path, bpm, notes)

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required")
    ogg_path = output / "exploration_tension_v01_master.ogg"
    mp3_path = output / "exploration_tension_v01_preview.mp3"
    subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path), "-c:a", "libvorbis", "-q:a", "5", str(ogg_path)], check=True)
    subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path), "-c:a", "libmp3lame", "-b:a", "192k", str(mp3_path)], check=True)

    sample_peak = float(np.max(np.abs(cycle)))
    rms = math.sqrt(float(np.mean(cycle * cycle)) + 1e-12)
    manifest = {
        "schema_version": 1,
        "composition_id": score["composition_id"],
        "render_id": "exploration_tension_v01_master_candidate_01",
        "status": "integrated_master_candidate",
        "renderer": "procedural_tension_renderer_v01",
        "numpy_version": REQUIRED_NUMPY_VERSION,
        "external_samples_used": False,
        "sample_rate": sr,
        "channels": 2,
        "tempo_bpm": bpm,
        "time_signature": score["time_signature"],
        "bars": bars,
        "duration_seconds": round(len(cycle) / sr, 6),
        "midi_note_count": len(notes),
        "peak_dbfs": round(20.0 * math.log10(max(sample_peak, 1e-12)), 3),
        "rms_dbfs": round(20.0 * math.log10(max(rms, 1e-12)), 3),
        "boundary_value_delta": round(float(np.max(np.abs(cycle[0] - cycle[-1]))), 8),
        "boundary_slope_delta": round(float(np.max(np.abs((cycle[1] - cycle[0]) - (cycle[-1] - cycle[-2])))), 8),
        "ogg_bytes": ogg_path.stat().st_size,
        "ogg_sha256": hashlib.sha256(ogg_path.read_bytes()).hexdigest(),
        "wav_sha256": hashlib.sha256(wav_path.read_bytes()).hexdigest(),
        "pcm_signature_shift_bits": pcm_signature_shift_bits,
        "pcm_signature_sha256": hashlib.sha256(pcm_signature.tobytes()).hexdigest(),
        "midi_sha256": hashlib.sha256(midi_path.read_bytes()).hexdigest(),
        "source_score_sha256": hashlib.sha256(json.dumps(score, sort_keys=True).encode("utf-8")).hexdigest()
    }
    manifest_path = output / "exploration_tension_v01_master_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
