from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from pyqtgraph import PlotWidget, InfiniteLine
import numpy as np

from core.config import PLOT_BG, OSC_CURVE, CURSOR1, CURSOR2, si_format

"""Виджет осциллограммы с курсорами и автоматическими измерениями."""


class OscilloscopeWidget(QWidget):

    def __init__(self, parent=None):
        # Инициализируем график и два курсора для интерактивных измерений.
        super().__init__(parent)
        self._t = np.array([])
        self._y = np.array([])
        self.plot = PlotWidget(background=PLOT_BG)
        self.plot.setLabel('left', 'Амплитуда', units='V', **{'color': '#1890ff', 'font-size': '10pt'})
        self.plot.setLabel('bottom', 'Время', units='s', **{'color': '#1890ff', 'font-size': '10pt'})
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        self.plot.getPlotItem().getViewBox().setBackgroundColor(PLOT_BG)
        self.plot.getPlotItem().invertX(False)
        self.plot.getPlotItem().getAxis('left').setPen('#1890ff')
        self.plot.getPlotItem().getAxis('bottom').setPen('#1890ff')
        self.plot.getPlotItem().getAxis('left').setTextPen('#c9d1d9')
        self.plot.getPlotItem().getAxis('bottom').setTextPen('#c9d1d9')
        self.curve = self.plot.plot(pen={'color': OSC_CURVE, 'width': 1.5})
        self.curve.setDownsampling(auto=True, method='peak')
        self.curve.setClipToView(True)
        self.cursor1 = InfiniteLine(pos=0, angle=90, movable=True, pen={'color': CURSOR1, 'width': 2})
        self.cursor2 = InfiniteLine(pos=0, angle=90, movable=True, pen={'color': CURSOR2, 'width': 2})
        self.plot.addItem(self.cursor1)
        self.plot.addItem(self.cursor2)
        self.cursor1.sigPositionChanged.connect(self._on_cursor_moved)
        self.cursor2.sigPositionChanged.connect(self._on_cursor_moved)

        self.meas_label = QLabel('Vpp: —  |  RMS: —  |  freq: —  |  period: —  |  Δt: —  |  ΔV: —')
        self.meas_label.setStyleSheet(
            f'color: #00ff41; font-size: 10pt; font-weight: 600; padding: 6px 12px;'
            f'background: #001a0a; border: 1px solid #1890ff; border-radius: 6px;'
            f'font-family: "Consolas", "Courier New", monospace;'
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)
        layout.addWidget(self.meas_label)

    def _on_cursor_moved(self):
        self._update_measurements()

    def _estimate_frequency(self) -> tuple[float | None, float | None]:
        # Оцениваем частоту по БПФ выбранного фрагмента между курсорами.
        if len(self._y) < 64 or len(self._t) != len(self._y):
            return None, None
        x1, x2 = self.cursor1.value(), self.cursor2.value()
        i1 = int(np.clip(np.searchsorted(self._t, min(x1, x2)), 0, len(self._t) - 1))
        i2 = int(np.clip(np.searchsorted(self._t, max(x1, x2)), 1, len(self._t)))
        if i2 - i1 < 64:
            segment = self._y[-min(len(self._y), 4096):]
            time_axis = self._t[-min(len(self._t), 4096):]
        else:
            segment = self._y[i1:i2]
            time_axis = self._t[i1:i2]
        if len(segment) < 64:
            return None, None
        n = min(len(segment), 8192)
        signal = segment[-n:] if len(segment) > n else segment
        time_axis = time_axis[-n:] if len(time_axis) > n else time_axis
        dt = float(np.median(np.diff(time_axis))) if len(time_axis) > 1 else 1.0 / 44100
        if not np.isfinite(dt) or dt <= 0:
            return None, None
        centered = signal - np.mean(signal)
        rms = float(np.sqrt(np.mean(centered ** 2)))
        if not np.isfinite(rms) or rms <= 1e-6:
            return None, None
        window = np.hanning(len(centered))
        spectrum = np.abs(np.fft.rfft(centered * window))
        if spectrum.size < 3:
            return None, None
        spectrum[0] = 0.0
        peak_idx = int(np.argmax(spectrum))
        peak_value = float(spectrum[peak_idx])
        noise_floor = float(np.median(spectrum[1:])) if spectrum.size > 1 else 0.0
        if not np.isfinite(peak_value) or peak_value <= 0.0:
            return None, None
        if peak_value < max(2.0 * max(noise_floor, 1e-12), 0.01 * float(np.sum(spectrum))):
            return None, None
        freq_axis = np.fft.rfftfreq(len(centered), d=dt)
        if peak_idx <= 0 or peak_idx >= len(freq_axis):
            return None, None
        freq = float(freq_axis[peak_idx])
        if not np.isfinite(freq) or freq <= 0.0:
            return None, None
        period = 1.0 / freq
        total_time = float(time_axis[-1] - time_axis[0]) if len(time_axis) > 1 else 0.0
        if period <= 0 or period > total_time:
            return None, None
        return freq, period

    def _update_measurements(self):
        # Пересчет подписи измерений (Vpp, RMS, freq/period, Delta t/V).
        vpp = rms = freq = period = dt = dv = None
        if len(self._y) > 0 and len(self._t) == len(self._y):
            vpp = float(np.ptp(self._y))
            centered = self._y - np.mean(self._y)
            rms = float(np.sqrt(np.mean(centered ** 2))) if len(centered) > 0 else None
            freq, period = self._estimate_frequency()
            x1, x2 = self.cursor1.value(), self.cursor2.value()
            if len(self._t) > 0 and len(self._y) > 0:
                last = min(len(self._t), len(self._y)) - 1
                i1 = int(np.clip(np.searchsorted(self._t, x1), 0, last))
                i2 = int(np.clip(np.searchsorted(self._t, x2), 0, last))
                dt = abs(self._t[i2] - self._t[i1])
                dv = abs(float(self._y[i2]) - float(self._y[i1]))

        parts = []
        parts.append(f'Vpp: {si_format(vpp, "V")}' if vpp is not None else 'Vpp: —')
        parts.append(f'RMS: {si_format(rms, "V")}' if rms is not None and np.isfinite(rms) else 'RMS: —')
        parts.append(f'freq: {si_format(freq, "Hz")}' if freq is not None and freq > 0 else 'freq: —')
        parts.append(f'period: {si_format(period, "s")}' if period is not None and period > 0 else 'period: —')
        parts.append(f'Δt: {si_format(dt, "s")}' if dt is not None else 'Δt: —')
        parts.append(f'ΔV: {si_format(dv, "V")}' if dv is not None else 'ΔV: —')
        self.meas_label.setText('  |  '.join(parts))

    def update_data(
        self,
        t: np.ndarray,
        y: np.ndarray,
        preserve_cursors: bool = False,
        visible_time_window: float | None = None,
    ):
        # Обновляем данные, масштаб графика и позиции курсоров.
        self._t = np.asarray(t, dtype=np.float64) if len(t) > 0 else np.array([])
        self._y = np.asarray(y, dtype=np.float64) if len(y) > 0 else np.array([])
        if len(self._t) > 1 and self._t[0] > self._t[-1]:
            self._t = self._t[::-1]
            self._y = self._y[::-1]
        self.curve.setData(self._t, self._y)
        if len(self._t) > 1:
            x_start = float(self._t[0])
            x_stop = float(self._t[-1])
            if visible_time_window is not None and visible_time_window > 0:
                x_stop = min(x_stop, x_start + float(visible_time_window))
            self.plot.setXRange(x_start, x_stop, padding=0.01)
        if len(self._y) > 0:
            y_min = float(np.nanmin(self._y))
            y_max = float(np.nanmax(self._y))
            if np.isfinite(y_min) and np.isfinite(y_max):
                pad = max(0.02, 0.1 * max(abs(y_min), abs(y_max), y_max - y_min))
                if y_min == y_max:
                    y_min -= pad
                    y_max += pad
                self.plot.setYRange(y_min - pad, y_max + pad, padding=0.0)
        if not preserve_cursors and len(self._t) > 0:
            x_start = float(self._t[0])
            x_stop = float(self._t[-1]) if len(self._t) > 1 else x_start
            if visible_time_window is not None and visible_time_window > 0:
                x_stop = min(x_stop, x_start + float(visible_time_window))
            self.cursor1.setValue(x_start)
            self.cursor2.setValue(x_stop)
        self._update_measurements()

    def clear(self):
        # Сброс графика и измерений в начальное состояние.
        self._t = np.array([])
        self._y = np.array([])
        self.curve.setData([], [])
        self.cursor1.setValue(0)
        self.cursor2.setValue(0)
        self.meas_label.setText('Vpp: —  |  RMS: —  |  freq: —  |  period: —  |  Δt: —  |  ΔV: —')
