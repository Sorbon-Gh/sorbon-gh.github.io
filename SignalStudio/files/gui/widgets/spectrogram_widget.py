from PyQt6.QtWidgets import QWidget, QVBoxLayout
from pyqtgraph import ColorBarItem, ColorMap, ImageItem, PlotWidget
import numpy as np

from core.config import PLOT_BG, SPECTRO_COLORS

"""Виджет спектрограммы с динамической цветовой шкалой."""


class SpectrogramWidget(QWidget):

    def __init__(self, parent=None):
        # Инициализируем ImageItem + ColorBar и применяем общую палитру.
        super().__init__(parent)
        self.plot = PlotWidget(background=PLOT_BG)
        self.plot.setLabel('left', 'Частота, Гц', **{'color': '#1890ff', 'font-size': '10pt'})
        self.plot.setLabel('bottom', 'Время, с', **{'color': '#1890ff', 'font-size': '10pt'})
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        self.plot.getPlotItem().getViewBox().setBackgroundColor(PLOT_BG)
        self.plot.getPlotItem().invertX(False)
        self.plot.getPlotItem().getAxis('left').setPen('#1890ff')
        self.plot.getPlotItem().getAxis('bottom').setPen('#1890ff')
        self.plot.getPlotItem().getAxis('left').setTextPen('#c9d1d9')
        self.plot.getPlotItem().getAxis('bottom').setTextPen('#c9d1d9')
        self.img = ImageItem()
        self.plot.addItem(self.img)
        self._color_map = self._build_colormap()
        self.img.setLookupTable(self._color_map.getLookupTable(0, 1, 256, alpha=False))
        self.colorbar = ColorBarItem(values=(-120.0, 0.0), colorMap=self._color_map)
        self.colorbar.setImageItem(self.img, insert_in=self.plot.getPlotItem())
        self._levels = (-120.0, 0.0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)
        self.clear()

    def _build_colormap(self):
        # Собираем ColorMap из конфигурации проекта.
        pos = np.array([p for p, _ in SPECTRO_COLORS])
        color = np.array([c for _, c in SPECTRO_COLORS], dtype=np.ubyte)
        return ColorMap(pos, color)

    def _axis_bounds(self, axis: np.ndarray) -> tuple[float, float]:
        # Переводим ось в границы пикселей изображения (центр +- полшага).
        axis = np.asarray(axis, dtype=np.float64)
        if axis.size == 0:
            return 0.0, 1.0
        if axis.size == 1:
            step = 1.0
        else:
            step = float(np.median(np.diff(axis)))
            if not np.isfinite(step) or step == 0.0:
                step = float(axis[-1] - axis[0]) / max(axis.size - 1, 1)
            if not np.isfinite(step) or step == 0.0:
                step = 1.0
        start = float(axis[0]) - 0.5 * step
        stop = float(axis[-1]) + 0.5 * step
        return (start, stop) if start <= stop else (stop, start)

    def _update_levels(self, values: np.ndarray) -> tuple[float, float]:
        # Автоуровни сглаживаем, чтобы цветовая шкала не "прыгала" между кадрами.
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            self._levels = (-120.0, 0.0)
            return self._levels
        target_top = float(np.nanpercentile(finite, 99.5))
        if not np.isfinite(target_top):
            target_top = 0.0
        previous_bottom, previous_top = self._levels
        top = max(target_top, previous_top - 1.0)
        bottom = top - 90.0
        if not np.isfinite(bottom) or not np.isfinite(top) or bottom >= top:
            bottom, top = previous_bottom, previous_top
        self._levels = (bottom, top)
        return self._levels

    def update_spectrogram(self, f: np.ndarray, t: np.ndarray, Sxx: np.ndarray):
        # Обновляем картинку спектрограммы, диапазон осей и цветовую шкалу.
        if Sxx.size == 0:
            self.clear()
            return
        time_start, time_stop = self._axis_bounds(t)
        freq_start, freq_stop = self._axis_bounds(f)
        levels = self._update_levels(np.asarray(Sxx, dtype=np.float64))
        self.img.setImage(
            np.asarray(Sxx, dtype=np.float64),
            rect=[
                time_start,
                freq_start,
                max(1e-9, time_stop - time_start),
                max(1e-9, freq_stop - freq_start),
            ],
            levels=levels,
            autoLevels=False,
        )
        self.colorbar.setLevels(levels)
        self.plot.setXRange(time_start, time_stop, padding=0.0)
        self.plot.setYRange(freq_start, freq_stop, padding=0.0)

    def clear(self):
        # Пустая матрица-заглушка, чтобы виджет оставался в корректном состоянии.
        self.img.setImage(np.zeros((1, 1), dtype=np.float64), rect=[0.0, 0.0, 1.0, 1.0], levels=self._levels, autoLevels=False)
        self.colorbar.setLevels(self._levels)
