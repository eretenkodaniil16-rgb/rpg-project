#!/usr/bin/env python3
"""Render combat_climax_v01 ("Steel in Fire").

Original deterministic procedural synthesis for the project. No recordings,
sample packs, imported MIDI, or third-party melodic material are used.
The composition shares tempo and tonal language with combat_standard_v01 but
uses an independently authored climax arrangement.
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
BARS = 40
BEATS_PER_BAR = 3.0
BAR_SECONDS = 60.0 / BPM * BEATS_PER_BAR
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


def envelope(length: int, attack: float, release: float, sustain: float = 1.0) -> np.ndarray:
    result = np.full(length, sustain, dtype=np.float32)
    attack_samples = min(length, max(1, round(attack * SR)))
    release_samples = min(length, max(1, round(release * SR)))
    result[:attack_samples] *= np.sin(
        np.linspace(0.0, math.pi / 2.0, attack_samples, endpoint=False, dtype=np.float32)
    ) ** 2
    result[-release_samples:] *= np.cos(
        np.linspace(0.0, math.pi / 2.0, release_samples, endpoint=False, dtype=np.float32)
    ) ** 2
    return result


def stereo_pan(signal: np.ndarray, position: float) -> np.ndarray:
    position = max(-1.0, min(1.0, position))
    angle = (position + 1.0) * math.pi / 4.0
    return np.column_stack((signal * math.cos(angle), signal * math.sin(angle))).astype(np.float32)


def add(mix: np.ndarray, start_seconds: float, signal: np.ndarray, gain: float, position: float = 0.0) -> None:
    start = max(0, round(start_seconds * SR))
    stereo = stereo_pan(signal, position)
    end = min(len(mix), start + len(stereo))
    if end > start:
        mix[start:end] += stereo[: end - start] * gain


def low_string(note: str, duration: float, seed: int, tremolo: float = 0.0) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    f = hz(note)
    phase = 2.0 * math.pi * f * t + 0.0026 * np.sin(2.0 * math.pi * 4.9 * t)
    signal = (
        np.sin(phase)
        + 0.46 * np.sin(2.0 * phase + 0.11)
        + 0.20 * np.sin(3.0 * phase + 0.31)
        + 0.08 * np.sin(5.0 * phase + 0.17)
    )
    if tremolo > 0.0:
        signal *= 0.74 + 0.26 * np.sin(2.0 * math.pi * tremolo * t + 0.5)
    rng = np.random.default_rng(seed)
    grit = rng.standard_normal(length).astype(np.float32)
    grit = np.convolve(grit, np.ones(16, dtype=np.float32) / 16.0, mode="same")
    signal += 0.030 * grit
    signal *= envelope(length, 0.07, 0.25, 0.92)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def short_string(note: str, duration: float, seed: int, bite: float = 1.0) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    f = hz(note)
    phase = 2.0 * math.pi * f * t
    signal = (
        np.sin(phase)
        + 0.62 * bite * np.sin(2.0 * phase + 0.08)
        + 0.31 * bite * np.sin(3.0 * phase + 0.21)
        + 0.14 * bite * np.sin(4.0 * phase + 0.39)
    )
    rng = np.random.default_rng(seed)
    signal += 0.050 * rng.standard_normal(length).astype(np.float32) * np.exp(-t * 34.0)
    signal = np.tanh(signal * 1.08)
    signal *= np.exp(-t * 5.8).astype(np.float32)
    signal *= envelope(length, 0.002, min(0.095, duration * 0.35), 1.0)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def brass_stab(note: str, duration: float, seed: int, force: float = 1.0) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    f = hz(note)
    rng = np.random.default_rng(seed)
    drift = np.cumsum(rng.standard_normal(length).astype(np.float32))
    drift = drift / (np.max(np.abs(drift)) + 1e-9) * 0.002
    phase = 2.0 * math.pi * f * t + drift
    signal = np.zeros(length, dtype=np.float32)
    for harmonic, gain in ((1, 1.0), (2, 0.72), (3, 0.46), (4, 0.27), (5, 0.14), (6, 0.07)):
        signal += gain * np.sin(harmonic * phase + harmonic * 0.05)
    signal = np.tanh(signal * (1.05 + 0.55 * force))
    signal *= np.exp(-t * 1.65).astype(np.float32)
    signal *= envelope(length, 0.018, 0.18, 0.88)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def low_choir(note: str, duration: float, seed: int) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    f = hz(note)
    rng = np.random.default_rng(seed)
    wobble = 0.004 * np.sin(2.0 * math.pi * 5.2 * t) + 0.0015 * rng.standard_normal(length).astype(np.float32)
    phase = 2.0 * math.pi * f * t + wobble
    signal = (
        np.sin(phase)
        + 0.30 * np.sin(2.0 * phase + 0.2)
        + 0.13 * np.sin(3.0 * phase + 0.4)
    )
    formant = 0.55 + 0.45 * np.sin(2.0 * math.pi * 2.2 * f * t + 0.3) ** 2
    signal *= formant
    signal *= envelope(length, 0.24, 0.42, 0.82)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def war_drum(duration: float, seed: int, pitch: float = 43.0, snap: float = 1.0) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    frequency = pitch + 98.0 * np.exp(-t * 13.0)
    phase = 2.0 * math.pi * np.cumsum(frequency) / SR
    rng = np.random.default_rng(seed)
    skin = rng.standard_normal(length).astype(np.float32)
    skin = np.convolve(skin, np.ones(6, dtype=np.float32) / 6.0, mode="same")
    signal = np.sin(phase) * np.exp(-t * 6.0) + 0.24 * snap * skin * np.exp(-t * 28.0)
    signal = np.tanh(signal * 1.12)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def frame_snare(duration: float, seed: int) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(length).astype(np.float32)
    high = noise - np.convolve(noise, np.ones(42, dtype=np.float32) / 42.0, mode="same")
    tone = np.sin(2.0 * math.pi * 210.0 * t) * np.exp(-t * 22.0)
    signal = 0.88 * high * np.exp(-t * 25.0) + 0.12 * tone
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def impact(duration: float, seed: int, pitch: float = 35.0) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    rng = np.random.default_rng(seed)
    frequency = pitch + 130.0 * np.exp(-t * 9.0)
    phase = 2.0 * math.pi * np.cumsum(frequency) / SR
    noise = rng.standard_normal(length).astype(np.float32)
    noise = np.convolve(noise, np.ones(5, dtype=np.float32) / 5.0, mode="same")
    signal = 1.1 * np.sin(phase) * np.exp(-t * 3.8) + 0.38 * noise * np.exp(-t * 17.0)
    signal = np.tanh(signal * 1.35)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def metal_hit(frequency: float, duration: float) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    signal = np.zeros(length, dtype=np.float32)
    for ratio, gain, decay in ((1.0, 1.0, 1.1), (1.43, 0.61, 1.5), (2.17, 0.39, 1.9), (3.83, 0.21, 2.5), (5.37, 0.11, 3.1)):
        signal += gain * np.sin(2.0 * math.pi * frequency * ratio * t + ratio * 0.21) * np.exp(-t * decay)
    signal *= envelope(length, 0.002, min(0.48, duration * 0.3), 1.0)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def periodic_air(cycle_length: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(cycle_length).astype(np.float32)
    smooth = np.convolve(noise, np.ones(260, dtype=np.float32) / 260.0, mode="same")
    phase = np.arange(cycle_length, dtype=np.float32) / cycle_length
    smooth *= 0.48 + 0.52 * np.sin(2.0 * math.pi * phase * 5.0 + 0.6) ** 2
    return (smooth / (np.max(np.abs(smooth)) + 1e-9)).astype(np.float32)


def delay_reverb(stereo: np.ndarray) -> np.ndarray:
    dry = stereo.copy()
    result = stereo.copy()
    for delay, gain, cross in ((0.047, 0.085, False), (0.081, 0.070, True), (0.127, 0.050, False), (0.191, 0.033, True), (0.307, 0.019, False)):
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
    conductor = (
        b"\x00\xff\x51\x03" + tempo.to_bytes(3, "big")
        + b"\x00\xff\x58\x04\x06\x03\x18\x08"
        + b"\x00\xff\x2f\x00"
    )
    chunks = [b"MTrk" + struct.pack(">I", len(conductor)) + conductor]
    events: list[tuple[int, bytes]] = []
    for event in events_source:
        start = round(event.start_beats * PPQ)
        end = round((event.start_beats + event.duration_beats) * PPQ)
        events.append((start, bytes([0x90 | event.channel, event.note, event.velocity])))
        events.append((end, bytes([0x80 | event.channel, event.note, 0])))
    events.sort(key=lambda item: (item[0], 0 if item[1][0] & 0xF0 == 0x80 else 1))
    name = b"Combat climax v01"
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

    cycle_length = round(DURATION * SR)
    mix = np.zeros((cycle_length * 3, 2), dtype=np.float32)
    midi_events: list[MidiEvent] = []
    harmony: list[list[str]] = score["harmony"]

    # Same 96 BPM/6-8 grid as combat_standard_v01, but a distinct climax motif
    # and denser orchestration. The pattern never depends on hit points.
    ostinato = ["D3", "Eb3", "D3", "A2", "C3", "F3"]
    upper_drive = ["A3", "C4", "D4", "Eb4", "F4", "Gb4"]
    brass_calls: dict[int, list[str]] = {
        0: ["D4", "Eb4", "A4"],
        2: ["F4", "Eb4", "D4"],
        4: ["D4", "F4", "A4", "Eb4"],
        6: ["A3", "C4", "Eb4"],
        8: ["D4", "Eb4", "F4", "A4"],
        10: ["C4", "Eb4", "D4"],
        12: ["D4", "A4", "Bb4", "Eb5"],
        14: ["F4", "Gb4", "Eb4", "D4"],
        16: ["D4", "F4", "A4", "C5"],
        18: ["Eb4", "D4", "A3"],
        20: ["D4", "Eb4", "A4", "D5"],
        22: ["F4", "E4", "Eb4", "D4"],
        24: ["A4", "Bb4", "Eb5", "D5"],
        26: ["D4", "F4", "Gb4", "A4"],
        28: ["D4", "C4", "Eb4", "A3"],
        30: ["F4", "Gb4", "A4", "Eb5"],
        32: ["D4", "A4", "C5", "Eb5"],
        34: ["Bb4", "A4", "F4", "Eb4"],
        36: ["D4", "Eb4", "F4", "A4"],
        38: ["C5", "Eb5", "D5"],
        39: ["Eb4", "D4", "A3"],
    }
    impact_bars = {0, 4, 8, 12, 16, 20, 24, 28, 32, 36}
    breath_bars = {15, 31, 39}
    peak_bars = set(range(20, 32))

    for cycle in range(3):
        cycle_offset = cycle * DURATION
        for bar, (root, fifth, pressure) in enumerate(harmony):
            start = cycle_offset + bar * BAR_SECONDS
            if bar < 4:
                intensity = 1.16
            elif bar < 12:
                intensity = 1.27
            elif bar < 20:
                intensity = 1.38
            elif bar < 32:
                intensity = 1.52
            elif bar < 36:
                intensity = 1.34
            else:
                intensity = 1.20

            # The harmonic pedal is tighter and more saturated than the standard battle bed.
            add(mix, start, low_string(root, BAR_SECONDS + 0.24, 1000 + bar, 4.0), 0.090 * intensity, -0.24)
            add(mix, start, low_string(fifth, BAR_SECONDS + 0.24, 1100 + bar, 4.4), 0.058 * intensity, 0.22)
            add(mix, start, low_string(pressure, BAR_SECONDS + 0.20, 1200 + bar, 4.8), 0.047 * intensity, 0.0)

            if bar >= 4:
                add(mix, start, low_choir(root, BAR_SECONDS + 0.18, 1300 + bar), 0.046 * intensity, -0.04)
                if bar in peak_bars:
                    add(mix, start, low_choir(pressure, BAR_SECONDS + 0.12, 1400 + bar), 0.030 * intensity, 0.12)

            if cycle == 1:
                midi_events.extend([
                    MidiEvent(midi_note(root), bar * 3.0, 2.9, 62, 0),
                    MidiEvent(midi_note(fifth), bar * 3.0, 2.9, 52, 0),
                    MidiEvent(midi_note(pressure), bar * 3.0, 2.9, 46, 0),
                ])

            density = [0, 1, 2, 3, 4, 5]
            if bar in breath_bars:
                density = [0, 1, 3, 4]
            for eighth in density:
                note = ostinato[(bar * 3 + eighth) % len(ostinato)]
                event_time = start + eighth * BAR_SECONDS / 6.0
                base_gain = 0.088 if bar < 12 else 0.103 if bar < 20 else 0.119 if bar < 32 else 0.098
                accent = 1.30 if eighth in (0, 3) else 0.94
                add(
                    mix,
                    event_time,
                    short_string(note, 0.35, 2000 + bar * 10 + eighth, 1.42),
                    base_gain * intensity * accent,
                    -0.40 if eighth % 2 == 0 else 0.36,
                )
                if bar in peak_bars and eighth in (1, 2, 4, 5):
                    add(
                        mix,
                        event_time + BAR_SECONDS / 12.0,
                        short_string(note, 0.22, 2400 + bar * 10 + eighth, 1.18),
                        0.044 * intensity,
                        0.34 if eighth % 2 == 0 else -0.34,
                    )
                if cycle == 1:
                    midi_events.append(MidiEvent(midi_note(note), bar * 3.0 + eighth * 0.5, 0.28, 74 if eighth in (0, 3) else 63, 1))

            if bar >= 6 and bar not in breath_bars:
                upper_positions = (1, 2, 4, 5) if bar in peak_bars else (1, 4)
                for index, eighth in enumerate(upper_positions):
                    note = upper_drive[(bar + index * 2) % len(upper_drive)]
                    event_time = start + eighth * BAR_SECONDS / 6.0
                    add(mix, event_time, short_string(note, 0.29, 3000 + bar * 10 + eighth, 1.08), 0.051 * intensity, 0.46 if index % 2 == 0 else -0.46)
                    if cycle == 1:
                        midi_events.append(MidiEvent(midi_note(note), bar * 3.0 + eighth * 0.5, 0.22, 54, 2))

            drum_positions = [0, 1, 2, 3, 4, 5]
            if bar in breath_bars:
                drum_positions = [0, 3, 4]
            for hit_index, eighth in enumerate(drum_positions):
                event_time = start + eighth * BAR_SECONDS / 6.0
                accent = 1.46 if eighth == 0 else 1.28 if eighth == 3 else 0.78
                add(
                    mix,
                    event_time,
                    war_drum(0.62, 4000 + bar * 10 + hit_index, 36.0 if eighth == 0 else 47.0, 1.25),
                    0.166 * intensity * accent,
                    -0.07,
                )
                if eighth not in (0, 3) or bar in peak_bars:
                    add(mix, event_time + 0.010, frame_snare(0.24, 5000 + bar * 10 + hit_index), 0.060 * intensity, 0.18)

            if bar not in breath_bars:
                add(mix, start + 0.32 * BAR_SECONDS / 6.0, war_drum(0.44, 5400 + bar, 56.0, 1.0), 0.091 * intensity, 0.10)
                if bar in peak_bars:
                    add(mix, start + 3.32 * BAR_SECONDS / 6.0, war_drum(0.44, 5500 + bar, 59.0, 1.0), 0.086 * intensity, -0.10)

            if bar in brass_calls:
                notes = brass_calls[bar]
                for index, note in enumerate(notes):
                    eighth = index * (4.4 / max(1, len(notes) - 0.4))
                    event_time = start + eighth * BAR_SECONDS / 6.0
                    duration = 0.52 if index == 0 else 0.40
                    add(mix, event_time, brass_stab(note, duration, 6000 + bar * 10 + index, 1.2 + intensity), 0.139 * intensity, 0.11)
                    if cycle == 1:
                        midi_events.append(MidiEvent(midi_note(note), bar * 3.0 + eighth * 0.5, duration * BPM / 60.0, 88, 3))

            if bar in impact_bars:
                add(mix, start, impact(1.30, 7000 + bar, 30.0 if bar in (0, 20) else 35.0), 0.255 * intensity, 0.0)
                add(mix, start + 0.018, metal_hit(102.0 + bar * 1.7, 1.55), 0.071 * intensity, 0.53 if bar % 8 else -0.53)

            if bar in (3, 7, 11, 19, 23, 27, 35):
                add(mix, start + 5.0 * BAR_SECONDS / 6.0, metal_hit(148.0 + bar, 1.30), 0.058 * intensity, 0.57 if bar % 2 else -0.57)

    air_cycle = periodic_air(cycle_length, 1777)
    air = np.tile(air_cycle, 3)
    mix[:, 0] += air * 0.010
    mix[:, 1] += np.roll(air, 239) * 0.010

    mix = delay_reverb(mix)
    middle = mix[cycle_length:2 * cycle_length].copy()
    middle = np.tanh(middle * 1.92).astype(np.float32)

    target_peak = 10.0 ** (-1.0 / 20.0)
    middle *= target_peak / max(float(np.max(np.abs(middle))), 1e-9)

    seam_samples = round(0.62 * SR)
    t = np.linspace(0.0, 1.0, seam_samples, dtype=np.float32)[:, None]
    smoothstep = t * t * (3.0 - 2.0 * t)
    middle[-seam_samples:] += (middle[0].copy() - middle[-1].copy()) * smoothstep
    middle *= target_peak / max(float(np.max(np.abs(middle))), 1e-9)

    wav_path = output / "combat_climax_v01_master.wav"
    pcm = np.clip(np.round(middle * 32767.0), -32768, 32767).astype("<i2")
    pcm[-1] = pcm[0]
    pcm[-2] = pcm[-1] - (pcm[1] - pcm[0])
    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes(pcm.tobytes())

    ogg_path = output / "combat_climax_v01_master.ogg"
    preview_path = output / "combat_climax_v01_preview.mp3"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav_path),
        "-c:a", "libvorbis", "-q:a", "5", str(ogg_path),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav_path),
        "-c:a", "libmp3lame", "-q:a", "2", str(preview_path),
    ], check=True)

    midi_path = output / "combat_climax_v01.mid"
    write_midi(midi_path, midi_events)

    pcm_float = pcm.astype(np.float32) / 32768.0
    peak = float(np.max(np.abs(pcm_float)))
    rms = float(np.sqrt(np.mean(np.square(pcm_float))))
    boundary_value_delta = float(np.max(np.abs(pcm_float[0] - pcm_float[-1])))
    boundary_slope_delta = float(np.max(np.abs((pcm_float[1] - pcm_float[0]) - (pcm_float[-1] - pcm_float[-2]))))
    pcm_signature = (pcm.astype(np.int32) >> 8).astype(np.int8).tobytes()

    manifest = {
        "schema_version": 1,
        "composition_id": "combat_climax_v01",
        "title_ru": "Сталь в огне",
        "render_id": "combat_climax_v01_master_candidate_01",
        "status": "integrated_master_candidate",
        "renderer": "procedural_combat_climax_renderer_v01",
        "arrangement_revision": 1,
        "numpy_version": REQUIRED_NUMPY_VERSION,
        "external_samples_used": False,
        "sample_rate": SR,
        "channels": 2,
        "tempo_bpm": BPM,
        "time_signature": [6, 8],
        "bars": BARS,
        "duration_seconds": round(cycle_length / SR, 6),
        "midi_note_count": len(midi_events),
        "peak_dbfs": round(20.0 * math.log10(max(peak, 1e-12)), 3),
        "rms_dbfs": round(20.0 * math.log10(max(rms, 1e-12)), 3),
        "boundary_value_delta": round(boundary_value_delta, 8),
        "boundary_slope_delta": round(boundary_slope_delta, 8),
        "ogg_bytes": ogg_path.stat().st_size,
        "ogg_sha256": sha256(ogg_path),
        "wav_sha256": sha256(wav_path),
        "midi_sha256": sha256(midi_path),
        "source_score_sha256": sha256(score_path),
        "pcm_signature_shift_bits": 8,
        "pcm_signature_sha256": hashlib.sha256(pcm_signature).hexdigest(),
        "combat_profile": [
            "event-driven climax only",
            "tempo-compatible with combat_standard_v01",
            "continuous six-eighth martial drive",
            "double-layer short-string ostinato",
            "dense war drums and frame-snare",
            "expanded brass calls",
            "low synthetic choir pressure",
            "loop return without victory cadence",
        ],
    }
    manifest_path = output / "combat_climax_v01_master_manifest.json"
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
