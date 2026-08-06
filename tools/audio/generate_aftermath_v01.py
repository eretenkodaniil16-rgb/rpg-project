#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import struct
import subprocess
import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 48_000
CHANNELS = 2
RENDERER_ID = "procedural_aftermath_renderer_v01"
ARRANGEMENT_REVISION = 1
NUMPY_VERSION = "2.3.5"
TARGET_PEAK_DBFS = -2.0
PCM_SHIFT_BITS = 8


def midi_frequency(note: int) -> float:
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def smoothstep(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def envelope(length: int, attack: float, release: float) -> np.ndarray:
    env = np.ones(length, dtype=np.float64)
    attack_n = min(length, max(1, int(attack * SAMPLE_RATE)))
    release_n = min(length, max(1, int(release * SAMPLE_RATE)))
    env[:attack_n] *= smoothstep(np.linspace(0.0, 1.0, attack_n, endpoint=True))
    env[-release_n:] *= smoothstep(np.linspace(1.0, 0.0, release_n, endpoint=True))
    return env


def add_tone(mix: np.ndarray, start: float, duration: float, midi: int, gain: float,
             pan: float = 0.0, attack: float = 0.03, release: float = 0.35,
             colour: str = "strings") -> None:
    start_i = max(0, int(round(start * SAMPLE_RATE)))
    end_i = min(mix.shape[0], start_i + int(round(duration * SAMPLE_RATE)))
    if end_i <= start_i:
        return
    n = end_i - start_i
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    f = midi_frequency(midi)
    phase = 2.0 * math.pi * f * t
    if colour == "strings":
        signal = (
            np.sin(phase)
            + 0.34 * np.sin(2.0 * phase + 0.11)
            + 0.16 * np.sin(3.0 * phase + 0.37)
            + 0.07 * np.sin(5.0 * phase + 0.61)
        ) / 1.57
        signal *= 0.92 + 0.08 * np.sin(2.0 * math.pi * 4.1 * t)
    elif colour == "horn":
        signal = (
            np.sin(phase)
            + 0.48 * np.sin(2.0 * phase)
            + 0.22 * np.sin(3.0 * phase + 0.2)
        ) / 1.7
    elif colour == "air":
        signal = np.sin(phase) + 0.12 * np.sin(phase * 1.005)
        signal /= 1.12
    else:
        signal = np.sin(phase)
    signal *= envelope(n, attack, release) * gain
    left = math.sqrt((1.0 - pan) * 0.5)
    right = math.sqrt((1.0 + pan) * 0.5)
    mix[start_i:end_i, 0] += signal * left
    mix[start_i:end_i, 1] += signal * right


def add_drum(mix: np.ndarray, start: float, gain: float, decay: float = 0.7) -> None:
    start_i = max(0, int(round(start * SAMPLE_RATE)))
    n = min(mix.shape[0] - start_i, int(round(decay * SAMPLE_RATE)))
    if n <= 0:
        return
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    sweep = 73.0 * np.exp(-8.0 * t) + 39.0
    phase = 2.0 * math.pi * np.cumsum(sweep) / SAMPLE_RATE
    noise_rng = np.random.default_rng(7001 + int(start * 1000))
    noise = noise_rng.normal(0.0, 1.0, n)
    signal = (0.88 * np.sin(phase) + 0.12 * noise) * np.exp(-6.4 * t) * gain
    mix[start_i:start_i+n, 0] += signal * 0.72
    mix[start_i:start_i+n, 1] += signal * 0.72


def add_metal(mix: np.ndarray, start: float, gain: float, duration: float = 3.2, pan: float = 0.0) -> None:
    start_i = max(0, int(round(start * SAMPLE_RATE)))
    n = min(mix.shape[0] - start_i, int(round(duration * SAMPLE_RATE)))
    if n <= 0:
        return
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    freqs = (421.0, 677.0, 1039.0, 1451.0)
    signal = sum(np.sin(2.0 * math.pi * f * t + i * 0.37) / (i + 1.0) for i, f in enumerate(freqs))
    signal *= np.exp(-1.65 * t) * gain * 0.36
    left = math.sqrt((1.0 - pan) * 0.5)
    right = math.sqrt((1.0 + pan) * 0.5)
    mix[start_i:start_i+n, 0] += signal * left
    mix[start_i:start_i+n, 1] += signal * right


def lowpass(signal: np.ndarray, coefficient: float) -> np.ndarray:
    result = np.empty_like(signal)
    result[0] = signal[0]
    for i in range(1, signal.shape[0]):
        result[i] = coefficient * result[i - 1] + (1.0 - coefficient) * signal[i]
    return result


def render(score: dict) -> np.ndarray:
    duration = float(score["duration_seconds"])
    frames = int(round(duration * SAMPLE_RATE))
    mix = np.zeros((frames, CHANNELS), dtype=np.float64)

    # Residual battle impact: decisive but deliberately not triumphant.
    add_drum(mix, 0.0, 0.72, 1.25)
    add_metal(mix, 0.08, 0.34, 4.2, -0.18)
    add_drum(mix, 1.25, 0.28, 0.85)
    add_drum(mix, 2.50, 0.16, 0.72)

    # Low strings lose momentum over nine bars.
    bass_events = [
        (0.0, 5.0, 38), (2.5, 5.0, 36), (5.0, 5.0, 34),
        (7.5, 5.0, 33), (10.0, 5.0, 31), (12.5, 5.0, 33),
        (15.0, 5.0, 34), (17.5, 5.0, 36), (20.0, 2.5, 38),
    ]
    for index, (start, length, note) in enumerate(bass_events):
        gain = 0.23 * (1.0 - index * 0.045)
        add_tone(mix, start, length, note, gain, -0.12, 0.18, 1.35, "strings")
        add_tone(mix, start, length, note + 12, gain * 0.34, 0.16, 0.22, 1.1, "air")

    # Broken fragments of the combat leitmotif, with longer silences each time.
    motif = [50, 57, 60, 63, 62]
    motif_times = [1.15, 2.00, 3.05, 4.15, 5.25]
    for start, note in zip(motif_times, motif):
        add_tone(mix, start, 1.45, note, 0.17, 0.08, 0.025, 0.72, "horn")
    for start, note in zip([8.2, 9.45, 11.1], [57, 60, 63]):
        add_tone(mix, start, 1.65, note, 0.11, -0.05, 0.04, 0.95, "horn")
    for start, note in zip([15.35, 17.2, 19.4], [50, 48, 50]):
        add_tone(mix, start, 2.1, note, 0.075, 0.03, 0.08, 1.35, "strings")

    add_metal(mix, 6.9, 0.115, 4.6, 0.28)
    add_metal(mix, 13.6, 0.072, 5.0, -0.30)

    # Dark air bed and a restrained semitone unease.
    add_tone(mix, 4.0, 16.0, 62, 0.035, -0.28, 1.5, 2.4, "air")
    add_tone(mix, 4.6, 15.4, 63, 0.027, 0.30, 1.7, 2.5, "air")

    # Gentle deterministic texture, filtered to avoid hiss on phone speakers.
    rng = np.random.default_rng(int(score["seed"]))
    noise = rng.normal(0.0, 1.0, frames)
    noise = lowpass(noise, 0.992)
    noise /= max(float(np.max(np.abs(noise))), 1e-9)
    texture_env = smoothstep(np.arange(frames) / (2.8 * SAMPLE_RATE))
    texture_env *= smoothstep((frames - 1 - np.arange(frames)) / (3.0 * SAMPLE_RATE))
    mix[:, 0] += noise * texture_env * 0.015
    mix[:, 1] += np.roll(noise, 211) * texture_env * 0.015

    # Master contour: immediate impact, then exhausted release and quiet handoff.
    contour = np.ones(frames, dtype=np.float64)
    fade_start = int(round(19.2 * SAMPLE_RATE))
    contour[fade_start:] *= smoothstep(np.linspace(1.0, 0.0, frames - fade_start, endpoint=True))
    mix *= contour[:, None]
    mix[0] = 0.0
    mix[-1] = 0.0

    # Soft saturation, DC removal and exact peak normalization.
    mix = np.tanh(mix * 1.12)
    mix -= np.mean(mix, axis=0, keepdims=True)
    peak = float(np.max(np.abs(mix)))
    target = 10.0 ** (TARGET_PEAK_DBFS / 20.0)
    if peak > 0.0:
        mix *= target / peak
    mix[0] = 0.0
    mix[-1] = 0.0
    return np.clip(mix, -1.0, 1.0)


def write_wav(path: Path, mix: np.ndarray) -> None:
    pcm = np.round(mix * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(CHANNELS)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm.tobytes())


def write_midi(path: Path, tempo_bpm: int) -> int:
    ticks = 480
    events: list[tuple[int, bytes]] = []
    # Sparse score representation; rendered timbre remains procedural.
    notes = [
        (0, 38, 3600, 54), (0, 50, 720, 72), (480, 57, 720, 63),
        (960, 60, 720, 60), (1440, 63, 720, 57), (1920, 62, 960, 55),
        (2880, 36, 2880, 48), (3840, 57, 960, 45), (4560, 60, 960, 42),
        (5280, 63, 960, 39), (5760, 34, 2880, 44), (7200, 50, 1440, 36),
        (8640, 33, 2880, 40), (9600, 48, 1440, 34), (11520, 38, 1440, 30),
    ]
    for start, note, length, velocity in notes:
        events.append((start, bytes([0x90, note, velocity])))
        events.append((start + length, bytes([0x80, note, 0])))
    events.sort(key=lambda item: (item[0], item[1][0] == 0x90))

    def vlq(value: int) -> bytes:
        buffer = value & 0x7F
        out = bytearray([buffer])
        while value >> 7:
            value >>= 7
            buffer = (value & 0x7F) | 0x80
            out.insert(0, buffer)
        return bytes(out)

    tempo = round(60_000_000 / tempo_bpm)
    track = bytearray()
    track.extend(b"\x00\xff\x51\x03" + tempo.to_bytes(3, "big"))
    track.extend(b"\x00\xff\x58\x04\x06\x03\x18\x08")
    previous = 0
    for tick, payload in events:
        track.extend(vlq(tick - previous))
        track.extend(payload)
        previous = tick
    track.extend(b"\x00\xff\x2f\x00")
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, ticks)
    path.write_bytes(header + b"MTrk" + struct.pack(">I", len(track)) + track)
    return len(notes)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pcm_signature(mix: np.ndarray) -> str:
    pcm = np.round(mix * 32767.0).astype(np.int16).astype(np.int32)
    quantized = (pcm >> PCM_SHIFT_BITS).astype(np.int16)
    return hashlib.sha256(quantized.astype("<i2").tobytes()).hexdigest()


