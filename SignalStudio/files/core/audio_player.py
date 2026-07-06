import threading
import numpy as np
import sounddevice as sd

"""Обертка над sounddevice: единое воспроизведение и остановка звука."""

_lock = threading.Lock()
_is_playing = False


def play(data: np.ndarray, sample_rate: int, blocking: bool = False) -> None:
    global _is_playing
    # Если уже что-то играет, сначала аккуратно останавливаем прошлый поток.
    with _lock:
        if _is_playing:
            try:
                sd.stop()
            except OSError:
                pass
            _is_playing = False
    if len(data) == 0:
        return
    # Приводим к float32 и 2D-форме, как ожидает sounddevice.
    data = np.asarray(data, dtype=np.float32)
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    try:
        sd.play(data, sample_rate)
        if blocking:
            sd.wait()
            with _lock:
                _is_playing = False
        else:
            with _lock:
                _is_playing = True
    except Exception as e:
        raise RuntimeError(f'Ошибка воспроизведения: {e}') from e


def stop() -> None:
    global _is_playing
    # Унифицированная остановка для всех экранов приложения.
    with _lock:
        try:
            sd.stop()
        except OSError:
            pass
        _is_playing = False
