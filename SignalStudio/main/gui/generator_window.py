from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
                             QLabel, QComboBox, QSlider, QSpinBox,
                             QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut, QKeySequence

import numpy as np

from core.config import SAMPLE_RATES, WAVEFORM_MAP, SPLITTER_SIZES
from core.fft import build_analysis_frames
from core.signal_processor import generate_signal
from core.audio_player import stop
from gui.layout import create_apply_play_stop_row, create_left_panel, create_plots_pane
from gui.controls import SIDoubleSpinBox, bind_slider_spin
from gui.widgets.filter_panel import FilterPanel
from gui.io import save_wav_dialog, play_with_error_handling

"""Экран генератора: формирование сигнала, фильтрация, анализ и экспорт WAV."""


class GeneratorWindow(QWidget):

    def __init__(self):
        # Храним последний рассчитанный сигнал, чтобы быстро воспроизводить/сохранять.
        super().__init__()
        self._t = np.array([])
        self._y = np.array([])
        self._sample_rate = 44100
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_panel())
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 8, 8)
        vert_split, self.osc, self.fft, self.spec = create_plots_pane()
        right_layout.addWidget(vert_split)
        splitter.addWidget(right)
        splitter.setSizes(SPLITTER_SIZES)
        layout.addWidget(splitter)
        QShortcut(QKeySequence('F5'), self, self._apply)
        self.sr_combo.currentIndexChanged.connect(self._sync_sampling_controls)
        self._sync_sampling_controls()
        self._apply()

    def _build_panel(self) -> QWidget:
        # Вся левая колонка управления генератором собрана в одном месте.
        form = QWidget()
        fl = QVBoxLayout(form)
        fl.setSpacing(10)

        fl.addWidget(QLabel('Форма:'))
        self.wave_combo = QComboBox()
        for label, _ in WAVEFORM_MAP:
            self.wave_combo.addItem(label)
        self.wave_combo.setCurrentIndex(0)
        fl.addWidget(self.wave_combo)

        fl.addWidget(QLabel('Частота дискретизации:'))
        self.sr_combo = QComboBox()
        self.sr_combo.addItems([str(r) for r in SAMPLE_RATES])
        idx = SAMPLE_RATES.index(44100) if 44100 in SAMPLE_RATES else 0
        self.sr_combo.setCurrentIndex(idx)
        fl.addWidget(self.sr_combo)

        fl.addWidget(QLabel('Частота:'))
        fr = QHBoxLayout()
        self.freq_slider = QSlider(Qt.Orientation.Horizontal)
        self.freq_slider.setRange(0, 96000)
        self.freq_slider.setValue(440)
        fr.addWidget(self.freq_slider, 1)
        self.freq_spin = SIDoubleSpinBox('Hz')
        self.freq_spin.setRange(0.001, 10_000_000)
        self.freq_spin.setValue(440)
        fr.addWidget(self.freq_spin)
        bind_slider_spin(
            self.freq_slider, self.freq_spin,
            lambda v: max(v, 0.001),
            lambda v: int(np.clip(round(v), 0, self.freq_slider.maximum())),
        )
        fl.addLayout(fr)

        fl.addWidget(QLabel('Амплитуда:'))
        ar = QHBoxLayout()
        self.amp_slider = QSlider(Qt.Orientation.Horizontal)
        self.amp_slider.setRange(0, 1000)
        self.amp_slider.setValue(65)
        ar.addWidget(self.amp_slider, 1)
        self.amp_spin = SIDoubleSpinBox('V')
        self.amp_spin.setRange(0, 10)
        self.amp_spin.setSingleStep(0.01)
        self.amp_spin.setValue(0.65)
        ar.addWidget(self.amp_spin)
        bind_slider_spin(
            self.amp_slider, self.amp_spin,
            lambda v: v / 100,
            lambda v: int(np.clip(v * 100, 0, self.amp_slider.maximum())),
        )
        fl.addLayout(ar)

        fl.addWidget(QLabel('Смещение (DC):'))
        dr = QHBoxLayout()
        self.dc_slider = QSlider(Qt.Orientation.Horizontal)
        self.dc_slider.setRange(-1000, 1000)
        self.dc_slider.setValue(0)
        dr.addWidget(self.dc_slider, 1)
        self.dc_spin = SIDoubleSpinBox('V')
        self.dc_spin.setRange(-10, 10)
        self.dc_spin.setSingleStep(0.01)
        self.dc_spin.setValue(0)
        dr.addWidget(self.dc_spin)
        bind_slider_spin(
            self.dc_slider, self.dc_spin,
            lambda v: v / 100,
            lambda v: int(np.clip(v * 100, self.dc_slider.minimum(), self.dc_slider.maximum())),
        )
        fl.addLayout(dr)

        fl.addWidget(QLabel('Длительность:'))
        self.dur_spin = SIDoubleSpinBox('s')
        self.dur_spin.setRange(0.0001, 600)
        self.dur_spin.setValue(2)
        fl.addWidget(self.dur_spin)

        fl.addWidget(QLabel('Фаза:'))
        pr = QHBoxLayout()
        self.phase_slider = QSlider(Qt.Orientation.Horizontal)
        self.phase_slider.setRange(0, 360)
        pr.addWidget(self.phase_slider, 1)
        self.phase_spin = QSpinBox()
        self.phase_spin.setRange(0, 360)
        self.phase_spin.setSuffix(' °')
        bind_slider_spin(self.phase_slider, self.phase_spin, float, int)
        pr.addWidget(self.phase_spin)
        fl.addLayout(pr)

        fl.addWidget(QLabel('Заполнение:'))
        du = QHBoxLayout()
        self.duty_slider = QSlider(Qt.Orientation.Horizontal)
        self.duty_slider.setRange(1, 99)
        self.duty_slider.setValue(50)
        du.addWidget(self.duty_slider, 1)
        self.duty_spin = QSpinBox()
        self.duty_spin.setRange(1, 99)
        self.duty_spin.setValue(50)
        self.duty_spin.setSuffix(' %')
        bind_slider_spin(self.duty_slider, self.duty_spin, float, int)
        du.addWidget(self.duty_spin)
        fl.addLayout(du)

        self.filter_panel = FilterPanel(f1_default=1000, f2_default=4000)
        fl.addWidget(self.filter_panel)

        fg2 = QGroupBox('Спектральный анализ')
        fl3 = QVBoxLayout(fg2)
        fl3.addWidget(QLabel('Окно:'))
        self.fft_window = QComboBox()
        self.fft_window.addItems(['hann', 'hamming', 'blackman', 'kaiser'])
        fl3.addWidget(self.fft_window)
        fl3.addWidget(QLabel('Размер (nperseg):'))
        self.fft_nperseg = QSpinBox()
        self.fft_nperseg.setRange(128, 8192)
        self.fft_nperseg.setValue(4096)
        fl3.addWidget(self.fft_nperseg)
        fl.addWidget(fg2)

        row_btns = create_apply_play_stop_row(self._apply, self._play, stop)
        fl.addLayout(row_btns)
        fl.addStretch()
        return create_left_panel('Параметры', form)

    def _sync_sampling_controls(self):
        # При смене Fs сразу ограничиваем частоты генератора и панели фильтра.
        self._sample_rate = SAMPLE_RATES[self.sr_combo.currentIndex()]
        nyquist = max(1.0, self._sample_rate * 0.5 * 0.99)
        self.freq_slider.setRange(0, max(1, int(nyquist)))
        self.freq_spin.setRange(0.001, 10_000_000)
        self.filter_panel.set_frequency_limit(nyquist)

    def _default_osc_window(self, waveform: str, frequency_hz: float, duration_s: float) -> float:
        # Для периодики показываем несколько периодов, для шума/DC - короткое стабильное окно.
        if waveform in {'noise', 'dc'}:
            return min(duration_s, 0.2)
        base = 4.0 / max(abs(frequency_hz), 1e-6)
        return min(duration_s, min(0.2, max(0.01, base)))

    def _apply(self):
        # Полный цикл: генерация -> фильтрация -> пересчет всех графиков.
        self._sync_sampling_controls()
        waveform = WAVEFORM_MAP[self.wave_combo.currentIndex()][1]
        frequency_hz = self.freq_spin.value()
        duration_s = self.dur_spin.value()
        t, y = generate_signal(
            waveform, frequency_hz, self._sample_rate,
            duration_s, self.amp_spin.value(), self.dc_spin.value(),
            self.phase_spin.value(), self.duty_spin.value() / 100.0
        )
        y = self.filter_panel.apply_to(y, self._sample_rate)
        self._t, self._y = t, y
        win = self.fft_window.currentText()
        nperseg = self.fft_nperseg.value()
        frames = build_analysis_frames(y, self._sample_rate, nperseg=nperseg, window=win)
        self.osc.update_data(
            frames.time_axis,
            frames.signal,
            visible_time_window=self._default_osc_window(waveform, frequency_hz, duration_s),
        )
        self.spec.update_spectrogram(frames.spectrogram_freq, frames.spectrogram_time, frames.spectrogram_db)
        self.fft.update_spectrum(frames.spectrum_freq, frames.spectrum_db)

    def _play(self):
        # Если сигнал еще не рассчитан, сначала считаем с текущими параметрами.
        if len(self._y) == 0:
            self._apply()
        play_with_error_handling(self, self._y, self._sample_rate)

    def save_wav(self):
        # В файл пишем только готовый (последний рассчитанный) сигнал.
        if len(self._y) == 0:
            QMessageBox.information(self, 'Сохранение', 'Сначала нажмите Применить для генерации сигнала.')
            return
        save_wav_dialog(self, self._y, self._sample_rate, '')
