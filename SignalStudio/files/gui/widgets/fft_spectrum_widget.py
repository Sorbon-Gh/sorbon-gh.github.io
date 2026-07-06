from PyQt6.QtWidgets import QWidget, QVBoxLayout
from pyqtgraph import PlotWidget
import numpy as np

from core.config import PLOT_BG, OSC_CURVE

"""Виджет амплитудного спектра (частота - уровень в дБ)."""


class FFTSpectrumWidget(QWidget):

    def __init__(self, parent=None):
        # Настраиваем единый стиль спектрального графика.
        super().__init__(parent)
        self.plot = PlotWidget(background=PLOT_BG)
        self.plot.setLabel('left', 'Амплитуда, дБ', **{'color': '#1890ff', 'font-size': '10pt'})
        self.plot.setLabel('bottom', 'Частота, Гц', **{'color': '#1890ff', 'font-size': '10pt'})
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        self.plot.getPlotItem().getViewBox().setBackgroundColor(PLOT_BG)
        self.plot.getPlotItem().invertX(False)
        self.plot.getPlotItem().getAxis('left').setPen('#1890ff')
        self.plot.getPlotItem().getAxis('bottom').setPen('#1890ff')
        self.plot.getPlotItem().getAxis('left').setTextPen('#c9d1d9')
        self.plot.getPlotItem().getAxis('bottom').setTextPen('#c9d1d9')
        self.curve = self.plot.plot(pen={'color': OSC_CURVE, 'width': 1.5})
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)

    def update_spectrum(self, f: np.ndarray, db: np.ndarray):
        # Защищаемся от NaN/Inf и аккуратно пересчитываем пределы осей.
        f = np.asarray(f, dtype=np.float64)
        db = np.asarray(db, dtype=np.float64)
        n = min(len(f), len(db))
        if n > 0:
            fx = f[:n]
            dy = np.nan_to_num(db[:n], nan=0.0, posinf=0.0, neginf=-120.0)
            if n > 1 and fx[0] > fx[-1]:
                fx = fx[::-1]
                dy = dy[::-1]
            self.curve.setData(fx, dy)
            self.plot.setXRange(max(0.0, float(fx[0])), float(fx[-1]), padding=0.01)
            y_min = float(np.nanmin(dy))
            y_max = float(np.nanmax(dy))
            if np.isfinite(y_min) and np.isfinite(y_max):
                if y_min == y_max:
                    y_min -= 3.0
                    y_max += 3.0
                self.plot.setYRange(y_min - 3.0, y_max + 3.0, padding=0.0)
        else:
            self.curve.setData([], [])

    def clear(self):
        # Быстрый сброс спектра без пересоздания виджета.
        self.curve.setData([], [])
