#!/usr/bin/env python3
"""Render combat_start_v01 ("First Strike").

Original deterministic procedural synthesis for the project. No recordings,
sample packs, imported MIDI, or third-party melodies are used.
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
SR = 48_000
BPM = 96
DURATION_BEATS = 5.0
BEAT_SECONDS = 60.0 / BPM
DURATION = DURATION_BEATS * BEAT_SECONDS
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


def pan(signal: np.ndarray, position: float) -> np.ndarray:
    angle = (max(-1.0, min(1.0, position)) + 1.0) * math.pi / 4.0
    return np.column_stack((signal * math.cos(angle), signal * math.sin(angle))).astype(np.float32)


def add(mix: np.ndarray, start_seconds: float, signal: np.ndarray, gain: float, position: float = 0.0) -> None:
    start = max(0, round(start_seconds * SR))
    stereo = pan(signal, position)
    end = min(len(mix), start + len(stereo))
    if end > start:
        mix[start:end] += stereo[: end - start] * gain


def impact(duration: float, seed: int, base_frequency: float = 39.0) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    rng = np.random.default_rng(seed)
    frequency = base_frequency + 105.0 * np.exp(-t * 14.0)
    phase = 2.0 * math.pi * np.cumsum(frequency) / SR
    body = np.sin(phase) * np.exp(-t * 3.2)
    sub = 0.62 * np.sin(2.0 * math.pi * base_frequency * 0.5 * t + 0.25) * np.exp(-t * 2.3)
    noise = rng.standard_normal(length).astype(np.float32)
    noise = np.convolve(noise, np.ones(7, dtype=np.float32) / 7.0, mode="same")
    crack = 0.22 * noise * np.exp(-t * 25.0)
    signal = body + sub + crack
    signal *= np.minimum(1.0, t / 0.0025)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def brass_stab(note: str, duration: float, seed: int, force: float) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    f = hz(note)
    rng = np.random.default_rng(seed)
    jitter = rng.standard_normal(length).astype(np.float32)
    jitter = np.convolve(jitter, np.ones(48, dtype=np.float32) / 48.0, mode="same") * 0.004
    phase = 2.0 * math.pi * f * t + jitter
    signal = np.zeros(length, dtype=np.float32)
    for harmonic, gain in ((1, 1.0), (2, 0.72), (3, 0.46), (4, 0.27), (5, 0.13), (6, 0.07)):
        signal += gain * np.sin(harmonic * phase + harmonic * 0.11)
    signal = np.tanh(signal * (1.1 + 0.55 * force))
    attack = np.minimum(1.0, t / 0.012)
    release = np.exp(-t * (3.6 + force))
    signal *= attack * release
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def short_string(note: str, duration: float, seed: int) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    f = hz(note)
    phase = 2.0 * math.pi * f * t
    rng = np.random.default_rng(seed)
    signal = np.sin(phase) + 0.54 * np.sin(2.0 * phase + 0.1) + 0.22 * np.sin(3.0 * phase + 0.31)
    signal += 0.045 * rng.standard_normal(length).astype(np.float32) * np.exp(-t * 33.0)
    signal *= np.minimum(1.0, t / 0.004) * np.exp(-t * 5.4)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def frame_roll(duration: float, seed: int) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(length).astype(np.float32)
    bright = noise - np.convolve(noise, np.ones(45, dtype=np.float32) / 45.0, mode="same")
    pulses = np.zeros(length, dtype=np.float32)
    for center in (0.00, 0.09, 0.17, 0.24, 0.30):
        pulses += np.exp(-((t - center) / 0.026) ** 2).astype(np.float32)
    signal = bright * pulses * np.exp(-t * 2.4)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def metal_hit(duration: float) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    signal = np.zeros(length, dtype=np.float32)
    for frequency, gain, decay in ((131.0, 1.0, 2.1), (211.0, 0.58, 2.7), (337.0, 0.35, 3.1), (571.0, 0.20, 3.8), (887.0, 0.10, 4.4)):
        signal += gain * np.sin(2.0 * math.pi * frequency * t + frequency * 0.0017) * np.exp(-t * decay)
    signal *= np.minimum(1.0, t / 0.002)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def air_tail(duration: float, seed: int) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(length).astype(np.float32)
    smooth = np.convolve(noise, np.ones(260, dtype=np.float32) / 260.0, mode="same")
    smooth *= np.exp(-t * 1.25)
    return (smooth / (np.max(np.abs(smooth)) + 1e-9)).astype(np.float32)


def delay_tail(stereo: np.ndarray) -> np.ndarray:
    dry = stereo.copy()
    result = stereo.copy()
    for delay, gain, cross in ((0.071, 0.13, True), (0.137, 0.09, False), (0.233, 0.055, True), (0.371, 0.032, False)):
        offset = round(delay * SR)
        if cross:
            result[offset:, 0] += dry[:-offset, 1] * gain
            result[offset:, 1] += dry[:-offset, 0] * gain
        else:
            result[offset:] += dry[:-offset] * gain
    return result


@dataclass
class MidiEvent:
    note: int
    start_beats: float
    duration_beats: float
    velocity: int
    channel: int = 0


def variable_length(value: int) -> bytes:
    output = [value & 0x7F]
    value >>= 7
    while value:
        output.insert(0, (value & 0x7F) | 0x80)
        value >>= 7
    return bytes(output)


def write_midi(path: Path, events_source: list[MidiEvent]) -> None:
    tempo = round(60_000_000 / BPM)
    conductor = b"\x00\xff\x51\x03" + tempo.to_bytes(3, "big") + b"\x00\xff\x58\x04\x06\x03\x18\x08\x00\xff\x2f\x00"
    chunks = [b"MTrk" + struct.pack(">I", len(conductor)) + conductor]
    events: list[tuple[int, bytes]] = []
    for event in events_source:
        start = round(event.start_beats * PPQ)
        end = round((event.start_beats + event.duration_beats) * PPQ)
        events.append((start, bytes([0x90 | event.channel, event.note, event.velocity])))
        events.append((end, bytes([0x80 | event.channel, event.note, 0])))
    events.sort(key=lambda item: (item[0], 0 if item[1][0] & 0xF0 == 0x80 else 1))
    name = b"Combat start v01"
    payload = bytearray(b"\x00\xff\x03" + bytes([len(name)]) + name + b"\x00\xc0\x30")
    previous = 0
    for tick, message in events:
        payload += variable_length(tick - previous) + message
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
    mix = np.zeros((length, 2), dtype=np.float32)

    add(mix, 0.000, impact(1.55, 101, 38.0), 0.76, 0.0)
    add(mix, 0.004, metal_hit(2.35), 0.22, 0.42)
    for index, note in enumerate(("D3", "A3", "Eb4")):
        add(mix, 0.030 + index * 0.012, brass_stab(note, 0.92, 200 + index, 1.25), 0.22, -0.18 + index * 0.18)

    for index, note in enumerate(("D3", "Eb3", "A2", "D3")):
        add(mix, 0.460 + index * 0.105, short_string(note, 0.46, 300 + index), 0.115, -0.35 if index % 2 == 0 else 0.32)

    add(mix, 0.790, impact(1.25, 401, 46.0), 0.46, -0.05)
    add(mix, 0.815, brass_stab("D4", 0.66, 402, 1.05), 0.16, -0.16)
    add(mix, 0.826, brass_stab("Eb4", 0.62, 403, 1.00), 0.14, 0.16)

    add(mix, 1.390, frame_roll(0.48, 501), 0.12, -0.16)
    for index, note in enumerate(("A2", "C3", "D3", "Eb3")):
        add(mix, 1.480 + index * 0.115, short_string(note, 0.40, 510 + index), 0.10 + index * 0.008, 0.28 if index % 2 == 0 else -0.28)

    add(mix, 1.930, impact(1.18, 601, 41.0), 0.58, 0.0)
    for index, note in enumerate(("D3", "A3", "C4", "Eb4")):
        add(mix, 1.955 + index * 0.010, brass_stab(note, 0.78, 610 + index, 1.18), 0.17, -0.24 + index * 0.16)
    add(mix, 1.980, metal_hit(1.10), 0.13, -0.46)

    tail = air_tail(DURATION, 777)
    mix[:, 0] += tail * 0.018
    mix[:, 1] += np.roll(tail, 113) * 0.018
    mix = delay_tail(mix)

    # Preserve a clear handoff window: the final 0.65 s fades to digital silence.
    fade_samples = round(0.65 * SR)
    fade = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)[:, None]
    fade = fade * fade * (3.0 - 2.0 * fade)
    mix[-fade_samples:] *= fade
    mix[-8:] = 0.0

    mix = np.tanh(mix * 1.18).astype(np.float32)
    target_peak = 10.0 ** (-1.5 / 20.0)
    mix *= target_peak / max(float(np.max(np.abs(mix))), 1e-9)

    pcm = np.clip(np.round(mix * 32767.0), -32768, 32767).astype("<i2")
    wav_path = output / "combat_start_v01_master.wav"
    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes(pcm.tobytes())

    ogg_path = output / "combat_start_v01_master.ogg"
    preview_path = output / "combat_start_v01_preview.mp3"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav_path), "-c:a", "libvorbis", "-q:a", "5", str(ogg_path)], check=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav_path), "-c:a", "libmp3lame", "-q:a", "2", str(preview_path)], check=True)

    midi_events = [
        MidiEvent(midi_note("D2"), 0.0, 0.45, 118, 0),
        MidiEvent(midi_note("D3"), 0.05, 0.55, 108, 1),
        MidiEvent(midi_note("A3"), 0.07, 0.50, 101, 1),
        MidiEvent(midi_note("Eb4"), 0.09, 0.48, 105, 1),
        MidiEvent(midi_note("D3"), 0.75, 0.30, 94, 2),
        MidiEvent(midi_note("Eb3"), 0.92, 0.30, 90, 2),
        MidiEvent(midi_note("A2"), 1.09, 0.30, 92, 2),
        MidiEvent(midi_note("D2"), 1.27, 0.38, 112, 0),
        MidiEvent(midi_note("D4"), 1.31, 0.38, 96, 1),
        MidiEvent(midi_note("Eb4"), 1.34, 0.36, 93, 1),
        MidiEvent(midi_note("A2"), 2.37, 0.25, 88, 2),
        MidiEvent(midi_note("C3"), 2.55, 0.25, 87, 2),
        MidiEvent(midi_note("D3"), 2.73, 0.25, 91, 2),
        MidiEvent(midi_note("Eb3"), 2.91, 0.25, 94, 2),
        MidiEvent(midi_note("D2"), 3.09, 0.48, 116, 0),
        MidiEvent(midi_note("D3"), 3.13, 0.45, 104, 1),
        MidiEvent(midi_note("A3"), 3.15, 0.43, 98, 1),
        MidiEvent(midi_note("C4"), 3.17, 0.41, 96, 1),
        MidiEvent(midi_note("Eb4"), 3.19, 0.39, 101, 1),
    ]
    midi_path = output / "combat_start_v01.mid"
    write_midi(midi_path, midi_events)

    pcm_float = pcm.astype(np.float32) / 32768.0
    peak = float(np.max(np.abs(pcm_float)))
    rms = float(np.sqrt(np.mean(np.square(pcm_float))))
    final_window_peak = float(np.max(np.abs(pcm_float[-round(0.10 * SR):])))
    pcm_signature = (pcm.astype(np.int32) >> 8).astype(np.int8).tobytes()
    manifest = {
        "schema_version": 1,
        "composition_id": "combat_start_v01",
        "title_ru": "Первый удар",
        "render_id": "combat_start_v01_master_candidate_01",
        "status": "integrated_master_candidate",
        "renderer": "procedural_combat_start_renderer_v01",
        "arrangement_revision": 1,
        "numpy_version": REQUIRED_NUMPY_VERSION,
        "external_samples_used": False,
        "sample_rate": SR,
        "channels": 2,
        "tempo_bpm": BPM,
        "time_signature": [6, 8],
        "duration_beats": DURATION_BEATS,
        "duration_seconds": round(length / SR, 6),
        "midi_note_count": len(midi_events),
        "peak_dbfs": round(20.0 * math.log10(max(peak, 1e-12)), 3),
        "rms_dbfs": round(20.0 * math.log10(max(rms, 1e-12)), 3),
        "final_100ms_peak_dbfs": round(20.0 * math.log10(max(final_window_peak, 1e-12)), 3),
        "handoff_tail_seconds": 1.175,
        "ogg_bytes": ogg_path.stat().st_size,
        "ogg_sha256": sha256(ogg_path),
        "wav_sha256": sha256(wav_path),
        "midi_sha256": sha256(midi_path),
        "source_score_sha256": sha256(score_path),
        "pcm_signature_shift_bits": 8,
        "pcm_signature_sha256": hashlib.sha256(pcm_signature).hexdigest(),
        "trigger_profile": [
            "false-to-true combat transition only",
            "skip baseline combat on scene load",
            "no turn or round retrigger",
            "overlay combat_standard_v01 crossfade",
            "spectral handoff tail",
        ],
    }
    manifest_path = output / "combat_start_v01_master_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(args.score, args.output)


if __name__ == "__main__":
    main()
