from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
                             QLabel, QComboBox, QPushButton, QFileDialog, QApplication, QMessageBox)
from PyQt6.QtCore import Qt

import numpy as np

from core.fft import build_analysis_frames
from core.wav_handler import load_wav
from core.config import SPLITTER_SIZES, BG_CARD
from core.audio_player import stop
from gui.widgets.filter_panel import FilterPanel
from gui.layout import create_apply_play_stop_row, create_left_panel, create_plots_pane
from gui.io import save_wav_dialog, play_with_error_handling
from gui.icons import create_icon

"""Экран анализатора WAV: загрузка, выбор канала, фильтрация и визуализация."""


class AnalyzerWindow(QWidget):

    def __init__(self):
        # Держим исходные и отфильтрованные данные отдельно, чтобы не терять оригинал.
        super().__init__()
        self._data = np.array([])
        self._filtered = np.array([])
        self._sample_rate = 44100
        self._duration = 0
        self._channels = 1
        self._filename = ''
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_panel())
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 8, 8, 8)
        vs, self.osc, self.fft, self.spec = create_plots_pane()
        rl.addWidget(vs)
        splitter.addWidget(right)
        splitter.setSizes(SPLITTER_SIZES)
        layout.addWidget(splitter)

    def _build_panel(self) -> QWidget:
        # Формируем левую панель управления загрузкой и анализом файла.
        form = QWidget()
        fl = QVBoxLayout(form)
        fl.setSpacing(10)

        lb = QPushButton(' Загрузить WAV')
        lb.setObjectName('primaryButton')
        lb.setIcon(create_icon('open', 20, '#ffffff'))
        lb.clicked.connect(self.load_wav)
        fl.addWidget(lb)

        fl.addWidget(QLabel('Канал:'))
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(['L+R (сумма)', 'Левый', 'Правый'])
        self.channel_combo.setEnabled(False)
        self.channel_combo.currentIndexChanged.connect(self._analyze)
        fl.addWidget(self.channel_combo)

        self.info_label = QLabel('Файл: —\nЧастота: —\nДлительность: —\nКаналы: —')
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(f'padding: 8px; background: {BG_CARD}; border-radius: 4px;')
        fl.addWidget(self.info_label)

        self.filter_panel = FilterPanel(f1_default=300, f2_default=3400)
        self.filter_panel.set_frequency_limit(self._sample_rate * 0.5 * 0.99)
        fl.addWidget(self.filter_panel)

        row_btns = create_apply_play_stop_row(self._analyze, self._play, stop)
        fl.addLayout(row_btns)
        fl.addStretch()
        return create_left_panel('Файл', form)

    def _get_channel_data(self) -> np.ndarray:
        # Для стерео даем выбор: левый, правый или усредненный канал.
        if len(self._data) == 0:
            return np.array([])
        if self._data.ndim == 1:
            return self._data
        idx = self.channel_combo.currentIndex()
        if idx == 1:
            return self._data[:, 0]
        if idx == 2:
            return self._data[:, 1]
        return (self._data[:, 0] + self._data[:, 1]) * 0.5

    def _clear_views(self):
        # Полная очистка графиков и промежуточных данных анализа.
        self._filtered = np.array([])
        self.osc.clear()
        self.spec.clear()
        self.fft.clear()

    def _default_osc_window(self, signal_length: int) -> float | None:
        # В анализаторе показываем короткое окно, чтобы лучше видеть форму сигнала.
        if signal_length <= 1:
            return None
        duration_s = signal_length / self._sample_rate
        return min(duration_s, 0.01)

    def load_wav(self):
        # Загружаем WAV, обновляем карточку файла и запускаем пересчет графиков.
        path, _ = QFileDialog.getOpenFileName(self, 'Открыть WAV', '', 'WAV (*.wav);;Все (*)')
        if not path:
            return
        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self._data, self._sample_rate, self._channels = load_wav(path)
            self._filename = Path(path).name
            self._duration = len(self._data) / self._sample_rate
            self.filter_panel.set_frequency_limit(self._sample_rate * 0.5 * 0.99)
            self.info_label.setText(
                f'Файл: {self._filename}\n'
                f'Частота: {self._sample_rate} Гц\n'
                f'Длительность: {self._duration:.2f} с\n'
                f'Каналы: {"стерео" if self._channels == 2 else "моно"}'
            )
            self.channel_combo.setEnabled(self._channels == 2)
            self._analyze()
        except Exception as e:
            self._data = np.array([])
            self._filename = ''
            self._duration = 0
            self._channels = 1
            self.info_label.setText('Файл: —\nЧастота: —\nДлительность: —\nКаналы: —')
            self.channel_combo.setEnabled(False)
            self._clear_views()
            QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить файл: {e}')
        finally:
            QApplication.restoreOverrideCursor()

    def _analyze(self):
        # Расчет во всех представлениях делаем на выбранном канале и после фильтра.
        if len(self._data) == 0:
            self._clear_views()
            return
        y = self._get_channel_data()
        if y.size == 0:
            self._clear_views()
            return
        y = self.filter_panel.apply_to(y, self._sample_rate)
        self._filtered = y
        frames = build_analysis_frames(y, self._sample_rate)
        self.osc.update_data(
            frames.time_axis,
            frames.signal,
            visible_time_window=self._default_osc_window(len(y)),
        )
        self.spec.update_spectrogram(frames.spectrogram_freq, frames.spectrogram_time, frames.spectrogram_db)
        self.fft.update_spectrum(frames.spectrum_freq, frames.spectrum_db)

    def _play(self):
        # Воспроизводим только актуальный отфильтрованный буфер.
        if len(self._filtered) == 0:
            self._analyze()
        if len(self._filtered) == 0:
            return
        play_with_error_handling(self, self._filtered, self._sample_rate)

    def save_wav(self):
        # Сохраняем ровно то, что сейчас видим/слышим после обработки.
        if len(self._filtered) == 0:
            QMessageBox.information(self, 'Сохранение', 'Сначала загрузите WAV и нажмите Применить.')
            return
        save_wav_dialog(self, self._filtered, self._sample_rate, self._filename or '')
