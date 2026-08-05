#!/usr/bin/env python3
"""Generate the original main-theme prototype for Chronicles of the Wanderer.

Outputs a deterministic MIDI source, a 48 kHz stereo WAV mock-up and, when
ffmpeg is available, an Ogg Vorbis game preview. The synthesis deliberately
uses no downloaded samples, so the musical material and rendered prototype are
fully reproducible from this repository.
"""

from __future__ import annotations

import argparse
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
    "Bbmaj7": ["Bb1", "F2", "Bb2", "D3", "A3"],
    "Csus2": ["C2", "G2", "C3", "D3", "G3"],
    "Dm": ["D2", "A2", "D3", "F3", "A3"],
    "Gm": ["G1", "D2", "G2", "Bb2", "D3"],
    "Bb": ["Bb1", "F2", "Bb2", "D3", "F3"],
    "A5(b9)": ["A1", "E2", "A2", "Bb2", "E3"],
    "C": ["C2", "G2", "C3", "E3", "G3"],
    "A": ["A1", "E2", "A2", "C#3", "E3"],
    "Dm/F": ["F1", "A2", "D3", "F3", "A3"],
    "Eb": ["Eb2", "Bb2", "Eb3", "G3", "Bb3"],
    "Asus4": ["A1", "E2", "A2", "D3", "E3"],
    "F": ["F1", "C2", "F2", "A2", "C3"],
    "C/E": ["E1", "G2", "C3", "E3", "G3"],
}

