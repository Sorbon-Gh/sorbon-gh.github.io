from PyQt6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
                             QStatusBar, QMessageBox)
from PyQt6.QtGui import QAction

from gui.generator_window import GeneratorWindow
from gui.analyzer_window import AnalyzerWindow
from gui.realtime_window import RealtimeWindow
from gui.about_dialog import AboutDialog
from gui.tutorial_dialog import TutorialDialog
from gui.icons import create_icon

"""Главное окно приложения: меню, переключение режимов и общие действия."""


MODE_NAMES = ['Генератор сигналов', 'Анализатор WAV', 'Реальное время']


class MainWindow(QMainWindow):

    def __init__(self):
        # Поднимаем все режимы один раз и дальше просто переключаем вкладки.
        super().__init__()
        self.setWindowTitle('Signal Studio')
        self.setMinimumSize(1440, 860)
        self.resize(1680, 980)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stacked = QStackedWidget()
        self.generator = GeneratorWindow()
        self.analyzer = AnalyzerWindow()
        self.realtime = RealtimeWindow()

        self.stacked.addWidget(self.generator)
        self.stacked.addWidget(self.analyzer)
        self.stacked.addWidget(self.realtime)
        self.stacked.currentChanged.connect(self._on_mode_changed)
        layout.addWidget(self.stacked)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._update_status(0)

        self._create_menu()

    def _create_menu(self):
        # Горячие клавиши собраны здесь, чтобы поведение было единым для всех режимов.
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Файл')
        open_act = QAction(create_icon('open', 18), ' Открыть WAV...', self)
        open_act.setShortcut('Ctrl+O')
        open_act.triggered.connect(self._on_open_wav)
        file_menu.addAction(open_act)
        save_act = QAction(create_icon('save', 18), ' Сохранить WAV...', self)
        save_act.setShortcut('Ctrl+S')
        save_act.triggered.connect(self._on_save_wav)
        file_menu.addAction(save_act)
        file_menu.addSeparator()
        exit_act = QAction(' Выход', self)
        exit_act.setShortcut('Ctrl+Q')
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        modes_menu = menubar.addMenu('Режимы')
        gen_act = QAction(create_icon('generator', 18), ' Генератор сигналов', self)
        gen_act.setShortcut('Ctrl+1')
        gen_act.triggered.connect(lambda: self._switch(0))
        anal_act = QAction(create_icon('analyzer', 18), ' Анализатор WAV', self)
        anal_act.setShortcut('Ctrl+2')
        anal_act.triggered.connect(lambda: self._switch(1))
        rt_act = QAction(create_icon('microphone', 18), ' Реальное время', self)
        rt_act.setShortcut('Ctrl+3')
        rt_act.triggered.connect(lambda: self._switch(2))
        for a in (gen_act, anal_act, rt_act):
            modes_menu.addAction(a)

        help_menu = menubar.addMenu('Помощь')
        tutorial_act = QAction(create_icon('tutorial', 18), ' Справочное руководство', self)
        tutorial_act.setShortcut('Ctrl+4')
        tutorial_act.triggered.connect(self._show_tutorial)
        help_menu.addAction(tutorial_act)
        about_act = QAction(create_icon('about', 18), ' О программе', self)
        about_act.setShortcut('F1')
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

    def _switch(self, index: int):
        self.stacked.setCurrentIndex(index)

    def _on_mode_changed(self, index: int):
        self._update_status(index)

    def _update_status(self, index: int):
        self._status.showMessage(f'Режим: {MODE_NAMES[index]}')

    def _on_open_wav(self):
        # Открытие WAV имеет смысл в анализаторе, поэтому принудительно туда переключаемся.
        if self.stacked.currentIndex() != 1:
            self._switch(1)
        self.analyzer.load_wav()

    def _on_save_wav(self):
        # Сохранение из realtime не поддерживаем: там поток живой, без зафиксированного буфера.
        idx = self.stacked.currentIndex()
        if idx == 0:
            self.generator.save_wav()
        elif idx == 1:
            self.analyzer.save_wav()
        else:
            QMessageBox.information(self, 'Сохранение',
                'Сохранить WAV доступно в режимах Генератор и Анализатор.')

    def _show_tutorial(self):
        TutorialDialog(self).exec()

    def _show_about(self):
        AboutDialog(self).exec()

    def closeEvent(self, event):
        # Не даем закрыть окно "молча", если сейчас идет захват с микрофона.
        if self.realtime.is_recording():
            r = QMessageBox.question(self, 'Выход',
                'Идёт захват с микрофона. Остановить и выйти?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if r == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self.realtime.stop_recording()
        event.accept()
