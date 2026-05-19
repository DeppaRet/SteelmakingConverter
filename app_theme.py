"""Centralized Qt palettes and stylesheets for dark/light themes."""

from __future__ import annotations

from PyQt5.QtGui import QColor, QPalette

from theme_settings import THEME_DARK, THEME_LIGHT, get_theme, normalize_theme

# ── Color tokens ──────────────────────────────────────────────────────────────

_TOKENS = {
    THEME_DARK: {
        "accent": "#00c8f0",
        "accent2": "#00d4ff",
        "accent_dim": "#0090b8",
        "window_bg": "#12121e",
        "window_bg2": "#181828",
        "gradient_start": "#1a1a2e",
        "gradient_end": "#16213e",
        "central_grad_start": "#181828",
        "central_grad_end": "#14142a",
        "text": "#e0e0e0",
        "text_muted": "#8aaab8",
        "text_label": "#d8d8d8",
        "text_on_accent": "#12121e",
        "input_bg": "rgba(0,0,0,0.42)",
        "input_border": "rgba(0,200,240,0.28)",
        "panel_bg": "rgba(0,0,0,0.18)",
        "menubar_bg": "#0b0b18",
        "table_bg": "#0f111a",
        "table_alt": "#141828",
        "table_header": "#1a2030",
        "group_border": "rgba(0,200,240,0.30)",
        "login_panel": "rgba(0, 0, 0, 0.3)",
        "login_panel_border": "rgba(0, 212, 255, 0.2)",
        "icon_bg": "#e8e8e8",
        "chrome_bg": "#12101a",
        "chrome_text": "#8fb8d8",
        "header_grad_start": "#0a0a18",
        "header_grad_mid": "#181830",
        "header_grad_end": "#0a0a18",
        "header_border": "#00c8f0",
        "card_bg": "rgba(0,0,0,0.45)",
        "card_border": "rgba(128,128,128,0.5)",
        "scroll_bg": "#181828",
        "btn_hover_flat": "rgba(0,200,240,0.14)",
        "control_warn": "#e6a817",
        "control_danger": "#e04040",
        "control_computed": "#6a8a9a",
        "control_dial_track": "rgba(0,200,240,0.22)",
        "control_slider_groove": "rgba(0,0,0,0.35)",
    },
    THEME_LIGHT: {
        "accent": "#006494",
        "accent2": "#0078b8",
        "accent_dim": "#005078",
        "window_bg": "#eef2f7",
        "window_bg2": "#ffffff",
        "gradient_start": "#e8eef5",
        "gradient_end": "#d4e2f0",
        "central_grad_start": "#eef2f8",
        "central_grad_end": "#e2eaf4",
        "text": "#1c2836",
        "text_muted": "#4a5c6e",
        "text_label": "#243444",
        "text_on_accent": "#ffffff",
        "input_bg": "#ffffff",
        "input_border": "#a8bccf",
        "panel_bg": "#ffffff",
        "menubar_bg": "#dce6f2",
        "table_bg": "#ffffff",
        "table_alt": "#f0f4fa",
        "table_header": "#c5d4e6",
        "group_border": "#8aa8c4",
        "login_panel": "#ffffff",
        "login_panel_border": "#8aa8c4",
        "icon_bg": "#ffffff",
        "chrome_bg": "#dce8f4",
        "chrome_text": "#1c4058",
        "header_grad_start": "#d0dce8",
        "header_grad_mid": "#e8eef5",
        "header_grad_end": "#d0dce8",
        "header_border": "#0078b8",
        "card_bg": "#ffffff",
        "card_border": "#a8bccf",
        "scroll_bg": "#e8eef5",
        "btn_hover_flat": "rgba(0,120,168,0.12)",
        "control_warn": "#b8860b",
        "control_danger": "#c03030",
        "control_computed": "#6a7c8e",
        "control_dial_track": "rgba(0,100,148,0.25)",
        "control_slider_groove": "rgba(0,0,0,0.12)",
    },
}


def tokens(theme: str | None = None) -> dict:
    return _TOKENS[normalize_theme(theme)]


