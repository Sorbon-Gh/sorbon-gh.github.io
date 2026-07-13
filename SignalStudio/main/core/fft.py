from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal as scipy_signal

"""Расчет спектра и спектрограммы для визуализации в интерфейсе."""


_EPS = 1e-12
_SUPPORTED_WINDOWS = {"hann", "hamming", "blackman", "kaiser"}


@dataclass(frozen=True)
class AnalysisFrames:
    time_axis: np.ndarray
    signal: np.ndarray
    spectrum_freq: np.ndarray
    spectrum_db: np.ndarray
    spectrogram_freq: np.ndarray
    spectrogram_time: np.ndarray
    spectrogram_db: np.ndarray


def _as_1d_signal(data: np.ndarray) -> np.ndarray:
    # Любой вход (моно/стерео) приводим к одному каналу для спектрального анализа.
    arr = np.asarray(data, dtype=np.float64)
    if arr.size == 0:
        return np.array([], dtype=np.float64)
    if arr.ndim == 1:
        return arr
    if arr.ndim == 2 and arr.shape[1] == 1:
        return arr[:, 0]
    return np.mean(arr, axis=1)


def _effective_nperseg(signal_size: int, nperseg: int) -> int:
    # Длина окна не может быть больше сигнала и меньше 1.
    if signal_size <= 0:
        return 1
    n = int(max(1, nperseg))
    return min(n, signal_size)


def _window_values(window: str, n: int) -> np.ndarray:
    # Если окно не поддерживается, молча возвращаем Hann как безопасный дефолт.
    win_name = window if window in _SUPPORTED_WINDOWS else "hann"
    if win_name == "kaiser":
        return scipy_signal.windows.kaiser(n, beta=14.0, sym=False).astype(np.float64)
    return scipy_signal.get_window(win_name, n, fftbins=True).astype(np.float64)


def _single_sided_amplitude(segment: np.ndarray, window_values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # Нормируем спектр с учетом coherent gain окна, иначе амплитуды будут смещены.
    n = len(segment)
    coherent_gain = float(np.mean(window_values))
    coherent_gain = coherent_gain if coherent_gain > _EPS else 1.0

    spectrum = np.fft.rfft(segment * window_values, n=n)
    magnitude = np.abs(spectrum) / (n * coherent_gain)
    if magnitude.size > 2:
        magnitude[1:-1] *= 2.0
    elif magnitude.size == 2 and n % 2 == 1:
        magnitude[1] *= 2.0
    return magnitude, np.fft.rfftfreq(n, d=1.0)


def compute_fft_spectrum(
    data: np.ndarray,
    sample_rate: float,
    nperseg: int = 4096,
    window: str = "hann",
    use_tail: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    # Возвращаем заглушку -120 дБ, если считать спектр по сути не из чего.
    sr = float(sample_rate)
    if sr <= 0:
        return np.array([0.0], dtype=np.float64), np.array([-120.0], dtype=np.float64)

    signal = _as_1d_signal(data)
    if signal.size == 0:
        return np.array([0.0], dtype=np.float64), np.array([-120.0], dtype=np.float64)

    n = _effective_nperseg(signal.size, nperseg)
    segment = signal[-n:] if use_tail else signal[:n]
    if segment.size < n:
        pad_len = n - segment.size
        segment = np.concatenate([segment, np.zeros(pad_len, dtype=segment.dtype)])

    w = _window_values(window, n)
    magnitude, f_norm = _single_sided_amplitude(segment, w)
    magnitude = np.maximum(magnitude, _EPS)
    db = 20.0 * np.log10(magnitude)
    freq = f_norm * sr
    return freq.astype(np.float64), db.astype(np.float64)


def compute_spectrogram(
    data: np.ndarray,
    sample_rate: float,
    nperseg: int = 1024,
    window: str = "hann",
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Для коротких сигналов обрабатываем крайние случаи отдельно, без падений scipy.
    sr = float(sample_rate)
    signal = _as_1d_signal(data)
    if sr <= 0 or signal.size == 0:
        return (
            np.array([0.0], dtype=np.float64),
            np.array([0.0], dtype=np.float64),
            np.array([[-120.0]], dtype=np.float64),
        )

    if signal.size == 1:
        level = 20.0 * np.log10(max(abs(float(signal[0])), _EPS))
        return (
            np.array([0.0], dtype=np.float64),
            np.array([0.0], dtype=np.float64),
            np.array([[level]], dtype=np.float64),
        )

    n = _effective_nperseg(signal.size, nperseg)
    noverlap = max(0, min(n - 1, n // 2))
    win_name = window if window in _SUPPORTED_WINDOWS else "hann"
    kwargs = {"window": ("kaiser", 14.0)} if win_name == "kaiser" else {"window": win_name}
    freq, time, psd = scipy_signal.spectrogram(
        signal,
        fs=sr,
        nperseg=n,
        noverlap=noverlap,
        detrend=False,
        scaling="density",
        mode="psd",
        **kwargs,
    )
    psd = np.maximum(psd, _EPS)
    db = 10.0 * np.log10(psd)
    return freq.astype(np.float64), time.astype(np.float64), db.astype(np.float64)


def build_analysis_frames(
    data: np.ndarray,
    sample_rate: float,
    nperseg: int = 4096,
    window: str = "hann",
) -> AnalysisFrames:
    # Собираем полный набор данных для трех графиков одним вызовом.
    signal = _as_1d_signal(data)
    sr = float(sample_rate)
    if signal.size == 0 or sr <= 0:
        empty = np.array([], dtype=np.float64)
        return AnalysisFrames(
            time_axis=empty,
            signal=empty,
            spectrum_freq=np.array([0.0], dtype=np.float64),
            spectrum_db=np.array([-120.0], dtype=np.float64),
            spectrogram_freq=np.array([0.0], dtype=np.float64),
            spectrogram_time=np.array([0.0], dtype=np.float64),
            spectrogram_db=np.array([[-120.0]], dtype=np.float64),
        )

    t = np.arange(signal.size, dtype=np.float64) / sr
    f_fft, db_fft = compute_fft_spectrum(signal, sr, nperseg=nperseg, window=window, use_tail=True)
    f_sp, t_sp, db_sp = compute_spectrogram(signal, sr, nperseg=min(nperseg, 2048), window=window)
    return AnalysisFrames(
        time_axis=t,
        signal=signal.astype(np.float64),
        spectrum_freq=f_fft,
        spectrum_db=db_fft,
        spectrogram_freq=f_sp,
        spectrogram_time=t_sp,
        spectrogram_db=db_sp,
    )
