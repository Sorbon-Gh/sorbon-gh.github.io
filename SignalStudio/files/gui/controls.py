from typing import Callable

from PyQt6.QtCore import QLocale
from PyQt6.QtGui import QValidator
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QSlider,
    QSpinBox,
    QWidget,
)

from core.config import SI_PAIRS

"""Общие контролы и привязки для числового ввода в GUI."""

_PREFIX_SCALE: dict[str, float] = {}
for _s, _p in SI_PAIRS:
    if _p:
        _PREFIX_SCALE[_p] = _s
_PREFIX_SCALE['u'] = 1e-6


class SIDoubleSpinBox(QDoubleSpinBox):

    def __init__(self, unit: str = '', parent=None):
        # Спинбокс с красивым отображением SI-префиксов (k, m, u и т.д.).
        super().__init__(parent)
        self._unit = unit
        self.setDecimals(10)

    def textFromValue(self, value: float) -> str:
        # Подбираем удобный SI-масштаб, чтобы значение читалось без длинных хвостов.
        av = abs(value)
        if av < 1e-15:
            return f'0 {self._unit}'.strip() if self._unit else '0'
        for scale, prefix in SI_PAIRS:
            if av >= scale * 0.9995:
                sv = value / scale
                text = f'{sv:.4f}'.rstrip('0')
                if text.endswith('.'):
                    text += '0'
                suffix = f'{prefix}{self._unit}'
                return f'{text} {suffix}'.strip() if suffix else text
        return f'{value:.3e} {self._unit}'.strip()

    def _try_parse(self, text: str) -> float | None:
        # Парсим как обычный float, так и формы вида "2.2kHz", "10 mV".
        t = text.strip()
        if self._unit and t.endswith(self._unit):
            t = t[:-len(self._unit)].strip()
        for prefix in sorted(_PREFIX_SCALE, key=len, reverse=True):
            if t.endswith(prefix):
                num = t[:-len(prefix)].strip()
                try:
                    return float(num) * _PREFIX_SCALE[prefix]
                except ValueError:
                    continue
        try:
            return float(t)
        except ValueError:
            return None

    def valueFromText(self, text: str) -> float:
        v = self._try_parse(text)
        return v if v is not None else self.value()

    def validate(self, text: str, pos: int):
        if not text.strip():
            return QValidator.State.Intermediate, text, pos
        v = self._try_parse(text)
        if v is not None:
            if self.minimum() <= v <= self.maximum():
                return QValidator.State.Acceptable, text, pos
            return QValidator.State.Invalid, text, pos
        return QValidator.State.Intermediate, text, pos

    def fixup(self, text: str) -> str:
        try:
            v = self.valueFromText(text)
            v = max(self.minimum(), min(self.maximum(), v))
            return self.textFromValue(v)
        except Exception:
            return self.textFromValue(self.value())


def bind_slider_spin(
    slider: QSlider,
    spin: QSpinBox | QDoubleSpinBox,
    to_spin: Callable[[int], float],
    to_slider: Callable[[float], int],
) -> None:
    # Двусторонняя синхронизация с блокировкой сигналов от зацикливания.
    def on_slider(v: int):
        spin.blockSignals(True)
        value = to_spin(v)
        if isinstance(spin, QSpinBox):
            spin.setValue(int(round(value)))
        else:
            spin.setValue(float(value))
        spin.blockSignals(False)

    def on_spin(v: float | int):
        slider.blockSignals(True)
        slider.setValue(int(to_slider(v)))
        slider.blockSignals(False)

    slider.valueChanged.connect(on_slider)
    spin.valueChanged.connect(on_spin)


def apply_numeric_locale(widget: QWidget) -> None:
    # Принудительно фиксируем C-локаль, чтобы разделитель был точкой во всех полях.
    locale = QLocale(QLocale.Language.C)
    for w in widget.findChildren(QSpinBox):
        w.setLocale(locale)
        w.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        w.setMinimumWidth(90)
    for w in widget.findChildren(QDoubleSpinBox):
        w.setLocale(locale)
        w.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        w.setMinimumWidth(90)
