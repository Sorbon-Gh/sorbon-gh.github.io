import numpy as np
from PyQt6.QtWidgets import (QComboBox, QDoubleSpinBox, QGroupBox, QHBoxLayout,
                             QLabel, QMessageBox, QSpinBox, QVBoxLayout)

from core.config import FILTER_KEYS, FILTER_LABELS, FILTER_APPROX_KEYS, FILTER_APPROX_LABELS
from core.signal_processor import apply_filter
from gui.controls import SIDoubleSpinBox

"""Панель параметров фильтра с динамическим показом релевантных полей."""


class FilterPanel(QGroupBox):

    def __init__(self, f1_default: float = 1000, f2_default: float = 4000, parent=None):
        # Единая панель фильтра используется и в генераторе, и в анализаторе.
        super().__init__('Фильтр', parent)
        fl = QVBoxLayout(self)
        fl.addWidget(QLabel('Форма:'))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(FILTER_LABELS)
        fl.addWidget(self.filter_combo)
        self.approx_label = QLabel('Аппроксимация:')
        fl.addWidget(self.approx_label)
        self.approx_combo = QComboBox()
        self.approx_combo.addItems(FILTER_APPROX_LABELS)
        fl.addWidget(self.approx_combo)

        rp_rs_row = QHBoxLayout()
        self.rp_label = QLabel('Rp, дБ:')
        self.rp_spin = QDoubleSpinBox()
        self.rp_spin.setRange(0.1, 6.0)
        self.rp_spin.setValue(1.0)
        self.rp_spin.setSingleStep(0.1)
        self.rp_spin.setDecimals(1)
        rp_rs_row.addWidget(self.rp_label)
        rp_rs_row.addWidget(self.rp_spin)
        self.rs_label = QLabel('Rs, дБ:')
        self.rs_spin = QDoubleSpinBox()
        self.rs_spin.setRange(10.0, 80.0)
        self.rs_spin.setValue(40.0)
        self.rs_spin.setSingleStep(1.0)
        self.rs_spin.setDecimals(0)
        rp_rs_row.addWidget(self.rs_label)
        rp_rs_row.addWidget(self.rs_spin)
        fl.addLayout(rp_rs_row)
        self._rp_rs_widgets = (self.rp_label, self.rp_spin, self.rs_label, self.rs_spin)

        fr = QHBoxLayout()
        self.f1_label = QLabel('Fc:')
        self.f1_spin = SIDoubleSpinBox('Hz')
        self.f1_spin.setRange(0, 10_000_000)
        self.f1_spin.setValue(f1_default)
        fr.addWidget(self.f1_label)
        fr.addWidget(self.f1_spin)
        self.f2_label = QLabel('F2:')
        self.f2_spin = SIDoubleSpinBox('Hz')
        self.f2_spin.setRange(0, 10_000_000)
        self.f2_spin.setValue(f2_default)
        fr.addWidget(self.f2_label)
        fr.addWidget(self.f2_spin)
        fl.addLayout(fr)
        self.order_label = QLabel('Порядок:')
        fl.addWidget(self.order_label)
        self.filter_order = QSpinBox()
        self.filter_order.setRange(1, 10)
        self.filter_order.setValue(5)
        fl.addWidget(self.filter_order)
        self.filter_combo.currentIndexChanged.connect(self._sync_mode)
        self.approx_combo.currentIndexChanged.connect(self._sync_mode)
        self._sync_mode()

    def set_frequency_limit(self, max_frequency: float) -> None:
        # Ограничиваем частоты фильтра текущим диапазоном Найквиста.
        max_frequency = max(1.0, float(max_frequency))
        self.f1_spin.setRange(0.0, max_frequency)
        self.f2_spin.setRange(0.0, max_frequency)
        self.f1_spin.setValue(min(self.f1_spin.value(), max_frequency))
        self.f2_spin.setValue(min(self.f2_spin.value(), max_frequency))

    def apply_to(self, data: np.ndarray, sample_rate: float) -> np.ndarray:
        # Применяем фильтр с выбранной аппроксимацией, при ошибке оставляем исходный сигнал.
        ftype = FILTER_KEYS[self.filter_combo.currentIndex()]
        if ftype == 'none':
            return data
        approx_idx = self.approx_combo.currentIndex()
        approx = FILTER_APPROX_KEYS[min(approx_idx, len(FILTER_APPROX_KEYS) - 1)]
        try:
            return apply_filter(
                data, sample_rate, ftype,
                self.f1_spin.value(), self.f2_spin.value(),
                self.filter_order.value(),
                approx=approx,
                rp=self.rp_spin.value(),
                rs=self.rs_spin.value(),
            )
        except ValueError as e:
            QMessageBox.warning(self, 'Фильтр', f'Параметры фильтра некорректны: {e}')
            return data

    def _sync_mode(self) -> None:
        # Переключаем видимость полей под тип фильтра и выбранную аппроксимацию.
        mode = FILTER_KEYS[self.filter_combo.currentIndex()]
        is_none = mode == 'none'
        self.approx_label.setVisible(not is_none)
        self.approx_combo.setVisible(not is_none)
        approx_idx = self.approx_combo.currentIndex()
        approx = FILTER_APPROX_KEYS[approx_idx] if 0 <= approx_idx < len(FILTER_APPROX_KEYS) else 'butter'
        is_bandpass = mode == 'bandpass'
        show_rp_rs = not is_none and approx in ('cheby1', 'cheby2', 'ellip')
        for w in self._rp_rs_widgets:
            w.setVisible(show_rp_rs)
        self.f1_label.setVisible(not is_none)
        self.f1_spin.setVisible(not is_none)
        self.f2_label.setVisible(is_bandpass)
        self.f2_spin.setVisible(is_bandpass)
        self.order_label.setVisible(not is_none)
        self.filter_order.setVisible(not is_none)