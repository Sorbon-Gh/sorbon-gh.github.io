from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.config import FORM_MIN_WIDTH, PANEL_MAX_WIDTH, PANEL_MIN_WIDTH, VERT_SPLITTER_SIZES
from gui.controls import apply_numeric_locale
from gui.icons import create_icon

"""Переиспользуемые элементы компоновки интерфейса."""


class CollapsiblePanel(QFrame):

    toggled = pyqtSignal(bool)

    def __init__(self, title: str, parent=None):
        # Сворачиваемая секция для левой панели параметров.
        super().__init__(parent)
        self.setObjectName('collapsiblePanel')
        self._title = title
        self._expanded = True
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.header = QPushButton(f'  ▼ {title}')
        self.header.setObjectName('collapseHeader')
        self.header.setCheckable(True)
        self.header.setChecked(True)
        self.header.clicked.connect(self._toggle)
        layout.addWidget(self.header)
        self._container = QFrame()
        self._container.setObjectName('collapseContent')
        self._inner_layout = QVBoxLayout(self._container)
        self._inner_layout.setContentsMargins(12, 12, 12, 12)
        self._inner_layout.setSpacing(12)
        layout.addWidget(self._container)

    def _toggle(self):
        # Обновляем видимость контента и внешний вид заголовка.
        self._expanded = self.header.isChecked()
        self._container.setVisible(self._expanded)
        self.header.setText(f'  {"▼" if self._expanded else "▶"} {self._title}')
        self.toggled.emit(self._expanded)

    def set_content_widget(self, w: QWidget):
        # Гарантируем, что внутри панели всегда только один актуальный виджет.
        while self._inner_layout.count():
            item = self._inner_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._inner_layout.addWidget(w)


def create_left_panel(title: str, form: QWidget) -> QFrame:
    # Оборачиваем форму параметров в скролл и применяем числовую локаль.
    wrapper = QFrame()
    wrapper.setObjectName('leftPanel')
    wrapper.setMinimumWidth(PANEL_MIN_WIDTH)
    wrapper.setMaximumWidth(PANEL_MAX_WIDTH)
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    coll = CollapsiblePanel(title)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setStyleSheet('QScrollArea { background: transparent; }')
    form.setMinimumWidth(FORM_MIN_WIDTH)
    apply_numeric_locale(form)
    scroll.setWidget(form)
    coll.set_content_widget(scroll)
    layout.addWidget(coll)
    return wrapper


def create_apply_play_stop_row(
    apply_cb: Callable[[], None],
    play_cb: Callable[[], None],
    stop_cb: Callable[[], None],
) -> QHBoxLayout:
    # Единая кнопочная строка для всех режимов (применить, play, stop).
    row = QHBoxLayout()
    
    apply_btn = QPushButton(' Применить')
    apply_btn.setObjectName('primaryButton')
    apply_btn.setIcon(create_icon('apply', 20, '#ffffff'))
    apply_btn.setMinimumWidth(130)
    apply_btn.setToolTip('Применить параметры (F5)')
    apply_btn.clicked.connect(apply_cb)
    row.addWidget(apply_btn)
    
    play_btn = QToolButton()
    play_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    play_btn.setIcon(create_icon('play', 22, '#00ff41'))
    play_btn.setToolTip('Воспроизвести')
    play_btn.clicked.connect(play_cb)
    play_btn.setFixedSize(40, 40)
    row.addWidget(play_btn)
    
    stop_btn = QToolButton()
    stop_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    stop_btn.setIcon(create_icon('stop', 22, '#ff4444'))
    stop_btn.setToolTip('Стоп')
    stop_btn.clicked.connect(stop_cb)
    stop_btn.setFixedSize(40, 40)
    row.addWidget(stop_btn)
    
    return row


def create_plots_pane(sizes: list[int] | None = None) -> tuple[QSplitter, "OscilloscopeWidget", "FFTSpectrumWidget", "SpectrogramWidget"]:
    # Создаем вертикальную связку из трех графиков в одинаковом стиле.
    from gui.widgets.oscilloscope_widget import OscilloscopeWidget
    from gui.widgets.fft_spectrum_widget import FFTSpectrumWidget
    from gui.widgets.spectrogram_widget import SpectrogramWidget

    vs = QSplitter(Qt.Orientation.Vertical)
    osc = OscilloscopeWidget()
    fft = FFTSpectrumWidget()
    spec = SpectrogramWidget()
    vs.addWidget(osc)
    vs.addWidget(fft)
    vs.addWidget(spec)
    vs.setSizes(sizes if sizes is not None else VERT_SPLITTER_SIZES)
    return vs, osc, fft, spec
