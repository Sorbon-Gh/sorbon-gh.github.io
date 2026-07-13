import math

VERSION = "1.0.0"

BG_MAIN = "#0d1117"
BG_PANEL = "#161b22"
BG_CARD = "#1c2128"
BG_INPUT = "#21262d"
BG_DARK = "#010409"
MENU_BG = "#161b22"

PRIMARY = "#0078d4"
PRIMARY_HOVER = "#1890ff"

TEXT = "#e6edf3"
TEXT_ON_DARK = "#ffffff"
TEXT_LABEL = "#c9d1d9"
TEXT_MUTED = "#8b949e"

BORDER = "#30363d"
BORDER_FOCUS = "#1890ff"
BTN_BG = "#21262d"
BTN_BORDER = "#363b42"

ACCENT = "#1890ff"
ACCENT_ORANGE = "#1890ff"

PLOT_BG = "#000814"
OSC_CURVE = "#00ff41"
CURSOR1 = "#ff9500"
CURSOR2 = "#1890ff"
MEAS_PANEL_BG = "#161b22"
MEAS_PANEL_TEXT = "#c9d1d9"

STATUS_OK = "#3fb950"
STATUS_WARN = "#d29922"

SLIDER_GROOVE = "#30363d"
SCROLL_HANDLE = "#484f58"
SPLITTER = "#21262d"
STATUS_BG = "#161b22"

FORM_MIN_WIDTH = 200
PANEL_MIN_WIDTH = 280
PANEL_MAX_WIDTH = 420
SPLITTER_SIZES = [320, 1100]
VERT_SPLITTER_SIZES = [300, 250, 250]

SAMPLE_RATES = [8000, 11025, 16000, 22050, 32000, 44100, 48000, 96000]

WAVEFORM_MAP = [
    ("Синусоида", "sinusoidal"),
    ("Треугольник", "triangular"),
    ("Прямоугольник", "rectangular"),
    ("Меандр", "meander"),
    ("Пилообразный", "sawtooth"),
    ("Шум", "noise"),
    ("Импульс", "pulse"),
    ("Постоянный (DC)", "dc"),
    ("Чирп", "chirp"),
    ("Трапеция", "trapezoidal"),
    ("Гауссов импульс", "gaussian"),
]

FILTER_KEYS = ["none", "lowpass", "highpass", "bandpass"]
FILTER_LABELS = ["Без фильтра", "Низкочастотный (НЧ)", "Высокочастотный (ВЧ)", "Полосовой (ПФ)"]

FILTER_APPROX_KEYS = ["butter", "cheby1", "cheby2", "ellip"]
FILTER_APPROX_LABELS = ["Баттерворт", "Чебышёв I", "Чебышёв II", "Эллиптический"]

SI_PAIRS = [
    (1e12, "T"), (1e9, "G"), (1e6, "M"), (1e3, "k"),
    (1.0, ""), (1e-3, "m"), (1e-6, "μ"), (1e-9, "n"), (1e-12, "p"),
]

SPECTRO_COLORS = [
    (0.0,  [0, 0, 20, 255]),
    (0.1,  [0, 10, 60, 255]),
    (0.2,  [0, 30, 100, 255]),
    (0.3,  [0, 60, 140, 255]),
    (0.4,  [0, 100, 180, 255]),
    (0.5,  [0, 140, 220, 255]),
    (0.6,  [20, 180, 240, 255]),
    (0.7,  [80, 210, 250, 255]),
    (0.8,  [140, 230, 255, 255]),
    (0.9,  [200, 245, 255, 255]),
    (1.0,  [240, 255, 255, 255]),
]


def si_format(value, unit: str = "") -> str:
    if value is None or not isinstance(value, (int, float)):
        return "—"
    if not math.isfinite(value):
        return "—"
    av = abs(value)
    if av < 1e-15:
        return f"0 {unit}".strip()
    for scale, prefix in SI_PAIRS:
        if av >= scale * 0.9995:
            sv = value / scale
            text = f"{sv:.4f}".rstrip("0")
            if text.endswith("."):
                text += "0"
            suffix = f"{prefix}{unit}"
            return f"{text} {suffix}".strip() if suffix else text
    return f"{value:.3e} {unit}".strip()
