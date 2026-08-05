#!/usr/bin/env python3
"""Render exploration_tension_v01 revision 2 ("Danger closer").

The cue is original deterministic procedural synthesis. No recordings, sample
packs, or imported MIDI are used. NumPy is pinned because the waveform contract
is validated across GitHub runner images.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REQUIRED_NUMPY_VERSION = "2.3.5"
SR = 48000
BPM = 75
BARS = 34
BAR_SECONDS = 60.0 / BPM * 3.0
DURATION = BARS * BAR_SECONDS
PPQ = 480

NOTE_PC = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}


def midi_note(name: str) -> int:
    pitch = name[:2] if len(name) > 2 and name[1] in "#b" else name[0]
    octave = int(name[len(pitch):])
    return 12 * (octave + 1) + NOTE_PC[pitch]


def hz(name: str) -> float:
    return 440.0 * 2.0 ** ((midi_note(name) - 69) / 12.0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def env(length: int, attack: float, release: float, sustain: float = 1.0) -> np.ndarray:
    result = np.full(length, sustain, np.float32)
    attack_samples = min(length, max(1, int(attack * SR)))
    release_samples = min(length, max(1, int(release * SR)))
    result[:attack_samples] *= np.sin(
        np.linspace(0.0, math.pi / 2.0, attack_samples, endpoint=False, dtype=np.float32)
    ) ** 2
    result[-release_samples:] *= np.cos(
        np.linspace(0.0, math.pi / 2.0, release_samples, endpoint=False, dtype=np.float32)
    ) ** 2
    return result


def pan(signal: np.ndarray, position: float) -> np.ndarray:
    position = max(-1.0, min(1.0, position))
    angle = (position + 1.0) * math.pi / 4.0
    return np.column_stack((signal * math.cos(angle), signal * math.sin(angle))).astype(np.float32)


def add(mix: np.ndarray, start_s: float, signal: np.ndarray, gain: float, position: float = 0.0) -> None:
    start = max(0, round(start_s * SR))
    stereo = pan(signal, position)
    end = min(len(mix), start + len(signal))
    if end > start:
        mix[start:end] += stereo[:end - start] * gain


def bowed(note: str, duration: float, seed: int, grit: float = 0.025, tremolo: float = 0.0) -> np.ndarray:
    length = max(1, round(duration * SR))
    time = np.arange(length, dtype=np.float32) / SR
    frequency = hz(note)
    phase = 2.0 * math.pi * frequency * time + 0.002 * np.sin(2.0 * math.pi * 4.8 * time)
    signal = np.sin(phase) + 0.34 * np.sin(2.0 * phase + 0.17) + 0.12 * np.sin(3.0 * phase + 0.31)
    if tremolo > 0.0:
        signal *= 0.78 + 0.22 * np.sin(2.0 * math.pi * tremolo * time + 0.5)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(length).astype(np.float32)
    noise = np.convolve(noise, np.ones(24, dtype=np.float32) / 24.0, mode="same")
    signal += grit * noise
    signal *= env(length, 0.22, 0.48, 0.84)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def pluck(note: str, duration: float, seed: int, brightness: float = 1.0) -> np.ndarray:
    length = max(1, round(duration * SR))
    time = np.arange(length, dtype=np.float32) / SR
    frequency = hz(note)
    phase = 2.0 * math.pi * frequency * time
    signal = np.sin(phase) + 0.48 * brightness * np.sin(2.0 * phase) + 0.20 * brightness * np.sin(3.0 * phase)
    rng = np.random.default_rng(seed)
    signal += 0.015 * rng.standard_normal(length).astype(np.float32) * np.exp(-time * 18.0)
    signal *= np.exp(-time * (4.6 + 0.0015 * frequency)).astype(np.float32)
    signal *= env(length, 0.003, min(0.11, duration * 0.35), 1.0)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def flute(note: str, duration: float, seed: int) -> np.ndarray:
    length = max(1, round(duration * SR))
    time = np.arange(length, dtype=np.float32) / SR
    frequency = hz(note)
    rng = np.random.default_rng(seed)
    breath = rng.standard_normal(length).astype(np.float32)
    breath = np.convolve(breath, np.ones(72, dtype=np.float32) / 72.0, mode="same")
    phase = 2.0 * math.pi * frequency * time + 0.010 * np.sin(2.0 * math.pi * 5.1 * time)
    signal = np.sin(phase) + 0.10 * np.sin(2.0 * phase) + 0.032 * breath
    signal *= env(length, 0.08, 0.25, 0.78)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def drum(duration: float, seed: int, pitch: float = 42.0) -> np.ndarray:
    length = max(1, round(duration * SR))
    time = np.arange(length, dtype=np.float32) / SR
    frequency = pitch + 52.0 * np.exp(-time * 8.0)
    phase = 2.0 * math.pi * np.cumsum(frequency) / SR
    rng = np.random.default_rng(seed)
    skin = rng.standard_normal(length).astype(np.float32)
    skin = np.convolve(skin, np.ones(10, dtype=np.float32) / 10.0, mode="same")
    signal = np.sin(phase) * np.exp(-time * 7.2) + 0.13 * skin * np.exp(-time * 23.0)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def metal(frequency: float, duration: float) -> np.ndarray:
    length = max(1, round(duration * SR))
    time = np.arange(length, dtype=np.float32) / SR
    signal = np.zeros(length, np.float32)
    for ratio, gain, decay in ((1.0, 1.0, 0.95), (1.47, 0.52, 1.2), (2.11, 0.31, 1.55), (3.23, 0.17, 1.9), (4.91, 0.08, 2.5)):
        signal += gain * np.sin(2.0 * math.pi * frequency * ratio * time + ratio * 0.19) * np.exp(-time * decay)
    signal *= env(length, 0.005, min(0.65, duration * 0.35), 1.0)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def air_bed(length: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(length).astype(np.float32)
    smooth = np.convolve(noise, np.ones(240, dtype=np.float32) / 240.0, mode="same")
    time = np.arange(length, dtype=np.float32) / SR
    smooth *= 0.60 + 0.40 * np.sin(2.0 * math.pi * time / DURATION * 3.0 + 0.7) ** 2
    return smooth / (np.max(np.abs(smooth)) + 1e-9)


def delay_reverb(stereo: np.ndarray) -> np.ndarray:
    result = stereo.copy()
    for delay, gain, cross in ((0.071, 0.12, False), (0.113, 0.085, True), (0.181, 0.055, False), (0.293, 0.035, True)):
        offset = int(delay * SR)
        if cross:
            result[offset:, 0] += stereo[:-offset, 1] * gain
            result[offset:, 1] += stereo[:-offset, 0] * gain
        else:
            result[offset:] += stereo[:-offset] * gain
    return result


@dataclass
class MidiEvt:
    note: int
    start: float
    dur: float
    vel: int
    ch: int = 0


def varlen(value: int) -> bytes:
    output = [value & 0x7F]
    value >>= 7
    while value:
        output.insert(0, (value & 0x7F) | 0x80)
        value >>= 7
    return bytes(output)


def write_midi(path: Path, events_source: list[MidiEvt]) -> None:
    tempo = round(60_000_000 / BPM)
    conductor = b"\x00\xff\x51\x03" + tempo.to_bytes(3, "big") + b"\x00\xff\x58\x04\x06\x03\x18\x08\x00\xff\x2f\x00"
    chunks = [b"MTrk" + struct.pack(">I", len(conductor)) + conductor]
    events: list[tuple[int, bytes]] = []
    for event in events_source:
        start = round(event.start * PPQ)
        end = round((event.start + event.dur) * PPQ)
        events.append((start, bytes([0x90 | event.ch, event.note, event.vel])))
        events.append((end, bytes([0x80 | event.ch, event.note, 0])))
    events.sort(key=lambda item: (item[0], 0 if item[1][0] & 0xF0 == 0x80 else 1))
    payload = bytearray(b"\x00\xff\x03\x0eTension rev02\x00\xc0\x30")
    previous = 0
    for tick, message in events:
        payload += varlen(tick - previous) + message
        previous = tick
    payload += b"\x00\xff\x2f\x00"
    chunks.append(b"MTrk" + struct.pack(">I", len(payload)) + bytes(payload))
    path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQ) + b"".join(chunks))


def render(score_path: Path, output: Path) -> dict[str, object]:
    if np.__version__ != REQUIRED_NUMPY_VERSION:
        raise RuntimeError(f"NumPy {REQUIRED_NUMPY_VERSION} is required, got {np.__version__}")
    score = json.loads(score_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    length = round(DURATION * SR)
    mix = np.zeros((length, 2), np.float32)
    midi: list[MidiEvt] = []
    harmony = [
        ("D2", "A2"), ("D2", "Eb2"), ("D2", "A2"), ("Eb2", "A2"), ("D2", "Bb1"), ("A1", "Eb2"), ("D2", "A2"), ("D2", "Eb2"),
        ("D2", "A2"), ("G1", "D2"), ("Eb2", "Bb1"), ("A1", "Eb2"), ("D2", "A2"), ("Bb1", "E2"), ("C2", "Gb2"), ("A1", "Eb2"), ("D2", "A2"),
        ("Eb2", "A2"), ("F1", "B1"), ("G1", "Db2"), ("A1", "Eb2"), ("D2", "A2"), ("Bb1", "E2"), ("Eb2", "A2"), ("A1", "Eb2"), ("D2", "A2"),
        ("G1", "Db2"), ("Eb2", "A2"), ("D2", "Eb2"), ("D2", "C2"), ("Bb1", "E2"), ("A1", "Eb2"), ("D2", "A2"), ("D2", "Eb2"),
    ]
    ostinato = ["D3", "D3", "Eb3", "D3", "A2", "D3"]
    flute_events = {
        2: ["D4", "Eb4", "D4"], 6: ["A3", "C4", "Eb4"], 10: ["D4", "Eb4", "F4"],
        14: ["E4", "Eb4", "D4"], 18: ["D4", "Eb4", "A4"], 20: ["A4", "Bb4", "Eb4"],
        22: ["D4", "C4", "Eb4"], 24: ["F4", "E4", "Eb4"], 28: ["D4", "Eb4", "D4"], 32: ["Eb4", "D4"],
    }
    for bar, (root, pressure) in enumerate(harmony):
        start = bar * BAR_SECONDS
        intensity = 0.82 if bar < 8 else 0.98 if bar < 17 else 1.18 if bar < 26 else 1.02
        add(mix, start, bowed(root, BAR_SECONDS + 0.42, 1000 + bar, tremolo=2.1 if bar >= 8 else 1.25), 0.105 * intensity, -0.20)
        add(mix, start, bowed(pressure, BAR_SECONDS + 0.42, 1100 + bar, grit=0.032, tremolo=2.65 if bar >= 17 else 1.8), 0.070 * intensity, 0.17)
        midi += [MidiEvt(midi_note(root), bar * 3.0, 2.9, 46), MidiEvt(midi_note(pressure), bar * 3.0, 2.9, 39)]

        positions = [0, 3] if bar < 5 else [0, 2, 3, 5] if bar < 17 else [0, 1, 3, 4, 5]
        if bar >= 27:
            positions = [0, 2, 3, 5]
        for index, position in enumerate(positions):
            note = ostinato[(bar + index) % len(ostinato)]
            gain = 0.050 if bar < 8 else 0.066 if bar < 17 else 0.083 if bar < 26 else 0.063
            add(mix, start + position * (BAR_SECONDS / 6.0), pluck(note, 0.48, 2000 + bar * 10 + position, 1.05), gain, -0.28 if index % 2 == 0 else 0.28)
            midi.append(MidiEvt(midi_note(note), bar * 3.0 + position * 0.5, 0.34, 49 if bar < 17 else 58, 1))

        if bar in {3, 7, 11, 15, 17, 19, 21, 23, 25, 29, 31}:
            add(mix, start, drum(0.85, 3000 + bar, 40.0), 0.12 if bar < 17 else 0.17, -0.04)
            midi.append(MidiEvt(36, bar * 3.0, 0.20, 48 if bar < 17 else 65, 9))
            if 17 <= bar <= 25:
                add(mix, start + 0.66, drum(0.62, 3100 + bar, 46.0), 0.105, 0.06)
                midi.append(MidiEvt(36, bar * 3.0 + 0.825, 0.16, 55, 9))

        if bar in {6, 8, 12, 16, 18, 20, 22, 24, 26, 30, 32}:
            duration = 1.45 if bar < 17 else 1.8
            add(mix, start + 1.05, bowed("D4", duration, 4000 + bar, grit=0.012, tremolo=5.3), 0.034 if bar < 17 else 0.050, -0.42)
            add(mix, start + 1.05, bowed("Eb4", duration, 4100 + bar, grit=0.012, tremolo=5.6), 0.031 if bar < 17 else 0.047, 0.42)
            if 17 <= bar <= 25:
                add(mix, start + 1.10, bowed("A4", duration, 4200 + bar, grit=0.009, tremolo=6.1), 0.022, 0.0)

        if bar in flute_events:
            sequence = flute_events[bar]
            for index, note in enumerate(sequence):
                relative = [0.20, 0.44, 0.68][index] if len(sequence) == 3 else [0.34, 0.62][index]
                event_start = start + relative * BAR_SECONDS
                duration = 0.52 if bar < 17 else 0.42
                add(mix, event_start, flute(note, duration, 5000 + bar * 10 + index), 0.052 if bar < 17 else 0.066, 0.24 if index % 2 == 0 else -0.18)
                midi.append(MidiEvt(midi_note(note), event_start / (60.0 / BPM), duration / (60.0 / BPM), 54 if bar < 17 else 62, 2))

        if bar in {7, 15, 23, 31}:
            add(mix, start + 1.55, metal(117.0 if bar < 17 else 103.0, 3.5), 0.075 if bar < 17 else 0.098, 0.35 if bar % 2 else -0.35)

    for bar in range(18, 26, 2):
        start = bar * BAR_SECONDS
        for index, note in enumerate(["A4", "Bb4", "A4", "Eb5"]):
            add(mix, start + index * 0.42, bowed(note, 0.55, 7000 + bar * 10 + index, grit=0.010, tremolo=7.2), 0.020 + index * 0.003, -0.48 + index * 0.32)

    mix += pan(air_bed(length, 9001), 0.05) * 0.022
    time = np.arange(length, dtype=np.float32) / SR
    sub = np.sin(2.0 * math.pi * 36.71 * time) * (0.5 + 0.5 * np.sin(2.0 * math.pi * time / (BAR_SECONDS * 2.0) - 1.1)) ** 4
    mix += pan(sub.astype(np.float32), 0.0) * 0.018
    mix = delay_reverb(mix)
    mix = np.tanh(mix * 1.14).astype(np.float32)
    peak = float(np.max(np.abs(mix)))
    mix *= 10.0 ** (-1.8 / 20.0) / (peak + 1e-9)

    edge_samples = round(0.045 * SR)
    edge = np.sin(np.linspace(0.0, math.pi / 2.0, edge_samples, dtype=np.float32)) ** 2
    mix[:edge_samples] *= edge[:, None]
    mix[-edge_samples:] *= edge[::-1, None]

    wav_path = output / "exploration_tension_v01_master.wav"
    pcm = np.clip(mix, -1.0, 1.0)
    pcm16 = np.round(pcm * 32767.0).astype("<i2")
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SR)
        wav_file.writeframes(pcm16.tobytes())

    ogg_path = output / "exploration_tension_v01_master.ogg"
    mp3_path = output / "exploration_tension_v01_preview.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path), "-c:a", "libvorbis", "-q:a", "6", str(ogg_path)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path), "-c:a", "libmp3lame", "-b:a", "256k", str(mp3_path)], check=True)
    midi_path = output / "exploration_tension_v01.mid"
    write_midi(midi_path, midi)

    rms = float(np.sqrt(np.mean(mix.astype(np.float64) ** 2)))
    peak = float(np.max(np.abs(mix)))
    signature_shift = 8
    signature_bytes = (pcm16.astype(np.int32) >> signature_shift).astype(np.int8).tobytes()
    manifest: dict[str, object] = {
        "schema_version": 1,
        "composition_id": "exploration_tension_v01",
        "title_ru": "Тени рядом",
        "render_id": "exploration_tension_v01_master_candidate_02",
        "status": "integrated_master_candidate",
        "renderer": "procedural_tension_renderer_v02",
        "arrangement_revision": 2,
        "danger_density_pass": "approved_2026-08-06",
        "numpy_version": REQUIRED_NUMPY_VERSION,
        "external_samples_used": False,
        "sample_rate": SR,
        "channels": 2,
        "tempo_bpm": BPM,
        "time_signature": [6, 8],
        "bars": BARS,
        "duration_seconds": round(DURATION, 6),
        "midi_note_count": len(midi),
        "peak_dbfs": round(20.0 * math.log10(peak + 1e-12), 3),
        "rms_dbfs": round(20.0 * math.log10(rms + 1e-12), 3),
        "boundary_value_delta": round(float(np.max(np.abs(mix[0] - mix[-1]))), 8),
        "boundary_slope_delta": round(float(np.max(np.abs((mix[1] - mix[0]) - (mix[-1] - mix[-2])))), 8),
        "ogg_bytes": ogg_path.stat().st_size,
        "ogg_sha256": sha256(ogg_path),
        "wav_sha256": sha256(wav_path),
        "midi_sha256": sha256(midi_path),
        "source_score_sha256": hashlib.sha256(json.dumps(score, sort_keys=True).encode("utf-8")).hexdigest(),
        "pcm_signature_shift_bits": signature_shift,
        "pcm_signature_sha256": hashlib.sha256(signature_bytes).hexdigest(),
        "change_scope": [
            "stronger low-string pulse",
            "minor-second and tritone pressure",
            "controlled double heartbeat accents",
            "denser near-contact section",
        ],
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
