import time
import warnings

import numpy as np
from scipy import signal as scipy_signal

"""Генерация тестовых сигналов и фильтрация для всех рабочих режимов приложения."""

_KNOWN_WAVEFORMS = frozenset({
    'sinusoidal', 'triangular', 'rectangular', 'meander', 'sawtooth',
    'noise', 'pulse', 'dc', 'chirp', 'trapezoidal', 'gaussian'
})


def generate_signal(waveform: str, freq: float, sample_rate: float, duration: float,
                    amplitude: float = 1.0, offset: float = 0.0, phase_deg: float = 0.0,
                    duty_cycle: float = 0.5,                     noise_seed: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    # Базовая валидация параметров генерации.
    if sample_rate <= 0:
        raise ValueError('sample_rate должен быть > 0')
    if duration <= 0:
        raise ValueError('duration должен быть > 0')
    duty_cycle = float(np.clip(duty_cycle, 0.01, 0.99))
    nyquist = sample_rate / 2
    # Ограничиваем частоту, чтобы не выйти за Найквист и не ловить алиасинг в UI.
    if freq > nyquist * 0.99:
        freq = nyquist * 0.99
    n = int(sample_rate * duration)
    if n < 1:
        n = 1
    if n > 10_000_000:
        n = 10_000_000
    t = np.linspace(0, duration, n, endpoint=False, dtype=np.float64)
    phase_rad = np.deg2rad(phase_deg)

    if waveform == 'sinusoidal':
        y = amplitude * np.sin(2 * np.pi * freq * t + phase_rad) + offset
    elif waveform == 'triangular':
        y = amplitude * scipy_signal.sawtooth(2 * np.pi * freq * t + phase_rad, width=0.5) + offset
    elif waveform == 'rectangular':
        y = amplitude * scipy_signal.square(2 * np.pi * freq * t + phase_rad, duty=duty_cycle) + offset
    elif waveform == 'meander':
        y = amplitude * scipy_signal.square(2 * np.pi * freq * t + phase_rad, duty=0.5) + offset
    elif waveform == 'sawtooth':
        y = amplitude * scipy_signal.sawtooth(2 * np.pi * freq * t + phase_rad, width=1) + offset
    elif waveform == 'noise':
        # Если seed не задан, берем быстро меняющееся значение времени.
        seed = noise_seed if noise_seed is not None else int(time.time_ns() % (2**32))
        rng = np.random.default_rng(seed)
        y = amplitude * np.float32(rng.standard_normal(len(t))) + offset
    elif waveform == 'pulse':
        y = amplitude * (scipy_signal.square(2 * np.pi * freq * t + phase_rad, duty=duty_cycle) * 0.5 + 0.5) + offset
    elif waveform == 'dc':
        y = np.full_like(t, offset, dtype=np.float32)
    elif waveform == 'chirp':
        f_end = min(4.0 * freq, nyquist * 0.99)
        y = amplitude * scipy_signal.chirp(t, f0=freq, f1=f_end, t1=duration, method='linear') + offset
    elif waveform == 'trapezoidal':
        x = (freq * t + phase_rad / (2 * np.pi)) % 1.0
        r = 0.125
        y_cycle = np.where(x < r, -1.0 + 2.0 * x / r,
                  np.where(x < 0.5, 1.0,
                  np.where(x < 0.5 + r, 1.0 - 2.0 * (x - 0.5) / r,
                  -1.0)))
        y = amplitude * y_cycle + offset
    elif waveform == 'gaussian':
        # Формируем периодический гауссов импульс с безопасной защитой от деления на ноль.
        safe_freq = max(abs(freq), 1e-6)
        T = 1.0 / safe_freq
        sigma = T / 6.0
        x = (t + phase_rad / (2 * np.pi * safe_freq)) % T
        y_cycle = np.exp(-0.5 * ((x - 0.5 * T) / sigma) ** 2)
        y = amplitude * y_cycle + offset
    else:
        if waveform not in _KNOWN_WAVEFORMS:
            warnings.warn(f'Неизвестная форма волны "{waveform}", используется синусоида', UserWarning)
        y = amplitude * np.sin(2 * np.pi * freq * t + phase_rad) + offset

    return t, np.asarray(y, dtype=np.float32)


def apply_filter(data: np.ndarray, sample_rate: float, filter_type: str,
                 f1: float, f2: float | None = None, order: int = 5,
                 approx: str = 'butter', rp: float = 1.0, rs: float = 40.0) -> np.ndarray:
    # Режим "без фильтра" и пустые данные возвращаем как есть.
    if filter_type == 'none' or filter_type is None:
        return data
    if data is None or data.size == 0:
        return data
    data = np.asarray(data, dtype=np.float64)
    # Чиним NaN/Inf до проектирования фильтра, чтобы sosfiltfilt не падал.
    if not np.isfinite(data).all():
        data = np.nan_to_num(data, nan=0.0, posinf=1.0, neginf=-1.0)

    nyquist = sample_rate / 2
    f_min = max(0.5, nyquist * 1e-6)
    f_max = nyquist * 0.999
    order = max(1, min(10, order))
    rp = max(0.1, min(6.0, rp))
    rs = max(10.0, min(80.0, rs))
    f1_safe = max(f_min, min(f_max, float(f1)))
    if filter_type == 'bandpass':
        # Нормализуем границы полосы и принудительно разводим их по частоте.
        f2_val = f1 * 2 if f2 is None else float(f2)
        f_low = max(f_min, min(f_max, min(f1_safe, f2_val)))
        f_high = max(f_min, min(f_max, max(f1_safe, f2_val)))
        if f_low >= f_high:
            f_high = min(f_max, f_low * 2)
        w_norm = [f_low / nyquist, f_high / nyquist]
        btype = 'band'
    elif filter_type == 'lowpass':
        w_norm = f1_safe / nyquist
        btype = 'low'
    elif filter_type == 'highpass':
        w_norm = f1_safe / nyquist
        btype = 'high'
    else:
        return data

    _approx = (approx or 'butter').lower()
    try:
        # Все варианты фильтров считаем в SOS-форме для численной устойчивости.
        if _approx == 'butter':
            sos = scipy_signal.butter(order, w_norm, btype=btype, output='sos')
        elif _approx == 'cheby1':
            sos = scipy_signal.cheby1(order, rp, w_norm, btype=btype, output='sos')
        elif _approx == 'cheby2':
            sos = scipy_signal.cheby2(order, rs, w_norm, btype=btype, output='sos')
        elif _approx == 'ellip':
            sos = scipy_signal.ellip(order, rp, rs, w_norm, btype=btype, output='sos')
        else:
            sos = scipy_signal.butter(order, w_norm, btype=btype, output='sos')
    except ValueError:
        return data

    try:
        if data.ndim == 1:
            return scipy_signal.sosfiltfilt(sos, data).astype(np.float32)
        return scipy_signal.sosfiltfilt(sos, data, axis=0).astype(np.float32)
    except ValueError:
        return data
