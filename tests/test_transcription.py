import shutil
import subprocess
from pathlib import Path

import pytest

from scripts import transcription


def test_ensure_ffmpeg_available_raises_when_missing(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="ffmpeg"):
        transcription.ensure_ffmpeg_available()


def test_extract_audio_invokes_ffmpeg(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/ffmpeg" if name == "ffmpeg" else None)
    monkeypatch.setattr(subprocess, "run", lambda cmd, check: calls.append((cmd, check)))
    transcription.extract_audio(tmp_path / "in.mp4", tmp_path / "out.wav")
    assert calls
    assert calls[0][0][0] == "ffmpeg"
    assert str(tmp_path / "out.wav") in calls[0][0]