MELODY_BARS: list[list[tuple[str, int, int]]] = [
    [],
    [],
    [("D4", 2, 72), ("A3", 1, 64), ("C4", 1, 67), ("Eb4", 1, 70), ("D4", 1, 66)],
    [("F4", 2, 66), ("E4", 1, 62), ("D4", 3, 65)],
    [("G4", 2, 69), ("D4", 1, 63), ("F4", 1, 66), ("A4", 1, 70), ("G4", 1, 64)],
    [("F4", 2, 66), ("D4", 1, 61), ("C4", 1, 62), ("D4", 2, 66)],
    [("E4", 1, 62), ("F4", 1, 65), ("E4", 1, 61), ("D4", 1, 63), ("C#4", 2, 65)],
    [("D4", 6, 68)],
    [("D4", 2, 76), ("A3", 1, 68), ("C4", 1, 71), ("E4", 1, 73), ("D4", 1, 70)],
    [("G4", 2, 70), ("E4", 1, 65), ("D4", 1, 65), ("C4", 2, 68)],
    [("F4", 1, 67), ("G4", 1, 70), ("A4", 2, 74), ("F4", 2, 68)],
    [("E4", 1, 65), ("D4", 1, 64), ("C#4", 2, 68), ("A3", 2, 61)],
    [("G4", 2, 72), ("Bb4", 1, 74), ("A4", 1, 70), ("G4", 2, 68)],
    [("F4", 2, 68), ("E4", 1, 64), ("D4", 3, 67)],
    [("Eb4", 2, 72), ("Bb3", 1, 65), ("D4", 1, 68), ("F4", 2, 71)],
    [("E4", 1, 65), ("D4", 1, 63), ("C#4", 2, 69), ("A3", 2, 62)],
    [("A4", 2, 75), ("F4", 1, 67), ("G4", 1, 70), ("A4", 2, 73)],
    [("G4", 2, 69), ("E4", 1, 64), ("D4", 1, 65), ("C4", 2, 66)],
    [("D4", 1, 65), ("F4", 1, 68), ("A4", 2, 74), ("C5", 2, 76)],
    [("Bb4", 2, 72), ("A4", 1, 67), ("F4", 1, 66), ("D4", 2, 64)],
    [("G4", 1, 68), ("A4", 1, 71), ("Bb4", 2, 73), ("G4", 2, 67)],
    [("F4", 2, 67), ("E4", 1, 63), ("D4", 3, 66)],
    [("Eb4", 1, 70), ("F4", 1, 72), ("G4", 2, 74), ("Bb4", 2, 75)],
    [("A4", 1, 71), ("G4", 1, 67), ("E4", 1, 64), ("C#4", 1, 66), ("A3", 2, 61)],
    [("D4", 2, 78), ("A3", 1, 69), ("C4", 1, 72), ("Eb4", 1, 74), ("D4", 1, 71)],
    [("F4", 2, 70), ("D4", 1, 64), ("C4", 1, 65), ("Bb3", 2, 63)],
    [("E4", 1, 65), ("G4", 1, 69), ("A4", 2, 73), ("G4", 2, 68)],
    [("F4", 2, 68), ("E4", 1, 64), ("D4", 3, 68)],
    [("G4", 2, 70), ("D4", 1, 63), ("F4", 1, 67), ("A4", 2, 72)],
    [("Eb4", 2, 70), ("D4", 1, 64), ("C4", 1, 62), ("Bb3", 2, 60)],
    [("E4", 1, 63), ("D4", 1, 62), ("C#4", 2, 66), ("A3", 2, 59)],
    [("D4", 6, 65)],
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
    if len(name) < 2:
        raise ValueError(f"Invalid note: {name}")
    if name[1] in ("#", "b"):
        pitch_name, octave_text = name[:2], name[2:]
    else:
        pitch_name, octave_text = name[:1], name[1:]
    return 12 * (int(octave_text) + 1) + NOTE_TO_SEMITONE[pitch_name]


def frequency(name: str) -> float:
    return 440.0 * (2.0 ** ((note_number(name) - 69) / 12.0))


def envelope(length: int, sample_rate: int, attack: float, release: float, sustain: float = 1.0) -> np.ndarray:
    env = np.full(length, sustain, dtype=np.float64)
    a = min(length, max(1, int(attack * sample_rate)))
    r = min(length, max(1, int(release * sample_rate)))
    env[:a] *= np.sin(np.linspace(0.0, math.pi / 2.0, a, endpoint=False)) ** 2
    env[-r:] *= np.cos(np.linspace(0.0, math.pi / 2.0, r, endpoint=False)) ** 2
    return env


def oscillator(freq: float, seconds: float, sample_rate: int, kind: str, seed: int = 0) -> np.ndarray:
    n = max(1, int(seconds * sample_rate))
    t = np.arange(n, dtype=np.float64) / sample_rate
    rng = np.random.default_rng(seed)
    if kind == "bowed":
        vibrato = 0.0035 * np.sin(2.0 * math.pi * 5.1 * t)
        phase = 2.0 * math.pi * freq * t + vibrato
        signal = (
            np.sin(phase)
            + 0.42 * np.sin(2.0 * phase + 0.17)
            + 0.19 * np.sin(3.0 * phase + 0.31)
            + 0.09 * np.sin(5.0 * phase)
        )
        signal += 0.012 * rng.standard_normal(n)
        signal *= envelope(n, sample_rate, 0.18, 0.35, 0.85)
    elif kind == "flute":
        vibrato = 0.012 * np.sin(2.0 * math.pi * 5.4 * t)
        phase = 2.0 * math.pi * freq * t + vibrato
        breath = rng.standard_normal(n)
        breath = np.convolve(breath, np.ones(48) / 48.0, mode="same")
        signal = np.sin(phase) + 0.16 * np.sin(2.0 * phase) + 0.035 * breath
        signal *= envelope(n, sample_rate, 0.08, 0.22, 0.92)
    elif kind == "pluck":
        phase = 2.0 * math.pi * freq * t
        decay = np.exp(-t * (2.4 + 0.002 * freq))
        signal = (
            np.sin(phase)
            + 0.55 * np.sin(2.0 * phase)
            + 0.25 * np.sin(3.0 * phase)
            + 0.12 * np.sin(5.0 * phase)
        ) * decay
        signal *= envelope(n, sample_rate, 0.005, min(0.16, seconds * 0.4), 1.0)
    elif kind == "choir":
        detunes = (-0.006, -0.002, 0.002, 0.006)
        signal = np.zeros(n, dtype=np.float64)
        for detune in detunes:
            phase = 2.0 * math.pi * freq * (1.0 + detune) * t
            signal += np.sin(phase) + 0.18 * np.sin(2.0 * phase)
        signal /= len(detunes)
        signal *= envelope(n, sample_rate, 0.65, 0.75, 0.72)
    elif kind == "bell":
        partials = ((1.0, 1.0), (2.01, 0.48), (2.94, 0.27), (4.18, 0.16), (5.43, 0.09))
        signal = np.zeros(n, dtype=np.float64)
        for ratio, gain in partials:
            signal += gain * np.sin(2.0 * math.pi * freq * ratio * t) * np.exp(-t * (1.25 + ratio * 0.18))
        signal *= envelope(n, sample_rate, 0.003, 0.4, 1.0)
    else:
        raise ValueError(kind)
    peak = float(np.max(np.abs(signal))) or 1.0
    return signal / peak


def drum(seconds: float, sample_rate: int, seed: int) -> np.ndarray:
    n = max(1, int(seconds * sample_rate))
    t = np.arange(n, dtype=np.float64) / sample_rate
    rng = np.random.default_rng(seed)
    pitch = 62.0 * np.exp(-t * 4.5) + 37.0
    phase = 2.0 * math.pi * np.cumsum(pitch) / sample_rate
    body = np.sin(phase) * np.exp(-t * 5.4)
    skin = rng.standard_normal(n)
    skin = np.convolve(skin, np.ones(16) / 16.0, mode="same") * np.exp(-t * 16.0)
    signal = body + 0.24 * skin
    peak = float(np.max(np.abs(signal))) or 1.0
    return signal / peak


def pan_mono(signal: np.ndarray, pan: float) -> np.ndarray:
    pan = max(-1.0, min(1.0, pan))
    angle = (pan + 1.0) * math.pi / 4.0
    return np.column_stack((signal * math.cos(angle), signal * math.sin(angle)))


def add_audio(target: np.ndarray, start: int, stereo: np.ndarray, gain: float) -> None:
    total = target.shape[0]
    if start >= total:
        return
    end = min(total, start + stereo.shape[0])
    if end > start:
        target[start:end] += stereo[: end - start] * gain


def add_note(
    target: np.ndarray,
    note: str,
    start_seconds: float,
    duration_seconds: float,
    sample_rate: int,
    kind: str,
    gain: float,
    pan: float,
    seed: int,
) -> None:
    tail = 0.45 if kind in ("bowed", "flute") else 0.85 if kind in ("choir", "bell") else 0.18
    mono = oscillator(frequency(note), duration_seconds + tail, sample_rate, kind, seed)
    add_audio(target, int(start_seconds * sample_rate), pan_mono(mono, pan), gain)


def circular_room(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    wet = np.zeros_like(audio)
    taps = ((0.137, 0.15), (0.233, 0.11), (0.389, 0.085), (0.617, 0.06), (0.947, 0.035))
    for delay_seconds, gain in taps:
        shift = int(delay_seconds * sample_rate)
        wet[:, 0] += np.roll(audio[:, 1], shift) * gain
        wet[:, 1] += np.roll(audio[:, 0], shift + 37) * gain
    return audio + wet


def soft_limit(audio: np.ndarray) -> np.ndarray:
    audio -= np.mean(audio, axis=0, keepdims=True)
    peak = float(np.max(np.abs(audio))) or 1.0
    audio = np.tanh(audio / max(0.9, peak) * 1.35)
    peak = float(np.max(np.abs(audio))) or 1.0
    return audio * (0.92 / peak)


def encode_varlen(value: int) -> bytes:
    buffer = value & 0x7F
    output = bytearray([buffer])
    while value > 0x7F:
        value >>= 7
        buffer = (value & 0x7F) | 0x80
        output.insert(0, buffer)
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
    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQ)
    path.write_bytes(header + b"".join(chunks))


def build_score(score: dict, output_dir: Path) -> tuple[Path, Path, Path | None]:
    sample_rate = int(score["sample_rate"])
    bpm = int(score["tempo_bpm"])
    bars = int(score["bars"])
    beat_seconds = 60.0 / bpm
    eighth_seconds = beat_seconds / 2.0
    bar_seconds = beat_seconds * 3.0
    total_seconds = bars * bar_seconds
    total_samples = round(total_seconds * sample_rate)
    mix = np.zeros((total_samples, 2), dtype=np.float64)
    midi_notes: list[MidiNote] = []

    harmony = score["harmony"]
    for bar_index, chord_name in enumerate(harmony):
        chord = CHORDS[chord_name]
        bar_start = bar_index * bar_seconds
        root = chord[0]
        fifth = chord[1]
        add_note(mix, root, bar_start, bar_seconds * 0.96, sample_rate, "bowed", 0.17, -0.16, 1000 + bar_index)
        add_note(mix, fifth, bar_start, bar_seconds * 0.96, sample_rate, "bowed", 0.12, 0.14, 1100 + bar_index)
        midi_notes.append(MidiNote("Low bowed strings", 0, 42, note_number(root), bar_index * 3.0, 2.9, 52))
        midi_notes.append(MidiNote("Low bowed strings", 0, 42, note_number(fifth), bar_index * 3.0, 2.9, 43))

        pattern = [0, 2, 1, 3, 2, 1]
        for step, chord_index in enumerate(pattern):
            note_name = chord[min(chord_index, len(chord) - 1)]
            start = bar_start + step * eighth_seconds
            add_note(mix, note_name, start, eighth_seconds * 0.82, sample_rate, "pluck", 0.095, -0.42, 2000 + bar_index * 8 + step)
            midi_notes.append(MidiNote("Dark plucked strings", 1, 46, note_number(note_name), bar_index * 3.0 + step * 0.5, 0.42, 42 + (step % 2) * 5))

        if 8 <= bar_index <= 30:
            for choir_note in chord[2:5]:
                add_note(mix, choir_note, bar_start, bar_seconds * 0.92, sample_rate, "choir", 0.055, 0.22, 3000 + bar_index * 6 + note_number(choir_note))
                midi_notes.append(MidiNote("Low wordless choir", 2, 52, note_number(choir_note), bar_index * 3.0, 2.75, 34))

    for bar_index, events in enumerate(MELODY_BARS):
        cursor_eighths = 0
        for event_index, (note_name, duration_eighths, velocity) in enumerate(events):
            start = bar_index * bar_seconds + cursor_eighths * eighth_seconds
            duration = duration_eighths * eighth_seconds
            gain = 0.17 + (velocity - 60) / 180.0
            add_note(mix, note_name, start, duration * 0.91, sample_rate, "flute", gain, 0.30, 4000 + bar_index * 16 + event_index)
            midi_notes.append(MidiNote("Wooden flute", 3, 73, note_number(note_name), bar_index * 3.0 + cursor_eighths * 0.5, duration_eighths * 0.5 * 0.91, velocity))
            cursor_eighths += duration_eighths

    bell_bars = {0: "D5", 7: "A4", 15: "A4", 16: "F5", 23: "A4", 24: "D5", 31: "D5"}
    for bar_index, note_name in bell_bars.items():
        start = bar_index * bar_seconds + (0.15 if bar_index != 31 else 0.0)
        add_note(mix, note_name, start, 1.5, sample_rate, "bell", 0.075, 0.56, 5000 + bar_index)
        midi_notes.append(MidiNote("Distant bells", 4, 14, note_number(note_name), bar_index * 3.0, 1.3, 46))

    for bar_index in range(16, 31):
        for beat in (0.0, 1.5):
            start = bar_index * bar_seconds + beat * beat_seconds
            mono = drum(0.65, sample_rate, 6000 + bar_index * 4 + int(beat * 2))
            add_audio(mix, int(start * sample_rate), pan_mono(mono, -0.04), 0.10 if beat == 0.0 else 0.065)
            midi_notes.append(MidiNote("Frame drum", 9, 0, 36, bar_index * 3.0 + beat, 0.25, 46 if beat == 0.0 else 36))

    rng = np.random.default_rng(76032)
    room = rng.standard_normal(total_samples)
    room = np.convolve(room, np.ones(512) / 512.0, mode="same")
    slow = np.sin(np.linspace(0.0, math.pi * 8.0, total_samples, endpoint=False)) * 0.5 + 0.5
    mix += pan_mono(room * slow, -0.12) * 0.012

    mix = circular_room(mix, sample_rate)

    edge_samples = int(sample_rate * 0.09)
    edge = np.sin(np.linspace(0.0, math.pi / 2.0, edge_samples)) ** 2
    mix[:edge_samples] *= edge[:, None]
    mix[-edge_samples:] *= edge[::-1, None]
    mix = soft_limit(mix)

    output_dir.mkdir(parents=True, exist_ok=True)
    wav_path = output_dir / "main_theme_v01_mockup.wav"
    pcm = np.clip(mix * 32767.0, -32768, 32767).astype("<i2")
    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())

    midi_path = output_dir / "main_theme_v01.mid"
    write_midi(midi_path, bpm, midi_notes)

    ogg_path: Path | None = None
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        ogg_path = output_dir / "main_theme_v01.ogg"
        subprocess.run(
            [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path), "-c:a", "libvorbis", "-q:a", "5", str(ogg_path)],
            check=True,
        )

    manifest = {
        "composition_id": score["composition_id"],
        "duration_seconds": round(total_seconds, 6),
        "sample_rate": sample_rate,
        "channels": 2,
        "tempo_bpm": bpm,
        "bars": bars,
        "midi_note_count": len(midi_notes),
        "wav_file": wav_path.name,
        "ogg_file": ogg_path.name if ogg_path else None,
        "peak_pcm": int(np.max(np.abs(pcm))),
        "edge_fade_seconds": 0.09,
    }
    (output_dir / "main_theme_v01_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return midi_path, wav_path, ogg_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    score = json.loads(args.score.read_text(encoding="utf-8"))
    midi_path, wav_path, ogg_path = build_score(score, args.output)
    print(f"Generated {midi_path}")
    print(f"Generated {wav_path}")
    if ogg_path:
        print(f"Generated {ogg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
