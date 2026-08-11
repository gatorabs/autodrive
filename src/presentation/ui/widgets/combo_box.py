from __future__ import annotations

from PySide6.QtWidgets import QComboBox


class ComboBox(QComboBox):
    """QComboBox that ignores mouse-wheel scrolling.

    Plain QComboBox changes its selected value when the wheel is scrolled
    over it, even without focus - a common source of accidental changes
    when scrolling past it inside a panel. Ignoring the event here lets it
    bubble up to the parent (e.g. a QScrollArea) instead.
    """

    def wheelEvent(self, event) -> None:
        event.ignore()
