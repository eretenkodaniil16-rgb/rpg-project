#!/usr/bin/env python3
"""Create the game-ready main_theme_v01 master candidate from its approved score."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.signal import butter, sosfilt

HERE = Path(__file__).resolve().parent
PROTOTYPE = HERE / "generate_main_theme_v01.py"


def load_prototype():
    spec = importlib.util.spec_from_file_location("main_theme_prototype", PROTOTYPE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {PROTOTYPE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as source:
        if source.getnchannels() != 2 or source.getsampwidth() != 2:
            raise ValueError("Expected stereo 16-bit PCM")
        sample_rate = source.getframerate()
        pcm = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2")
    return (pcm.reshape(-1, 2).astype(np.float32) / 32768.0, sample_rate)


def write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    pcm = np.clip(audio * 32767.0, -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as target:
        target.setnchannels(2)
        target.setsampwidth(2)
        target.setframerate(sample_rate)
        target.writeframes(pcm.tobytes())


def filter_stereo(audio: np.ndarray, sample_rate: int, cutoff: float, kind: str) -> np.ndarray:
    sos = butter(2, cutoff / (sample_rate * 0.5), btype=kind, output="sos")
    return sosfilt(sos, audio, axis=0).astype(np.float32)


def room(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    wet = np.zeros_like(audio)
    taps = (
        (0.079, 0.095, True), (0.137, 0.080, False), (0.223, 0.067, True),
        (0.337, 0.054, False), (0.491, 0.043, True), (0.683, 0.034, False),
        (0.887, 0.026, True), (1.127, 0.019, False),
    )
    for delay_seconds, gain, cross in taps:
        shift = round(delay_seconds * sample_rate)
        if cross:
            wet[shift:, 0] += audio[:-shift, 1] * gain
            wet[shift:, 1] += audio[:-shift, 0] * gain
        else:
            wet[shift:] += audio[:-shift] * gain
    wet = filter_stereo(wet, sample_rate, 110.0, "highpass")
    wet = filter_stereo(wet, sample_rate, 6400.0, "lowpass")
    return wet


def master(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    audio = filter_stereo(audio, sample_rate, 28.0, "highpass")
    low_mid = filter_stereo(audio, sample_rate, 4200.0, "lowpass")
    audio = low_mid + (audio - low_mid) * 0.86

    mid = (audio[:, 0] + audio[:, 1]) * 0.5
    side = (audio[:, 0] - audio[:, 1]) * 0.54
    audio = np.column_stack((mid + side, mid - side)).astype(np.float32)
    audio = audio * 0.90 + room(audio, sample_rate) * 0.24

    power = np.mean(audio * audio, axis=1)
    rms = np.sqrt(uniform_filter1d(power, size=round(0.09 * sample_rate), mode="nearest") + 1e-9)
    threshold = 10.0 ** (-18.0 / 20.0)
    gain = np.ones_like(rms)
    mask = rms > threshold
    gain[mask] = (threshold + (rms[mask] - threshold) / 2.1) / rms[mask]
    gain = uniform_filter1d(gain, size=round(0.14 * sample_rate), mode="nearest")
    audio *= gain[:, None]

    target_rms = 10.0 ** (-18.0 / 20.0)
    current_rms = math.sqrt(float(np.mean(audio * audio)) + 1e-12)
    audio *= target_rms / max(current_rms, 1e-9)
    audio = np.tanh(audio * 1.08).astype(np.float32) / np.tanh(1.08)
    peak = float(np.max(np.abs(audio)))
    peak_limit = 10.0 ** (-1.5 / 20.0)
    if peak > peak_limit:
        audio *= peak_limit / peak
    return audio


def render(score_path: Path, output: Path) -> dict:
    score = json.loads(score_path.read_text(encoding="utf-8"))
    prototype = load_prototype()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="main-theme-prototype-") as temp_dir:
        prototype.build_score(score, Path(temp_dir))
        audio, sample_rate = read_wav(Path(temp_dir) / "main_theme_v01_mockup.wav")
    audio = master(audio, sample_rate)

    wav_path = output / "main_theme_v01_master_candidate.wav"
    ogg_path = output / "main_theme_v01_master_candidate.ogg"
    mp3_path = output / "main_theme_v01_master_candidate.mp3"
    write_wav(wav_path, audio, sample_rate)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required")
    subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path), "-c:a", "libvorbis", "-q:a", "6", str(ogg_path)], check=True)
    subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path), "-c:a", "libmp3lame", "-b:a", "256k", str(mp3_path)], check=True)

    peak = float(np.max(np.abs(audio)))
    rms = math.sqrt(float(np.mean(audio * audio)) + 1e-12)
    manifest = {
        "schema_version": 1,
        "composition_id": "main_theme_v01",
        "render_id": "main_theme_v01_master_candidate_02",
        "status": "integrated_master_candidate",
        "renderer": "procedural_master_v02",
        "external_samples_used": False,
        "sample_rate": sample_rate,
        "channels": 2,
        "tempo_bpm": score["tempo_bpm"],
        "time_signature": score["time_signature"],
        "bars": score["bars"],
        "duration_seconds": round(len(audio) / sample_rate, 6),
        "peak_dbfs": round(20.0 * math.log10(max(peak, 1e-12)), 3),
        "rms_dbfs": round(20.0 * math.log10(max(rms, 1e-12)), 3),
        "boundary_value_delta": round(float(np.max(np.abs(audio[0] - audio[-1]))), 8),
        "boundary_slope_delta": round(float(np.max(np.abs((audio[1] - audio[0]) - (audio[-1] - audio[-2])))), 8),
        "ogg_bytes": ogg_path.stat().st_size,
        "ogg_sha256": hashlib.sha256(ogg_path.read_bytes()).hexdigest(),
        "wav_sha256": hashlib.sha256(wav_path.read_bytes()).hexdigest(),
        "source_score_sha256": hashlib.sha256(json.dumps(score, sort_keys=True).encode("utf-8")).hexdigest(),
    }
    (output / "main_theme_v01_master_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
