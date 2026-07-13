from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from core.config import VERSION, ACCENT_ORANGE, TEXT, TEXT_LABEL, TEXT_MUTED, BG_CARD, BORDER

"""Диалог с краткой информацией о проекте и авторах."""


_STYLE = f"""
QDialog {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #141a24, stop:1 #0d1117);
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QLabel {{
    color: {TEXT};
}}
QLabel#aboutTitle {{
    color: {ACCENT_ORANGE};
    font-size: 20pt;
    font-weight: bold;
}}
QLabel#aboutDesc {{
    color: {TEXT_LABEL};
    font-size: 10pt;
}}
QLabel#aboutSection {{
    color: {TEXT_MUTED};
    font-size: 9pt;
}}
QFrame#aboutCard {{
    background-color: {BG_CARD};
    border-radius: 8px;
    border: 1px solid {BORDER};
}}
"""


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        # Небольшой статичный диалог без бизнес-логики, только аккуратная подача информации.
        super().__init__(parent)
        self.setWindowTitle('О программе')
        self.setMinimumSize(460, 400)
        self.setStyleSheet(_STYLE)
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(28, 28, 28, 28)

        title = QLabel(f'Signal Studio  v{VERSION}')
        title.setObjectName('aboutTitle')
        title.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel('Учебно-практический комплекс для генерации, фильтрации\nи спектрального анализа аудиосигналов')
        desc.setObjectName('aboutDesc')
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(12)

        dev = QLabel('Разработчик:  Ганизода Сорбон')
        dev.setObjectName('aboutDesc')
        dev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(dev)

        contact = QLabel('Для связи: ghanizodasorbon@gmail.com')
        contact.setObjectName('aboutDesc')
        contact.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(contact)

        tech = QLabel('Python · PyQt6 · NumPy · SciPy · sounddevice · PyQtGraph')
        tech.setObjectName('aboutSection')
        tech.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tech)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton(' Закрыть')
        close_btn.setObjectName('primaryButton')
        close_btn.setMinimumWidth(140)
        close_btn.setMinimumHeight(38)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
