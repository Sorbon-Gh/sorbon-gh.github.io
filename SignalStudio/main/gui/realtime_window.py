import threading
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QPushButton, QHBoxLayout, QLabel, QMessageBox
from PyQt6.QtCore import Qt, QTimer

import numpy as np
import sounddevice as sd

from core.fft import compute_fft_spectrum, compute_spectrogram
from core.config import STATUS_OK, STATUS_WARN
from gui.layout import create_plots_pane
from gui.icons import create_icon

"""Экран реального времени: захват микрофона, буферизация и online-анализ."""

BUFFER_SECONDS = 5
BLOCK_SIZE = 1024


def _get_input_sample_rate():
    # Берем частоту устройства ввода, а при ошибке используем безопасный дефолт.
    try:
        dev = sd.query_devices(kind='input')
        return int(dev['default_samplerate'])
    except Exception:
        return 44100


class RingBuffer:

    def __init__(self, size: int, dtype=np.float32):
        # Кольцевой буфер фиксированного размера для последних секунд сигнала.
        self.size = size
        self.data = np.zeros(size, dtype=dtype)
        self._write_pos = 0
        self._filled = 0
        self._lock = threading.Lock()

    def write(self, chunk: np.ndarray):
        # Записываем хвост чанка и корректно обрабатываем переход через конец буфера.
        n = min(len(chunk), self.size)
        chunk = chunk[-n:]
        with self._lock:
            if n <= self.size - self._write_pos:
                self.data[self._write_pos:self._write_pos + n] = chunk.astype(self.data.dtype)
            else:
                first = self.size - self._write_pos
                self.data[self._write_pos:] = chunk[:first].astype(self.data.dtype)
                self.data[:n - first] = chunk[first:].astype(self.data.dtype)
            self._write_pos = (self._write_pos + n) % self.size
            self._filled = min(self._filled + n, self.size)

    def read_active(self) -> np.ndarray:
        # Возвращаем данные в хронологическом порядке "от старых к новым".
        with self._lock:
            if self._filled < self.size:
                return self.data[:self._filled].copy()
            result = np.empty(self.size, dtype=self.data.dtype)
            part1 = self.size - self._write_pos
            result[:part1] = self.data[self._write_pos:].copy()
            result[part1:] = self.data[:self._write_pos].copy()
            return result

    def clear(self):
        with self._lock:
            self.data.fill(0)
            self._write_pos = 0
            self._filled = 0


class RealtimeWindow(QWidget):
    def __init__(self):
        # Инициализация экрана реального времени и таймера обновления графиков.
        super().__init__()
        self._sample_rate = _get_input_sample_rate()
        self._buffer_seconds = BUFFER_SECONDS
        self._buffer = RingBuffer(int(self._sample_rate * self._buffer_seconds))
        self._stream = None
        self._recording = False
        self._stream_warning = ''
        self._last_spectral_update = 0.0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        row = QHBoxLayout()
        self.toggle_btn = QPushButton(' Запуск захвата')
        self.toggle_btn.setObjectName('primaryButton')
        self.toggle_btn.setIcon(create_icon('start', 20, '#ffffff'))
        self.toggle_btn.clicked.connect(self._toggle_capture)
        row.addWidget(self.toggle_btn)
        self.status_ind = QLabel('')
        row.addWidget(self.status_ind)
        row.addStretch()
        layout.addLayout(row)

        vs, self.osc, self.fft, self.spec = create_plots_pane()
        layout.addWidget(vs)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_plots)

    def is_recording(self):
        return self._recording

    def stop_recording(self):
        if self._recording:
            self._stop()

    def _toggle_capture(self):
        # Одна кнопка работает как старт/стоп захвата.
        if self._recording:
            self._stop()
        else:
            self._start()

    def _recreate_buffer(self):
        self._buffer = RingBuffer(int(self._sample_rate * self._buffer_seconds))

    def _start(self):
        # Поднимаем поток ввода и синхронизируем UI-состояние под активный захват.
        self._sample_rate = _get_input_sample_rate()
        self._recreate_buffer()
        self._stream_warning = ''
        self._last_spectral_update = 0.0
        try:
            self._stream = sd.InputStream(samplerate=self._sample_rate, channels=1, blocksize=BLOCK_SIZE,
                                          dtype=np.float32, callback=self._audio_callback)
            self._stream.start()
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось открыть микрофон: {e}')
            return
        self._recording = True
        self.toggle_btn.setText(' Остановить захват')
        self.toggle_btn.setIcon(create_icon('pause', 20, '#ffffff'))
        self.status_ind.setText('● Захват')
        self.status_ind.setStyleSheet(f'color: {STATUS_OK};')
        self._timer.start(50)

    def _stop(self):
        # Полностью останавливаем поток и чистим визуализацию.
        self._recording = False
        self._timer.stop()
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except OSError:
                pass
            self._stream = None
        self.toggle_btn.setText(' Запуск захвата')
        self.toggle_btn.setIcon(create_icon('start', 20, '#ffffff'))
        self.status_ind.setText('')
        self.status_ind.setStyleSheet('')
        self.osc.clear()
        self.fft.clear()
        self.spec.clear()

    def _audio_callback(self, indata, _frames, _time_info, status):
        # Коллбэк аудиодрайвера: только быстрая запись в буфер без тяжелых расчетов.
        if status:
            self._stream_warning = str(status)
        if indata.size > 0:
            self._buffer.write(indata[:, 0].reshape(-1))

    def _update_status_label(self):
        if not self._recording:
            return
        if self._stream_warning:
            self.status_ind.setText(f'● Захват | {self._stream_warning}')
            self.status_ind.setStyleSheet(f'color: {STATUS_WARN};')
        else:
            self.status_ind.setText(f'● Захват | Буфер {self._buffer_seconds} с')
            self.status_ind.setStyleSheet(f'color: {STATUS_OK};')

    def _update_plots(self):
        # Осциллограмма обновляется чаще, спектральные графики - реже для стабильного FPS.
        if not self._recording or self._stream is None:
            return
        self._update_status_label()
        data = self._buffer.read_active()
        if data.size == 0:
            self.osc.clear()
            self.fft.clear()
            self.spec.clear()
            return
        osc_time = np.arange(data.size, dtype=np.float64) / self._sample_rate
        self.osc.update_data(osc_time, data, preserve_cursors=True)
        now = time.monotonic()
        if now - self._last_spectral_update < 0.15:
            return
        self._last_spectral_update = now
        spec_nperseg = min(2048, data.size)
        spec_f, spec_t, spec_db = compute_spectrogram(
            data, self._sample_rate, nperseg=spec_nperseg,
        )
        self.spec.update_spectrogram(spec_f, spec_t, spec_db)

        fft_len = min(data.size, 32768)
        fft_f, fft_db = compute_fft_spectrum(
            data, self._sample_rate, nperseg=fft_len, use_tail=True,
        )
        self.fft.update_spectrum(fft_f, fft_db)

    def closeEvent(self, event):
        if self._recording:
            self._stop()
        event.accept()
