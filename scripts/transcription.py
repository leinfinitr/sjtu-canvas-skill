from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def ensure_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required for audio extraction but was not found in PATH")


def extract_audio(video_path: Path, audio_path: Path) -> None:
    ensure_ffmpeg_available()
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(audio_path),
        ],
        check=True,
    )


def transcribe_audio(audio_path: Path, out_dir: Path, model: str = "small") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    whisper = shutil.which("whisper")
    if whisper is None:
        raise RuntimeError(
            "No ASR backend found. Install openai-whisper CLI or use platform subtitles."
        )
    subprocess.run(
        [
            whisper,
            str(audio_path),
            "--language",
            "Chinese",
            "--model",
            model,
            "--output_format",
            "srt",
            "--output_dir",
            str(out_dir),
        ],
        check=True,
    )
    return out_dir / f"{audio_path.stem}.srt"