def dbfs(value: float) -> float:
    return -120.0 if value <= 0.0 else 20.0 * math.log10(value)


def encode(wav_path: Path, ogg_path: Path, mp3_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(wav_path),
                    "-c:a", "libvorbis", "-q:a", "6", str(ogg_path)], check=True)
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(wav_path),
                    "-c:a", "libmp3lame", "-b:a", "192k", str(mp3_path)], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    score = json.loads(args.score.read_text(encoding="utf-8"))
    if np.__version__ != NUMPY_VERSION:
        raise RuntimeError(f"NumPy {NUMPY_VERSION} required, got {np.__version__}")
    args.output.mkdir(parents=True, exist_ok=True)
    mix = render(score)
    wav_path = args.output / "aftermath_v01_master.wav"
    ogg_path = args.output / "aftermath_v01_master.ogg"
    mp3_path = args.output / "aftermath_v01_preview.mp3"
    midi_path = args.output / "aftermath_v01.mid"
    write_wav(wav_path, mix)
    note_count = write_midi(midi_path, int(score["tempo_bpm"]))
    encode(wav_path, ogg_path, mp3_path)
    peak = float(np.max(np.abs(mix)))
    rms = float(np.sqrt(np.mean(np.square(mix))))
    tail = mix[-int(0.1 * SAMPLE_RATE):]
    manifest = {
        "schema_version": 1,
        "composition_id": score["composition_id"],
        "title_ru": score["title_ru"],
        "render_id": score["render_id"],
        "status": "integrated_master_candidate",
        "renderer": RENDERER_ID,
        "arrangement_revision": ARRANGEMENT_REVISION,
        "numpy_version": np.__version__,
        "external_samples_used": False,
        "sample_rate": SAMPLE_RATE,
        "channels": CHANNELS,
        "tempo_bpm": score["tempo_bpm"],
        "time_signature": score["time_signature"],
        "bars": score["bars"],
        "duration_seconds": round(mix.shape[0] / SAMPLE_RATE, 6),
        "midi_note_count": note_count,
        "peak_dbfs": round(dbfs(peak), 3),
        "rms_dbfs": round(dbfs(rms), 3),
        "final_100ms_peak_dbfs": round(dbfs(float(np.max(np.abs(tail)))), 3),
        "boundary_value_delta": round(float(np.max(np.abs(mix[0] - mix[-1]))), 9),
        "ogg_bytes": ogg_path.stat().st_size,
        "ogg_sha256": sha256(ogg_path),
        "wav_sha256": sha256(wav_path),
        "midi_sha256": sha256(midi_path),
        "source_score_sha256": sha256(args.score),
        "pcm_signature_shift_bits": PCM_SHIFT_BITS,
        "pcm_signature_sha256": pcm_signature(mix),
        "outcome_profile": ["victory_only", "escape_skips", "defeat_skips", "scripted_end_skips"],
    }
    (args.output / "aftermath_v01_master_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
