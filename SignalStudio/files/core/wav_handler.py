import wave
from pathlib import Path

import numpy as np

"""Чтение и сохранение WAV-файлов с защитой от типичных ошибок формата."""

_MIN_FRAMERATE = 1
_MAX_FRAMERATE = 1_000_000
_MAX_CHANNELS = 2


def load_wav(path: str) -> tuple[np.ndarray, int, int]:
    # Открываем WAV и валидируем базовые параметры потока.
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f'Файл не найден: {path}')
    with wave.open(str(p), 'rb') as wf:
        n_channels = wf.getnchannels()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        sampwidth = wf.getsampwidth()
        if n_channels < 1 or n_channels > _MAX_CHANNELS:
            raise ValueError(f'Неподдерживаемое число каналов: {n_channels}')
        if framerate < _MIN_FRAMERATE or framerate > _MAX_FRAMERATE:
            raise ValueError(f'Недопустимая частота дискретизации: {framerate}')
        raw = wf.readframes(n_frames)
    if n_frames == 0:
        empty = np.array([], dtype=np.float32)
        return (empty.reshape(-1, 2) if n_channels == 2 else empty, framerate, n_channels)

    if sampwidth == 1:
        # 8-битный PCM в WAV беззнаковый: смещаем в диапазон [-1, 1).
        data = np.frombuffer(raw, dtype=np.uint8)
        data = (data.astype(np.float32) - 128) / 128.0
    elif sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16)
        data = data.astype(np.float32) / 32768.0
    elif sampwidth == 3:
        # Для 24-бит собираем little-endian вручную и делаем sign extension.
        arr = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        lo, mi, hi = arr[:, 0].astype(np.int32), arr[:, 1].astype(np.int32), arr[:, 2].astype(np.int32)
        data = (lo + (mi << 8) + (hi << 16)).astype(np.float32)
        data[hi >= 128] -= 16777216.0
        data = data / 8388608.0
    elif sampwidth == 4:
        data = np.frombuffer(raw, dtype=np.int32)
        data = data.astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f'Неподдерживаемая разрядность WAV: {sampwidth * 8} бит')

    if n_channels == 2:
        data = data.reshape(-1, 2)
    return data, framerate, n_channels


def save_wav(path: str, data: np.ndarray, sample_rate: int, n_channels: int = 1) -> None:
    # Перед сохранением нормализуем данные и добавляем TPDF-дизеринг.
    if data is None or data.size == 0:
        raise ValueError('Данные для сохранения пусты')
    data = np.nan_to_num(np.asarray(data, dtype=np.float64), nan=0.0, posinf=1.0, neginf=-1.0)
    expected_channels = data.shape[1] if data.ndim == 2 else 1
    if n_channels != expected_channels:
        raise ValueError(f'n_channels={n_channels} не соответствует данным (shape={data.shape})')
    if sample_rate < _MIN_FRAMERATE or sample_rate > _MAX_FRAMERATE:
        raise ValueError(f'Недопустимая частота дискретизации: {sample_rate}')
    p = Path(path)
    if not p.parent.exists():
        raise FileNotFoundError(f'Директория не существует: {p.parent}')
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    scale = peak if peak > 1.0 else 1.0
    if scale > 0:
        data = data / scale
    rng = np.random.default_rng()
    dither = rng.uniform(-0.5, 0.5, data.shape)
    int_data = np.clip(np.round(data * 32768.0 + dither).astype(np.int32), -32768, 32767).astype(np.int16)
    if int_data.ndim == 1:
        int_data = int_data.reshape(-1, 1)

    with wave.open(path, 'wb') as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_data.tobytes())