def palette(theme: str | None = None) -> QPalette:
    t = tokens(theme)
    p = QPalette()
    if normalize_theme(theme) == THEME_DARK:
        p.setColor(QPalette.Window, QColor(18, 18, 30))
        p.setColor(QPalette.WindowText, QColor(220, 220, 220))
        p.setColor(QPalette.Base, QColor(28, 28, 45))
        p.setColor(QPalette.AlternateBase, QColor(38, 38, 58))
        p.setColor(QPalette.Text, QColor(220, 220, 220))
        p.setColor(QPalette.Button, QColor(38, 38, 55))
        p.setColor(QPalette.ButtonText, QColor(220, 220, 220))
        p.setColor(QPalette.Highlight, QColor(0, 200, 240))
        p.setColor(QPalette.HighlightedText, QColor(18, 18, 30))
    else:
        p.setColor(QPalette.Window, QColor(232, 236, 244))
        p.setColor(QPalette.WindowText, QColor(26, 36, 48))
        p.setColor(QPalette.Base, QColor(255, 255, 255))
        p.setColor(QPalette.AlternateBase, QColor(232, 238, 246))
        p.setColor(QPalette.Text, QColor(26, 36, 48))
        p.setColor(QPalette.Button, QColor(208, 218, 232))
        p.setColor(QPalette.ButtonText, QColor(26, 36, 48))
        p.setColor(QPalette.Highlight, QColor(0, 120, 168))
        p.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    return p


