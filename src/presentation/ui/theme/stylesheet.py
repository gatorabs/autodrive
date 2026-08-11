"""Builds the single QSS stylesheet applied once to the whole QApplication."""

from __future__ import annotations

from src.presentation.ui.theme.tokens import Color, Radius, Space, Type


def _accent_rule(selector: str, color: str) -> str:
    return f"{selector} {{ border: 1px solid {color}; }}"


def build_qss() -> str:
    return f"""
    * {{
        font-family: "{Type.FAMILY}";
        font-size: {Type.BODY}px;
        color: {Color.TEXT};
        outline: none;
    }}

    QMainWindow, QDialog, QWidget#Root {{
        background-color: {Color.BG};
    }}

    QToolTip {{
        background-color: {Color.PANEL_SOFT};
        color: {Color.TEXT};
        border: 1px solid {Color.BORDER_STRONG};
        border-radius: {Radius.SM}px;
        padding: 4px 8px;
    }}

    QScrollArea {{
        background: transparent;
        border: none;
    }}
    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}

    QFrame#Card {{
        background-color: {Color.PANEL};
        border: 1px solid {Color.BORDER};
        border-radius: {Radius.LG}px;
    }}
    {_accent_rule('QFrame#Card[accent="primary"]', Color.PRIMARY)}
    {_accent_rule('QFrame#Card[accent="secondary"]', Color.SECONDARY)}
    {_accent_rule('QFrame#Card[accent="success"]', Color.SUCCESS)}
    QFrame#Card[bordered="false"] {{ border: none; }}

    QLabel#CardTitle {{
        font-size: {Type.HEADING}px;
        font-weight: 600;
        color: {Color.TEXT};
    }}
    QLabel#SectionLabel {{
        font-size: {Type.CAPTION}px;
        font-weight: 600;
        letter-spacing: 1px;
        color: {Color.SUBTLE};
    }}
    QFrame#SectionRule {{
        background-color: {Color.BORDER};
        max-height: 1px;
        min-height: 1px;
        border: none;
    }}

    QFrame#StateBlock {{
        background-color: {Color.PANEL_ALT};
        border: 1px solid {Color.BORDER};
        border-radius: {Radius.SM}px;
    }}

    QFrame#StatusBadge {{
        border-radius: {Radius.PILL}px;
        border: none;
    }}
    QFrame#StatusBadge[tone="primary"] {{ background-color: {Color.PRIMARY_SOFT}; }}
    QFrame#StatusBadge[tone="secondary"] {{ background-color: {Color.SECONDARY_SOFT}; }}
    QFrame#StatusBadge[tone="success"] {{ background-color: {Color.SUCCESS_SOFT}; }}
    QFrame#StatusBadge[tone="warning"] {{ background-color: {Color.WARNING_SOFT}; }}
    QFrame#StatusBadge[tone="danger"] {{ background-color: {Color.DANGER_SOFT}; }}
    QFrame#StatusBadge[tone="muted"] {{ background-color: {Color.PANEL_SOFT}; }}

    QPushButton {{
        background-color: {Color.PANEL_SOFT};
        color: {Color.TEXT};
        border: 1px solid {Color.BORDER};
        border-radius: {Radius.SM}px;
        padding: 6px 14px;
        min-height: 22px;
    }}
    QPushButton:hover {{
        background-color: {Color.BORDER_STRONG};
    }}
    QPushButton:pressed {{
        background-color: {Color.PANEL_ALT};
    }}
    QPushButton:disabled {{
        color: {Color.SUBTLE};
        background-color: {Color.PANEL_ALT};
    }}
    QPushButton[variant="primary"] {{
        background-color: {Color.PRIMARY};
        border: 1px solid {Color.PRIMARY};
        color: {Color.BG};
        font-weight: 600;
    }}
    QPushButton[variant="primary"]:hover {{
        background-color: {Color.PRIMARY_HOVER};
        border-color: {Color.PRIMARY_HOVER};
    }}
    QPushButton[variant="danger"] {{
        background-color: {Color.DANGER_SOFT};
        border: 1px solid {Color.DANGER};
        color: {Color.DANGER};
    }}
    QPushButton[variant="danger"]:hover {{
        background-color: {Color.DANGER};
        color: {Color.BG};
    }}
    QPushButton#IconButton, QToolButton#IconButton {{
        background-color: transparent;
        border: none;
        border-radius: {Radius.SM}px;
        padding: 6px;
    }}
    QPushButton#IconButton:hover, QToolButton#IconButton:hover {{
        background-color: {Color.PANEL_SOFT};
    }}
    QPushButton#IconButton[active="true"], QToolButton#IconButton[active="true"] {{
        background-color: {Color.PRIMARY_SOFT};
    }}
    QToolButton#NavButton {{
        background-color: transparent;
        border: none;
        border-radius: {Radius.SM}px;
        color: {Color.MUTED};
        font-size: {Type.CAPTION}px;
        padding: 6px;
    }}
    QToolButton#NavButton:hover {{
        background-color: {Color.PANEL_ALT};
    }}
    QToolButton#NavButton[active="true"] {{
        background-color: {Color.PANEL_SOFT};
        color: {Color.TEXT};
    }}

    QComboBox, QLineEdit {{
        background-color: {Color.INPUT_BG};
        border: 1px solid {Color.BORDER_STRONG};
        border-radius: {Radius.SM}px;
        padding: 5px 8px;
        min-height: 22px;
    }}
    QComboBox:hover, QLineEdit:hover {{
        border-color: {Color.PRIMARY};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 22px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {Color.PANEL_ALT};
        border: 1px solid {Color.BORDER_STRONG};
        selection-background-color: {Color.PRIMARY_SOFT};
        selection-color: {Color.PRIMARY};
        outline: none;
    }}

    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid {Color.BORDER_STRONG};
        background-color: {Color.INPUT_BG};
    }}
    QCheckBox::indicator:checked {{
        background-color: {Color.PRIMARY};
        border-color: {Color.PRIMARY};
    }}

    QProgressBar {{
        background-color: {Color.PANEL_SOFT};
        border: none;
        border-radius: 4px;
        height: 8px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background-color: {Color.PRIMARY};
        border-radius: 4px;
    }}

    QTableWidget {{
        background-color: {Color.PANEL_ALT};
        alternate-background-color: {Color.PANEL_SOFT};
        gridline-color: {Color.BORDER};
        border: 1px solid {Color.BORDER};
        border-radius: {Radius.SM}px;
        selection-background-color: {Color.PRIMARY_SOFT};
        selection-color: {Color.TEXT};
    }}
    QTableWidget::item {{
        padding: 6px;
    }}
    QHeaderView::section {{
        background-color: {Color.PANEL_SOFT};
        color: {Color.MUTED};
        padding: 6px;
        border: none;
        border-bottom: 1px solid {Color.BORDER};
        font-weight: 600;
        font-size: {Type.CAPTION}px;
    }}

    QSplitter::handle {{
        background-color: {Color.BORDER};
    }}
    QSplitter::handle:vertical {{
        height: 3px;
        margin: 2px {Space.MD}px;
    }}
    QSplitter::handle:hover {{
        background-color: {Color.PRIMARY};
    }}

    QTabWidget::pane {{
        background-color: {Color.BG};
        border: 1px solid {Color.BORDER};
        border-radius: {Radius.MD}px;
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: transparent;
        color: {Color.MUTED};
        padding: 8px 16px;
        margin-right: 4px;
        border-top-left-radius: {Radius.SM}px;
        border-top-right-radius: {Radius.SM}px;
        font-weight: 600;
        font-size: {Type.BODY}px;
    }}
    QTabBar::tab:hover {{
        color: {Color.TEXT};
        background-color: {Color.PANEL_ALT};
    }}
    QTabBar::tab:selected {{
        color: {Color.PRIMARY};
        background-color: {Color.PANEL};
        border: 1px solid {Color.BORDER};
        border-bottom: none;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {Color.PANEL_SOFT};
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {Color.BORDER_STRONG};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {Color.PANEL_SOFT};
        border-radius: 4px;
        min-width: 24px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    QWidget#NavRail {{
        background-color: {Color.SIDEBAR};
        border-right: 1px solid {Color.BORDER};
    }}
    QWidget#TopBar {{
        background-color: {Color.PANEL};
        border-bottom: 1px solid {Color.BORDER};
    }}
    QLabel#AppTitle {{
        font-size: {Type.HEADING}px;
        font-weight: 700;
    }}
    """
