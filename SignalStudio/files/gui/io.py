from __future__ import annotations

from pathlib import Path

import numpy as np
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget

from core.audio_player import play
from core.wav_handler import save_wav

"""Общий слой ввода-вывода: безопасный play и диалог сохранения WAV."""


def play_with_error_handling(parent: QWidget, data: np.ndarray, sample_rate: int) -> None:
    # Любую ошибку аудиовывода показываем пользователю через QMessageBox.
    try:
        play(np.asarray(data, dtype=np.float32), int(sample_rate), blocking=False)
    except RuntimeError as exc:
        QMessageBox.warning(parent, "Ошибка воспроизведения", str(exc))


def save_wav_dialog(parent: QWidget, data: np.ndarray, sample_rate: int, default_name: str) -> None:
    # Унифицированный диалог сохранения, чтобы логика экспорта была в одном месте.
    if data is None or getattr(data, 'size', 0) == 0:
        return
    suggested = Path(default_name).stem if default_name else "signal"
    out_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Сохранить WAV",
        f"{suggested}.wav",
        "WAV (*.wav);;Все (*)",
    )
    if not out_path:
        return
    arr = np.asarray(data, dtype=np.float32)
    channels = arr.shape[1] if arr.ndim == 2 else 1
    try:
        save_wav(out_path, arr, int(sample_rate), n_channels=channels)
        QMessageBox.information(parent, "Сохранение", f"Файл сохранен:\n{out_path}")
    except Exception as exc:
        QMessageBox.warning(parent, "Ошибка сохранения", f"Не удалось сохранить WAV:\n{exc}")
