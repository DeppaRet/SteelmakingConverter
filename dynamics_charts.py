"""Графики динамики плавки (pyqtgraph, 2×2)."""

from __future__ import annotations

from typing import Any

from PyQt5 import QtWidgets

import app_theme
from theme_settings import get_theme

try:
    import pyqtgraph as pg
except ImportError:
    pg = None  # type: ignore


class DynamicsChartsWidget(QtWidgets.QWidget):
    """Четыре графика: [C]/[Si]/[Mn], T, v_C, η_CO и Z."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        *,
        compact: bool = False,
        expand_in_tab: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("dynamics_charts_widget")
        self._compact = compact
        self._expand_in_tab = expand_in_tab
        if expand_in_tab:
            self.setMinimumHeight(140)
            self.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding,
            )
        elif compact:
            self.setFixedHeight(118)
            self.setMinimumHeight(118)
            self.setMaximumHeight(118)
        else:
            self.setMinimumHeight(200)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        if pg is None:
            self._fallback = QtWidgets.QLabel(
                "Установите pyqtgraph: pip install -r requirements-dynamics.txt"
            )
            self._fallback.setWordWrap(True)
            lay.addWidget(self._fallback)
            self._plots = None
            return

        self._fallback = None
        self._theme = get_theme()
        pg.setConfigOptions(antialias=True)
        grid = pg.GraphicsLayoutWidget()
        lay.addWidget(grid)
        self._grid = grid

        title_sz = "8pt" if self._compact else "11pt"
        self._plot_c = grid.addPlot(row=0, col=0, title="[C], [Si], [Mn]")
        self._plot_c.setLabel("left", "%")
        self._plot_c.setTitle("[C], [Si], [Mn]", size=title_sz)
        if not self._compact:
            self._plot_c.addLegend(offset=(5, 5))
        self._curve_c = self._plot_c.plot(pen=pg.mkPen(width=2))
        self._curve_si = self._plot_c.plot(pen=pg.mkPen(width=1.5))
        self._curve_mn = self._plot_c.plot(pen=pg.mkPen(width=1.5))

        self._plot_t = grid.addPlot(row=0, col=1, title="T")
        self._plot_t.setLabel("left", "°C")
        self._plot_t.setTitle("T", size=title_sz)
        self._curve_t = self._plot_t.plot(pen=pg.mkPen(width=2))

        self._plot_vc = grid.addPlot(row=1, col=0, title="v_C")
        self._plot_vc.setLabel("left", "%/мин")
        self._plot_vc.setTitle("v_C", size=title_sz)
        self._curve_vc = self._plot_vc.plot(pen=pg.mkPen(width=2))

        self._plot_eta = grid.addPlot(row=1, col=1, title="η_CO, Z×100")
        self._plot_eta.setLabel("left", "% / Z×100")
        self._plot_eta.setTitle("η·Z", size=title_sz)
        self._curve_eta = self._plot_eta.plot(pen=pg.mkPen(width=2), name="η_CO")
        self._curve_z = self._plot_eta.plot(pen=pg.mkPen(width=2), name="Z×100")
        self._apply_chart_theme(self._theme)
        if self._compact:
            for plot in (
                self._plot_c,
                self._plot_t,
                self._plot_vc,
                self._plot_eta,
            ):
                plot.showGrid(x=True, y=True, alpha=0.2)
        self._plots = (
            self._curve_c,
            self._curve_si,
            self._curve_mn,
            self._curve_t,
            self._curve_vc,
            self._curve_eta,
            self._curve_z,
        )

    def _theme_colors(self) -> dict[str, str]:
        t = app_theme.tokens(getattr(self, "_theme", None) or get_theme())
        return {
            "accent": t["accent"],
            "warn": t["control_warn"],
            "danger": t["control_danger"],
            "muted": t["text_muted"],
            "success": t["control_success_green"],
        }

    def _apply_chart_theme(self, theme: str) -> None:
        if pg is None or not hasattr(self, "_plot_c"):
            return
        t = app_theme.tokens(theme)
        fg = t["text"]
        bg = t.get("table_bg") or t["window_bg2"]
        for plot in (
            self._plot_c,
            self._plot_t,
            self._plot_vc,
            self._plot_eta,
        ):
            plot.getAxis("bottom").setPen(pg.mkPen(fg))
            plot.getAxis("left").setPen(pg.mkPen(fg))
            plot.getAxis("bottom").setTextPen(pg.mkPen(fg))
            plot.getAxis("left").setTextPen(pg.mkPen(fg))
            if plot.getAxis("right") is not None:
                plot.getAxis("right").setPen(pg.mkPen(fg))
                plot.getAxis("right").setTextPen(pg.mkPen(fg))
        if hasattr(self, "_grid"):
            self._grid.setBackground(bg)
        c = self._theme_colors()
        self._curve_c.setPen(pg.mkPen(c["accent"], width=2))
        self._curve_si.setPen(pg.mkPen(c["warn"], width=1.5))
        self._curve_mn.setPen(pg.mkPen(c["muted"], width=1.5))
        self._curve_t.setPen(pg.mkPen(c["danger"], width=2))
        self._curve_vc.setPen(pg.mkPen(c["success"], width=2))
        self._curve_eta.setPen(pg.mkPen(c["accent"], width=2))
        self._curve_z.setPen(pg.mkPen(c["warn"], width=2))

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self._apply_chart_theme(theme)

    def update_curves(self, snapshots: list[dict[str, Any]]) -> None:
        if not snapshots or self._plots is None:
            return
        t = [s.get("t_min", 0.0) for s in snapshots]
        self._curve_c.setData(t, [s.get("C", 0.0) for s in snapshots])
        self._curve_si.setData(t, [s.get("Si", 0.0) for s in snapshots])
        self._curve_mn.setData(t, [s.get("Mn", 0.0) for s in snapshots])
        self._curve_t.setData(t, [s.get("T", 0.0) for s in snapshots])
        self._curve_vc.setData(t, [s.get("v_C", 0.0) for s in snapshots])
        self._curve_eta.setData(t, [s.get("eta_CO", 0.0) for s in snapshots])
        self._curve_z.setData(t, [s.get("Z", 0.0) * 100.0 for s in snapshots])

    def clear(self) -> None:
        if self._plots is None:
            return
        for curve in self._plots:
            curve.setData([], [])
