#!/usr/bin/env python3
"""Render combat_standard_v01 ("Steel and Ash").

Original deterministic procedural synthesis for the project. No recordings,
sample packs, or imported MIDI are used. NumPy is pinned to keep the PCM
fingerprint reproducible across the validation environment.
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
BPM = 84
BARS = 36
BEATS_PER_BAR = 3.0  # dotted-quarter pulse in 6/8
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
    vibrato = 0.0024 * np.sin(2.0 * math.pi * 4.7 * t + 0.2)
    phase = 2.0 * math.pi * f * t + vibrato
    signal = (
        np.sin(phase)
        + 0.42 * np.sin(2.0 * phase + 0.13)
        + 0.17 * np.sin(3.0 * phase + 0.41)
        + 0.07 * np.sin(5.0 * phase + 0.23)
    )
    if tremolo > 0.0:
        signal *= 0.78 + 0.22 * np.sin(2.0 * math.pi * tremolo * t + 0.5)
    rng = np.random.default_rng(seed)
    grit = rng.standard_normal(length).astype(np.float32)
    grit = np.convolve(grit, np.ones(20, dtype=np.float32) / 20.0, mode="same")
    signal += 0.024 * grit
    signal *= envelope(length, 0.12, 0.32, 0.9)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def short_string(note: str, duration: float, seed: int, bite: float = 1.0) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    f = hz(note)
    phase = 2.0 * math.pi * f * t
    signal = (
        np.sin(phase)
        + 0.52 * bite * np.sin(2.0 * phase + 0.08)
        + 0.24 * bite * np.sin(3.0 * phase + 0.19)
        + 0.10 * bite * np.sin(4.0 * phase + 0.37)
    )
    rng = np.random.default_rng(seed)
    attack_noise = rng.standard_normal(length).astype(np.float32) * np.exp(-t * 28.0)
    signal += 0.035 * attack_noise
    signal *= np.exp(-t * 4.1).astype(np.float32)
    signal *= envelope(length, 0.004, min(0.13, duration * 0.4), 1.0)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def brass(note: str, duration: float, seed: int, force: float = 1.0) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    f = hz(note)
    rng = np.random.default_rng(seed)
    drift = np.cumsum(rng.standard_normal(length).astype(np.float32))
    drift = drift / (np.max(np.abs(drift)) + 1e-9) * 0.003
    phase = 2.0 * math.pi * f * t + drift
    signal = np.zeros(length, dtype=np.float32)
    for harmonic, gain in ((1, 1.0), (2, 0.58), (3, 0.33), (4, 0.18), (5, 0.09)):
        signal += gain * np.sin(harmonic * phase + harmonic * 0.07)
    signal = np.tanh(signal * (0.85 + 0.35 * force))
    signal *= envelope(length, 0.055, 0.28, 0.82)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def war_drum(duration: float, seed: int, pitch: float = 47.0) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    frequency = pitch + 78.0 * np.exp(-t * 10.0)
    phase = 2.0 * math.pi * np.cumsum(frequency) / SR
    rng = np.random.default_rng(seed)
    skin = rng.standard_normal(length).astype(np.float32)
    skin = np.convolve(skin, np.ones(8, dtype=np.float32) / 8.0, mode="same")
    signal = np.sin(phase) * np.exp(-t * 5.3) + 0.18 * skin * np.exp(-t * 24.0)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def frame_hit(duration: float, seed: int) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(length).astype(np.float32)
    bright = noise - np.convolve(noise, np.ones(52, dtype=np.float32) / 52.0, mode="same")
    tone = np.sin(2.0 * math.pi * 188.0 * t + 0.2) * np.exp(-t * 18.0)
    signal = 0.78 * bright * np.exp(-t * 21.0) + 0.22 * tone
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def metal_hit(frequency: float, duration: float) -> np.ndarray:
    length = max(1, round(duration * SR))
    t = np.arange(length, dtype=np.float32) / SR
    signal = np.zeros(length, dtype=np.float32)
    partials = ((1.0, 1.0, 1.3), (1.41, 0.55, 1.7), (2.13, 0.36, 2.0), (3.77, 0.19, 2.6), (5.23, 0.10, 3.1))
    for ratio, gain, decay in partials:
        signal += gain * np.sin(2.0 * math.pi * frequency * ratio * t + ratio * 0.23) * np.exp(-t * decay)
    signal *= envelope(length, 0.003, min(0.55, duration * 0.35), 1.0)
    return (signal / (np.max(np.abs(signal)) + 1e-9)).astype(np.float32)


def periodic_air(cycle_length: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(cycle_length).astype(np.float32)
    smooth = np.convolve(noise, np.ones(300, dtype=np.float32) / 300.0, mode="same")
    phase = np.arange(cycle_length, dtype=np.float32) / cycle_length
    smooth *= 0.55 + 0.45 * np.sin(2.0 * math.pi * phase * 4.0 + 0.4) ** 2
    smooth /= np.max(np.abs(smooth)) + 1e-9
    return smooth.astype(np.float32)


def delay_reverb(stereo: np.ndarray) -> np.ndarray:
    dry = stereo.copy()
    result = stereo.copy()
    for delay, gain, cross in ((0.061, 0.105, False), (0.097, 0.082, True), (0.149, 0.058, False), (0.233, 0.041, True), (0.367, 0.025, False)):
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
    name = b"Combat standard v01"
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
    total_length = cycle_length * 3
    mix = np.zeros((total_length, 2), dtype=np.float32)
    midi_events: list[MidiEvent] = []

    harmony: list[list[str]] = score["harmony"]
    pulse_pattern = ["D3", "A2", "D3", "Eb3", "C3", "A2"]
    counter_pattern = ["D4", "F4", "Eb4", "A3", "C4", "D4"]
    brass_phrases: dict[int, list[str]] = {
        2: ["D4", "F4", "Eb4"],
        6: ["A3", "C4", "D4"],
        10: ["D4", "Eb4", "A4"],
        14: ["F4", "E4", "Eb4", "D4"],
        18: ["D4", "F4", "A4", "Eb4"],
        22: ["A4", "Bb4", "Eb4", "D4"],
        26: ["D4", "C4", "Eb4", "A3"],
        30: ["F4", "Eb4", "D4"],
        34: ["Eb4", "D4"],
    }

    for cycle in range(3):
        cycle_offset = cycle * DURATION
        for bar, chord in enumerate(harmony):
            root, fifth, pressure = chord
            start = cycle_offset + bar * BAR_SECONDS
            if bar < 4:
                intensity = 0.82
            elif bar < 12:
                intensity = 1.0
            elif bar < 18:
                intensity = 1.1
            elif bar < 26:
                intensity = 1.24
            elif bar < 32:
                intensity = 1.08
            else:
                intensity = 0.9

            add(mix, start, low_string(root, BAR_SECONDS + 0.38, 1000 + bar, 2.0), 0.105 * intensity, -0.24)
            add(mix, start, low_string(fifth, BAR_SECONDS + 0.38, 1100 + bar, 2.45), 0.072 * intensity, 0.20)
            add(mix, start, low_string(pressure, BAR_SECONDS + 0.30, 1200 + bar, 3.0), 0.045 * intensity, 0.02)

            if cycle == 1:
                midi_events.extend([
                    MidiEvent(midi_note(root), bar * 3.0, 2.9, 52, 0),
                    MidiEvent(midi_note(fifth), bar * 3.0, 2.9, 44, 0),
                    MidiEvent(midi_note(pressure), bar * 3.0, 2.9, 34, 0),
                ])

            density = [0, 3] if bar < 2 else [0, 2, 3, 5] if bar < 12 else [0, 1, 2, 3, 4, 5]
            if 32 <= bar:
                density = [0, 2, 3, 5]
            for index, eighth in enumerate(density):
                note = pulse_pattern[(bar + index) % len(pulse_pattern)]
                event_time = start + eighth * BAR_SECONDS / 6.0
                gain = 0.052 if bar < 4 else 0.068 if bar < 18 else 0.082 if bar < 26 else 0.066
                add(mix, event_time, short_string(note, 0.46, 2000 + bar * 10 + eighth, 1.1), gain, -0.34 if eighth % 2 == 0 else 0.31)
                if cycle == 1:
                    midi_events.append(MidiEvent(midi_note(note), bar * 3.0 + eighth * 0.5, 0.38, 58, 1))

            if 12 <= bar < 30:
                for index, eighth in enumerate((1, 4)):
                    note = counter_pattern[(bar + index) % len(counter_pattern)]
                    event_time = start + eighth * BAR_SECONDS / 6.0
                    add(mix, event_time, short_string(note, 0.38, 3000 + bar * 10 + eighth, 0.82), 0.036 * intensity, 0.40 if index == 0 else -0.42)
                    if cycle == 1:
                        midi_events.append(MidiEvent(midi_note(note), bar * 3.0 + eighth * 0.5, 0.3, 42, 2))

            # War drums preserve the 6/8 pulse without becoming continuous action percussion.
            drum_positions = [0, 3]
            if 8 <= bar < 28:
                drum_positions = [0, 2, 3, 5]
            if 18 <= bar < 26:
                drum_positions = [0, 1, 3, 4, 5]
            for hit_index, eighth in enumerate(drum_positions):
                event_time = start + eighth * BAR_SECONDS / 6.0
                accent = 1.0 if eighth in (0, 3) else 0.58
                add(mix, event_time, war_drum(0.72, 4000 + bar * 10 + hit_index, 43.0 if eighth == 0 else 50.0), 0.15 * intensity * accent, -0.05)
                if eighth not in (0, 3):
                    add(mix, event_time + 0.018, frame_hit(0.31, 5000 + bar * 10 + hit_index), 0.035 * intensity, 0.12)

            if bar in brass_phrases:
                notes = brass_phrases[bar]
                for phrase_index, note in enumerate(notes):
                    eighth = phrase_index * (6.0 / max(1, len(notes)))
                    event_time = start + eighth * BAR_SECONDS / 6.0
                    duration = BAR_SECONDS / max(2.0, len(notes) * 0.85)
                    add(mix, event_time, brass(note, duration, 6000 + bar * 10 + phrase_index, intensity), 0.085 * intensity, 0.08)
                    if cycle == 1:
                        midi_events.append(MidiEvent(midi_note(note), bar * 3.0 + eighth * 0.5, duration * BPM / 60.0, 66, 3))

            if bar in (7, 15, 19, 23, 27, 31):
                add(mix, start + 2.5 * BAR_SECONDS / 6.0, metal_hit(126.0 + bar, 1.8), 0.045 * intensity, 0.52 if bar % 2 else -0.52)

    air_cycle = periodic_air(cycle_length, 777)
    air = np.tile(air_cycle, 3)
    mix[:, 0] += air * 0.012
    mix[:, 1] += np.roll(air, 173) * 0.012

    mix = delay_reverb(mix)
    middle = mix[cycle_length : 2 * cycle_length].copy()
    middle = np.tanh(middle * 1.25).astype(np.float32)

    target_peak = 10.0 ** (-1.4 / 20.0)
    current_peak = float(np.max(np.abs(middle)))
    middle *= target_peak / max(current_peak, 1e-9)

    # Correct only the final 0.75 seconds with a bounded smoothstep ramp.
    # This removes the residual value offset from finite synthetic tails; the
    # final two PCM frames below then lock the exact periodic slope.
    seam_samples = round(0.75 * SR)
    t = np.linspace(0.0, 1.0, seam_samples, dtype=np.float32)[:, None]
    smoothstep = t * t * (3.0 - 2.0 * t)
    correction_value = middle[0].copy() - middle[-1].copy()
    middle[-seam_samples:] += correction_value * smoothstep
    middle *= target_peak / max(float(np.max(np.abs(middle))), 1e-9)

    wav_path = output / "combat_standard_v01_master.wav"
    pcm = np.clip(np.round(middle * 32767.0), -32768, 32767).astype("<i2")
    pcm[-1] = pcm[0]
    pcm[-2] = pcm[-1] - (pcm[1] - pcm[0])
    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes(pcm.tobytes())

    ogg_path = output / "combat_standard_v01_master.ogg"
    preview_path = output / "combat_standard_v01_preview.mp3"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav_path),
        "-c:a", "libvorbis", "-q:a", "5", str(ogg_path),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav_path),
        "-c:a", "libmp3lame", "-q:a", "2", str(preview_path),
    ], check=True)

    midi_path = output / "combat_standard_v01.mid"
    write_midi(midi_path, midi_events)

    pcm_float = pcm.astype(np.float32) / 32768.0
    peak = float(np.max(np.abs(pcm_float)))
    rms = float(np.sqrt(np.mean(np.square(pcm_float))))
    boundary_value_delta = float(np.max(np.abs(pcm_float[0] - pcm_float[-1])))
    boundary_slope_delta = float(np.max(np.abs((pcm_float[1] - pcm_float[0]) - (pcm_float[-1] - pcm_float[-2]))))
    pcm_signature = (pcm.astype(np.int32) >> 8).astype(np.int8).tobytes()

    manifest = {
        "schema_version": 1,
        "composition_id": "combat_standard_v01",
        "title_ru": "Сталь и пепел",
        "render_id": "combat_standard_v01_master_candidate_01",
        "status": "integrated_master_candidate",
        "renderer": "procedural_combat_renderer_v01",
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
            "immediate readable entry",
            "turn-based 6/8 pulse",
            "controlled martial percussion",
            "mid-cycle pressure crest",
            "loop return without victory cadence",
        ],
    }
    manifest_path = output / "combat_standard_v01_master_manifest.json"
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