def login_styles(theme: str | None = None) -> dict:
    t = tokens(theme)
    on_accent = t["text_on_accent"]
    return {
        "central": f"""
            QWidget#centralwidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {t['gradient_start']}, stop:1 {t['gradient_end']});
            }}
            QLabel {{ color: {t['text']}; }}
        """,
        "title": f"color: {t['accent2']}; background: transparent;",
        "icon": (
            f"background: {t['icon_bg']}; border-radius: 6px; "
            f"border: 2px solid {t['accent2']}; padding: 5px;"
        ),
        "form_panel": f"""
            QWidget#loginFormPanel {{
                background: {t['login_panel']};
                border-radius: 6px;
                border: 1px solid {t['login_panel_border']};
            }}
        """,
        "label": f"color: {t['text']}; background: transparent;",
        "line_edit": f"""
            QLineEdit {{
                background: {t['input_bg']};
                border: 1px solid {t['input_border']};
                border-radius: 4px;
                padding: 5px 12px;
                color: {t['text']};
                selection-background-color: {t['accent2']};
            }}
            QLineEdit:focus {{
                border: 2px solid {t['accent2']};
            }}
        """,
        "primary_btn": f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t['accent2']}, stop:1 {t['accent_dim']});
                color: {on_accent};
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t['accent']}, stop:1 {t['accent2']});
            }}
        """,
        "settings_btn": """
            QPushButton { background: transparent; border: none; }
            QPushButton:hover { background: rgba(128,128,128,0.15); border-radius: 4px; }
        """,
    }


def connection_styles(theme: str | None = None) -> dict:
    t = tokens(theme)
    on_accent = t["text_on_accent"]
    return {
        "central": f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {t['gradient_start']}, stop:1 {t['gradient_end']});
            }}
        """,
        "title": f"color: {t['accent2']}; background: transparent;",
        "form_panel": f"""
            QWidget {{
                background: {t['login_panel']};
                border-radius: 12px;
                border: 1px solid {t['login_panel_border']};
            }}
        """,
        "label": f"color: {t['text']}; background: transparent;",
        "line_edit": f"""
            QLineEdit {{
                background: {t['input_bg']};
                border: 1px solid {t['input_border']};
                border-radius: 6px;
                padding: 6px 12px;
                color: {t['text']};
            }}
            QLineEdit:focus {{ border: 2px solid {t['accent2']}; }}
        """,
        "test_btn": f"""
            QPushButton {{
                background: rgba(0, 120, 168, 0.12);
                color: {t['accent2']};
                border: 1px solid {t['accent2']};
                border-radius: 8px;
            }}
            QPushButton:hover {{ background: rgba(0, 120, 168, 0.22); }}
        """,
        "save_btn": f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t['accent2']}, stop:1 {t['accent_dim']});
                color: {on_accent};
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }}
        """,
        "combo": f"""
            QComboBox {{
                background: {t['input_bg']};
                border: 1px solid {t['input_border']};
                border-radius: 6px;
                padding: 4px 8px;
                color: {t['text']};
            }}
        """,
    }


def about_style(theme: str | None = None) -> str:
    t = tokens(theme)
    return f"""
        QDialog {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {t['gradient_start']}, stop:1 {t['gradient_end']});
        }}
        QLabel {{ color: {t['text']}; }}
    """


def operator_main_style(theme: str | None = None) -> str:
    t = tokens(theme)
    return f"""
        QMainWindow {{ background: {t['window_bg']}; }}
        QMenuBar {{
            background: {t['menubar_bg']}; color: {t['text']};
            border-bottom: 1px solid {t['group_border']}; padding: 2px 4px; font-size: 11px;
        }}
        QMenuBar::item {{ background: transparent; padding: 5px 12px; border-radius: 4px; }}
        QMenuBar::item:selected {{ background: rgba(0,120,168,0.25); color: {t['accent']}; }}
        QMenu {{
            background: {t['menubar_bg']}; color: {t['text']};
            border: 1px solid {t['group_border']}; border-radius: 6px; padding: 4px;
        }}
        QMenu::item {{ padding: 6px 22px 6px 14px; border-radius: 4px; }}
        QMenu::item:selected {{ background: rgba(0,120,168,0.28); color: {t['accent']}; }}
        QMenu::separator {{ height: 1px; background: {t['group_border']}; margin: 4px 8px; }}
        QStatusBar {{
            background: {t['menubar_bg']}; color: {t['text_muted']};
            border-top: 1px solid {t['group_border']}; font-size: 10px;
        }}
    """


def pushbutton_rules(t: dict | None = None) -> str:
    if t is None:
        t = tokens()
    on_accent = t["text_on_accent"]
    return f"""
        QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {t['accent']}, stop:1 {t['accent_dim']});
            color: {on_accent}; border: none; border-radius: 6px;
            padding: 4px 12px; font-weight: bold; font-size: 11px;
            min-height: 22px; max-height: 28px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {t['accent2']}, stop:1 {t['accent']});
        }}
        QPushButton:flat {{
            background: transparent; border: none;
            padding: 0px; margin: 0px;
            min-height: 0px; max-height: 32px; min-width: 0px;
        }}
        QPushButton:flat:hover {{
            background: {t['btn_hover_flat']};
            border-radius: 4px;
        }}
    """


def operator_central_style(theme: str | None = None) -> str:
    t = tokens(theme)
    btn = pushbutton_rules(t)
    return f"""
        QWidget#centralwidget {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {t['central_grad_start']}, stop:1 {t['central_grad_end']});
        }}
        QLabel  {{ color: {t['text_label']}; background: transparent; font-size: 11px; }}
        QGroupBox {{
            color: {t['accent']}; font-weight: bold; font-size: 11px;
            border: 1px solid {t['group_border']};
            border-radius: 7px; margin-top: 11px; padding: 4px;
            background: {t['panel_bg']};
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 9px; padding: 0 4px; }}
        QLineEdit {{
            background: {t['input_bg']}; border: 1px solid {t['input_border']};
            border-radius: 4px; padding: 3px 6px; color: {t['text']}; font-size: 11px;
        }}
        QLineEdit:focus {{ border: 2px solid {t['accent']}; }}
        QLineEdit[readOnly="true"] {{
            background: rgba(0,120,168,0.09); border: 1px solid {t['input_border']};
            color: {t['text']};
        }}
        QComboBox {{
            background: {t['input_bg']}; border: 1px solid {t['input_border']};
            border-radius: 5px; padding: 4px 6px; color: {t['text']}; font-size: 11px;
        }}
        QComboBox:hover {{ border: 1px solid {t['accent']}; }}
        QComboBox QAbstractItemView {{
            background: {t['window_bg2']}; color: {t['text']};
            selection-background-color: rgba(0,120,168,0.35);
        }}
        {btn}
        QPushButton#GetResExample {{
            min-height: 28px; max-height: 28px;
            padding: 4px 10px; font-size: 11px;
        }}
        QTabWidget::pane {{
            border: 1px solid {t['group_border']};
            border-radius: 7px; background: {t['panel_bg']};
        }}
        QTabBar::tab {{
            background: {t['panel_bg']}; color: {t['text_muted']};
            padding: 6px 16px; border-radius: 5px 5px 0 0; margin-right: 2px; font-size: 11px;
        }}
        QTabBar::tab:selected {{ background: rgba(0,120,168,0.28); color: {t['text']}; }}
        QProgressBar {{
            border: 1px solid {t['input_border']}; border-radius: 4px;
            background: {t['panel_bg']}; color: {t['text']}; text-align: center; font-size: 9px;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {t['accent']}, stop:1 {t['accent_dim']}); border-radius: 4px;
        }}
        QPlainTextEdit, QTextEdit {{
            background: {t['table_bg']}; border: 1px solid {t['group_border']};
            border-radius: 5px; color: {t['text']}; padding: 4px; font-size: 10pt;
        }}
        QScrollBar:vertical {{
            background: {t['panel_bg']}; width: 8px; border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(0,120,168,0.45); border-radius: 3px; min-height: 18px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{
            background: {t['panel_bg']}; height: 8px; border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: rgba(0,120,168,0.45); border-radius: 3px; min-width: 18px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        QTableWidget {{
            background: {t['table_bg']};
            alternate-background-color: {t['table_alt']};
            gridline-color: {t['input_border']};
            color: {t['text']}; border: 1px solid {t['group_border']}; border-radius: 6px;
            font-size: 11px;
        }}
        QTableWidget::item {{ padding: 2px 4px; color: {t['text']}; }}
        QTableWidget::item:selected {{
            background: rgba(0,120,168,0.28); color: {t['text']};
        }}
        QHeaderView {{ background: {t['table_header']}; }}
        QHeaderView::section {{
            background: {t['table_header']}; color: {t['text']};
            padding: 3px 4px; border: none; font-weight: bold; font-size: 10px;
        }}
        QSplitter::handle {{ background: {t['input_border']}; }}
        QScrollArea {{ border: none; background: {t['window_bg2']}; }}
        QScrollArea > QWidget {{ background: transparent; }}
    """


def field_style(theme: str | None = None) -> str:
    """Editable or neutral result field."""
    t = tokens(theme)
    return read_only_field_style(theme)


def line_edit_style(theme: str | None = None) -> str:
    t = tokens(theme)
    return f"""
        QLineEdit {{
            background: {t['input_bg']};
            border: 1px solid {t['input_border']};
            border-radius: 4px;
            padding: 3px 6px;
            color: {t['text']};
            font-size: 11px;
        }}
        QLineEdit:focus {{ border: 2px solid {t['accent']}; }}
    """


def label_style(theme: str | None = None) -> str:
    t = tokens(theme)
    return (
        f"color: {t['text_label']}; background: transparent; font-size: 11px;"
    )


def read_only_field_style(theme: str | None = None) -> str:
    """Read-only QLineEdit — opaque theme background (no white bleed-through)."""
    t = tokens(theme)
    if normalize_theme(theme) == THEME_DARK:
        bg = "rgba(0, 120, 168, 0.14)"
    else:
        bg = "rgba(0, 120, 168, 0.08)"
    return (
        f"QLineEdit {{ background: {bg}; color: {t['text']}; "
        f"border: 1px solid {t['input_border']}; border-radius: 4px; "
        f"padding: 3px 6px; }}"
    )


def table_style(theme: str | None = None) -> str:
    t = tokens(theme)
    return f"""
        QTableWidget {{
            background: {t['table_bg']};
            alternate-background-color: {t['table_alt']};
            color: {t['text']};
            gridline-color: {t['input_border']};
            border: 1px solid {t['group_border']};
            border-radius: 4px;
        }}
        QTableWidget::item {{
            padding: 2px 4px;
            color: {t['text']};
            background: {t['table_bg']};
        }}
        QTableWidget::item:alternate {{
            background: {t['table_alt']};
        }}
        QTableWidget::item:selected {{
            background: rgba(0, 120, 168, 0.28);
            color: {t['text']};
        }}
        QTableCornerButton::section {{
            background: {t['table_header']};
            border: 1px solid {t['input_border']};
        }}
        QHeaderView {{
            background: {t['table_header']};
        }}
        QHeaderView::section {{
            background: {t['table_header']};
            color: {t['accent']};
            padding: 4px;
            border: 1px solid {t['input_border']};
            font-weight: bold;
        }}
    """


def admin_style(theme: str | None = None) -> str:
    """Combined admin window + central widget styles."""
    t = tokens(theme)
    main = operator_main_style(theme)
    central = operator_central_style(theme)
    return main + central.replace("QWidget#centralwidget", "QWidget#centralwidget, QWidget")


def developer_style(theme: str | None = None) -> str:
    return operator_central_style(theme)


def control_inputs_panel_qss(theme: str | None = None) -> str:
    """QSS for operator control knobs (dials, sliders, range hints)."""
    t = tokens(theme)
    return f"""
        QWidget#control_inputs_panel {{
            background: transparent;
        }}
        QGroupBox#control_inputs_group {{
            color: {t['accent']};
            font-weight: bold;
            font-size: 10px;
            border: 1px solid {t['group_border']};
            border-radius: 6px;
            margin-top: 10px;
            padding: 4px 6px 6px 6px;
            background: {t['panel_bg']};
        }}
        QGroupBox#control_inputs_group > QWidget {{
            background: transparent;
        }}
        QGroupBox#control_inputs_group::title {{
            subcontrol-origin: margin; left: 8px; padding: 0 3px;
        }}
        QLabel.control_knob_title {{
            color: {t['text_label']}; font-size: 9px; font-weight: bold;
            background: transparent;
            min-width: 0px;
        }}
        QLabel.control_knob_value {{
            color: {t['accent']}; font-size: 9px; background: transparent;
        }}
        QFrame.control_knob_frame {{
            min-width: 0px;
            border: 1px solid {t['input_border']};
            border-radius: 5px;
            background: {t['input_bg']};
            padding: 2px;
        }}
        QDoubleSpinBox.control_spin {{
            background: {t['input_bg']};
            border: 1px solid {t['input_border']};
            border-radius: 3px;
            color: {t['text']};
            font-size: 10px;
            padding: 1px 3px;
            min-height: 18px;
            max-height: 22px;
        }}
        QDoubleSpinBox.control_spin_computed {{
            background: {t['input_bg']};
            border: 1px dashed {t['input_border']};
            border-radius: 3px;
            color: {t['control_computed']};
            font-size: 10px;
            font-style: italic;
            padding: 1px 3px;
            min-height: 18px;
            max-height: 22px;
        }}
        QSlider::groove:horizontal {{
            border: 1px solid {t['input_border']};
            height: 5px;
            background: {t['control_slider_groove']};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {t['accent']};
            border: 1px solid {t['accent_dim']};
            width: 12px;
            margin: -5px 0;
            border-radius: 6px;
        }}
        QDial {{
            background: {t['control_dial_track']};
            color: {t['accent']};
        }}
        QCheckBox.control_lock {{
            color: {t['text_muted']}; font-size: 8px; spacing: 2px;
        }}
        QPushButton.control_tool_btn {{
            background: transparent;
            border: 1px solid {t['group_border']};
            border-radius: 4px;
            color: {t['text_muted']};
            font-size: 9px;
            padding: 2px 6px;
            min-height: 18px;
            max-height: 22px;
        }}
        QPushButton.control_tool_btn:hover {{
            border-color: {t['accent']};
            color: {t['accent']};
        }}
    """


def converter_chrome_qss(theme: str | None = None) -> str:
    t = tokens(theme)
    return (
        f"background:{t['chrome_bg']}; color:{t['chrome_text']}; "
        "font:bold 10px 'Arial'; padding:3px 6px;"
    )


def accent_color(theme: str | None = None) -> str:
    return tokens(theme)["accent"]


def html_accent(theme: str | None = None) -> str:
    return tokens(theme)["accent2"]


def header_bar_style(theme: str | None = None) -> str:
    t = tokens(theme)
    return f"""
        QFrame#header_frame {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {t['header_grad_start']}, stop:0.5 {t['header_grad_mid']},
                stop:1 {t['header_grad_end']});
            border-bottom: 2px solid {t['header_border']};
        }}
        QLabel {{ font-family: 'Segoe UI', sans-serif; }}
    """


def header_title_style(theme: str | None = None) -> str:
    t = tokens(theme)
    return f"color: {t['accent2']}; font-size: 13px; font-weight: bold; background: transparent;"


def indicator_card_style(theme: str | None = None, border_rgb: str = "0,120,168") -> str:
    t = tokens(theme)
    if normalize_theme(theme) == THEME_DARK:
        bg = t["card_bg"]
    else:
        bg = t["panel_bg"]
    return (
        f"QFrame {{ background: {bg}; "
        f"border: 1px solid rgba({border_rgb},0.55); border-radius: 5px; }}"
    )


def help_rich_html(theme: str | None = None) -> str:
    ac = html_accent(theme)
    t = tokens(theme)
    body = t["text_label"]
    return (
        f"<span style='color:{ac};'><b>Порядок расчётов:</b></span>"
        f"<span style='color:{body};'>"
        "<br>1. <b>Металлошихта</b> — вычисление масс шихты<br>"
        "2. <b>Табл. окисления</b> — расход O₂ по элементам<br>"
        "3. <b>Расчёт шлака</b> — флюсы, состав шлака<br>"
        "4. <b>Расчёт дутья</b> — кислород, интенсивность<br>"
        "5. <b>Мат. баланс</b> — приход/расход материалов<br>"
        "6. <b>Тепл. баланс</b> — температура выхода стали<br>"
        "7. <b>Раскисление</b> — ферросплавы, выход металла<br>"
        "8. <b>Рекомендации</b> — режим продувки, MgO"
        "</span>"
    )


def hints_rich_html(theme: str | None = None) -> str:
    ac = html_accent(theme)
    body = tokens(theme)["text_label"]
    return (
        f"<b style='color:{ac};'>Ограничения:</b> "
        f"<span style='color:{body};'>Мин. T стали, содержание C и P — см. левую панель.<br>"
        f"</span><b style='color:{ac};'>LED:</b> "
        f"<span style='color:#00a850;'>●</span> "
        f"<span style='color:{body};'>рассчитан &nbsp; </span>"
        f"<span style='color:#8a94a8;'>●</span> "
        f"<span style='color:{body};'>ещё не выполнен</span>"
    )


def recommendation_style(theme: str | None = None) -> str:
    t = tokens(theme)
    if normalize_theme(theme) == THEME_DARK:
        return (
            "QPlainTextEdit { background: rgba(0,40,10,0.45); "
            "border: 1px solid rgba(0,255,100,0.30); color: #a0e8a0; font-size: 11px; }"
        )
    return (
        f"QPlainTextEdit {{ background: #eef8f0; "
        f"border: 1px solid #88c898; color: #1a5030; font-size: 11px; }}"
    )


def admin_central_style(theme: str | None = None) -> str:
    """Full admin content area — same coverage as operator central."""
    t = tokens(theme)
    base = operator_central_style(theme)
    btn = pushbutton_rules(t)
    extra = f"""
        {btn}
        QWidget {{
            background: transparent;
            color: {t['text']};
        }}
        QScrollArea {{
            border: none;
            background: {t['scroll_bg']};
        }}
        QScrollArea > QWidget > QWidget {{
            background: {t['window_bg']};
        }}
        QTableWidget, QTableView {{
            background: {t['table_bg']};
            alternate-background-color: {t['table_alt']};
            color: {t['text']};
            gridline-color: {t['input_border']};
            border: 1px solid {t['group_border']};
        }}
        QHeaderView::section {{
            background: {t['table_header']};
            color: {t['text']};
            font-weight: bold;
        }}
        QComboBox QAbstractItemView {{
            background: {t['window_bg2']};
            color: {t['text']};
            selection-background-color: {t['accent2']};
            selection-color: {t['text_on_accent']};
        }}
    """
    return base + extra


def primary_button_style(theme: str | None = None) -> str:
    """Single prominent action button (e.g. «Запустить все этапы»)."""
    t = tokens(theme)
    on = t["text_on_accent"]
    return f"""
        QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {t['accent']}, stop:1 {t['accent_dim']});
            color: {on}; border: none; border-radius: 6px;
            padding: 4px 10px; font-weight: bold; font-size: 11px;
            min-height: 28px; max-height: 28px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {t['accent2']}, stop:1 {t['accent']});
        }}
    """


def center_panel_style(theme: str | None = None) -> str:
    """Center column: background + buttons (own stylesheet overrides parent QSS)."""
    t = tokens(theme)
    return (
        panel_background_style(theme)
        + pushbutton_rules(t)
        + f"""
        QLabel {{ color: {t['text_label']}; background: transparent; }}
        QProgressBar {{
            border: 1px solid {t['input_border']}; border-radius: 4px;
            background: {t['panel_bg']}; color: {t['text']};
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {t['accent']}, stop:1 {t['accent_dim']});
        }}
    """
    )


def message_box_stylesheet(theme: str | None = None) -> str:
    """Global QMessageBox styling (set on QApplication)."""
    t = tokens(theme)
    return f"""
        QMessageBox {{
            background-color: {t['window_bg2']};
        }}
        QMessageBox QLabel {{
            color: {t['text']};
            background-color: transparent;
        }}
        QMessageBox QPushButton {{
            background-color: {t['accent']};
            color: {t['text_on_accent']};
            border: 1px solid {t['accent_dim']};
            border-radius: 4px;
            padding: 6px 14px;
            min-width: 72px;
            font-weight: bold;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {t['accent2']};
        }}
        QMessageBox QPushButton:default {{
            background-color: {t['accent2']};
            color: {t['text_on_accent']};
        }}
    """


def style_message_box(msg, theme: str | None = None) -> None:
    """Ensure a QMessageBox matches the active theme (palette + QSS)."""
    if theme is None:
        theme = get_theme()
    msg.setPalette(palette(theme))
    msg.setStyleSheet(message_box_stylesheet(theme))


def apply_to_application(app, theme: str | None = None) -> None:
    """Apply QMessageBox styles globally (do not set app palette — breaks forms)."""
    if theme is None:
        theme = get_theme()
    app.setStyleSheet(message_box_stylesheet(theme))


def panel_background_style(theme: str | None = None) -> str:
    t = tokens(theme)
    return f"background-color: {t['window_bg2']};"


def apply_scroll_panel(
    scroll_area,
    inner_widget,
    theme: str | None = None,
) -> None:
    """Force QScrollArea viewport and content to follow the active theme."""
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QScrollArea

    if not isinstance(scroll_area, QScrollArea):
        return
    t = tokens(theme)
    pal = palette(theme)
    bg = t["window_bg2"]
    scroll_area.setAttribute(Qt.WA_StyledBackground, True)
    scroll_area.setPalette(pal)
    scroll_area.setStyleSheet(
        f"QScrollArea {{ background: {bg}; border: none; }}"
    )
    vp = scroll_area.viewport()
    vp.setAttribute(Qt.WA_StyledBackground, True)
    vp.setAutoFillBackground(True)
    vp.setPalette(pal)
    vp.setStyleSheet(f"background-color: {bg};")
    if inner_widget is not None:
        inner_widget.setAttribute(Qt.WA_StyledBackground, True)
        inner_widget.setAutoFillBackground(True)
        inner_widget.setPalette(pal)
        inner_widget.setStyleSheet(panel_background_style(theme))


def apply_admin_content_styles(root, theme: str | None = None) -> None:
    """Explicit styles for admin form children (QTabWidget needs this on first show)."""
    from PyQt5.QtWidgets import (
        QComboBox,
        QGroupBox,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QPushButton,
        QTableWidget,
        QTextEdit,
    )

    if theme is None:
        theme = get_theme()
    pal = palette(theme)
    le_edit = line_edit_style(theme)
    le_ro = read_only_field_style(theme)
    lbl_s = label_style(theme)
    btn_s = pushbutton_rules(tokens(theme))
    pe_style = (
        f"QPlainTextEdit, QTextEdit {{ background: {tokens(theme)['table_bg']}; "
        f"border: 1px solid {tokens(theme)['group_border']}; "
        f"color: {tokens(theme)['text']}; padding: 4px; }}"
    )
    for w in root.findChildren(QLineEdit):
        w.setPalette(pal)
        w.setStyleSheet(le_ro if w.isReadOnly() else le_edit)
    for w in root.findChildren(QLabel):
        w.setPalette(pal)
        w.setStyleSheet(lbl_s)
    for w in root.findChildren(QComboBox):
        w.setPalette(pal)
    for w in root.findChildren(QGroupBox):
        w.setPalette(pal)
    for w in root.findChildren(QTableWidget):
        w.setPalette(pal)
        w.setStyleSheet(table_style(theme))
    t = tokens(theme)
    icon_btn = (
        "QPushButton { background: transparent; border: none; min-height: 0; "
        "max-height: 32px; padding: 2px; }"
        f"QPushButton:hover {{ background: {t['btn_hover_flat']}; border-radius: 4px; }}"
    )
    for w in root.findChildren(QPushButton):
        if w.isFlat():
            continue
        w.setPalette(pal)
        if w.icon() and not (w.text() or "").strip():
            w.setStyleSheet(icon_btn)
        else:
            w.setStyleSheet(btn_s)
    for w in root.findChildren(QPlainTextEdit):
        w.setPalette(pal)
        w.setStyleSheet(pe_style)
    for w in root.findChildren(QTextEdit):
        w.setPalette(pal)
        w.setStyleSheet(pe_style)


def apply_to_widget(widget, theme: str | None = None) -> None:
    widget.setPalette(palette(theme))
