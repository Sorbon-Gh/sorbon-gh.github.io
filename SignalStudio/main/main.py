import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QFile, QIODevice, QTextStream
from PyQt6.QtGui import QIcon

import core.config as config
from gui.main_window import MainWindow

"""Точка входа приложения: загружаем стиль, иконку и запускаем главное окно."""


def _get_base_path() -> Path:
    # При запуске из PyInstaller ресурсы лежат во временной папке _MEIPASS.
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def load_styles() -> str:
    # Подставляем цветовые константы из config прямо в QSS-шаблон.
    try:
        base = _get_base_path()
        qss_path = base / 'gui' / 'styles.qss'
        if qss_path.exists():
            f = QFile(str(qss_path))
            if f.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
                content = QTextStream(f).readAll()
                f.close()
                for name in dir(config):
                    if name.isupper() and not name.startswith('_'):
                        val = getattr(config, name)
                        if isinstance(val, str) and val.startswith('#'):
                            content = content.replace(f'{{{{{name}}}}}', val)
                return content
    except OSError:
        pass
    return ''


def load_icon() -> QIcon:
    # Поддерживаем оба имени иконки, чтобы не ломаться при переименовании файла.
    base = _get_base_path()
    for name in ('logo.ico', 'icon.ico'):
        p = base / 'assets' / name
        if p.exists():
            return QIcon(str(p))
    return QIcon()


def main():
    # Инициализация Qt-приложения и запуск главного окна.
    app = QApplication(sys.argv)
    app.setApplicationName('Signal Studio')
    app.setOrganizationName('SignalStudio')
    app.setStyleSheet(load_styles())
    icon = load_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    win = MainWindow()
    if not icon.isNull():
        win.setWindowIcon(icon)
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
