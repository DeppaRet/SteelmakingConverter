"""
converter3d/widget.py
Python-side wrapper for the BOF converter panel.

Backend priority (chosen automatically):
  1. OpenGL  (QOpenGLWidget + PyOpenGL) — true 3-D, mouse rotation, tapping.
  2. WebEngine (Three.js via QWebEngineView) — if PyQtWebEngine loads cleanly.
  3. QPainter cross-section — pure PyQt5 fallback, zero extra dependencies.

Exported names:
  ConverterWidget       — whichever backend is active.
  WEBENGINE_AVAILABLE   — bool, True when Three.js backend is used.

Both backends expose the same public API:
  update_state(dict)  — push new process data; keys documented below.
"""

import json
import math
import os
import random
import site
import sys

from PyQt5.QtCore import QObject, QTimer, QUrl, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import (
    QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath,
    QPen, QRadialGradient,
)
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

# On Windows + Python ≥ 3.8, Qt5 DLLs that ship with user-level PyQtWebEngine
# live in a non-standard location and won't be found by the default DLL loader
# unless we add them explicitly before the import is attempted.
if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    _candidates: list[str] = []
    try:
        _candidates.append(site.getusersitepackages())
    except Exception:
        pass
    try:
        _candidates.extend(site.getsitepackages())
    except Exception:
        pass
    for _sp in _candidates:
        _dll_dir = os.path.join(_sp, "PyQt5", "Qt5", "bin")
        if os.path.isdir(_dll_dir):
            try:
                os.add_dll_directory(_dll_dir)
            except OSError:
                pass

def _probe_webengine() -> bool:
    """Spawn a child process that mirrors the main-process DLL environment.

    We pass the exact same sys.path so that DLLs are loaded from the
    same locations as in the main process.  This prevents false positives
    from a 'cleaner' subprocess picking up different Qt DLLs.
    """
    import json
    import subprocess

    _PROBE = """\
import sys, json, os
sys.path[:] = json.loads(sys.argv[1])
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS","--no-sandbox")
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView as _W
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
app = QtWidgets.QApplication([])
w = _W()
sys.stdout.write("OK")
sys.stdout.flush()
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", _PROBE, json.dumps(sys.path)],
            timeout=15,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        return result.returncode == 0 and "OK" in result.stdout
    except Exception:
        return False


try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
    from PyQt5.QtWebChannel import QWebChannel
    _we_import_ok = True
except (ImportError, OSError):
    _we_import_ok = False

WEBENGINE_AVAILABLE: bool = _we_import_ok and _probe_webengine()


# ══════════════════════════════════════════════════════════════════════════════
# Backend A — Three.js via QWebEngineView
# ══════════════════════════════════════════════════════════════════════════════

class ConverterBridge(QObject):
    """QObject exposed to JS via QWebChannel."""

    stateChanged = pyqtSignal(str)

    @pyqtSlot(str)
    def on_ready(self, message: str) -> None:
        pass


class _WebEngineConverterWidget(QWidget):
    """Three.js 3D panel (used when WebEngine is available)."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._bridge = ConverterBridge()
        self._view = QWebEngineView()

        self._view.settings().setAttribute(
            QWebEngineSettings.LocalContentCanAccessRemoteUrls, True
        )

        self._channel = QWebChannel()
        self._channel.registerObject("bridge", self._bridge)
        self._view.page().setWebChannel(self._channel)

        html_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "converter.html"
        )
        self._view.load(QUrl.fromLocalFile(html_path))
        layout.addWidget(self._view)

    def update_state(self, state: dict) -> None:
        json_str = json.dumps(state)
        self._bridge.stateChanged.emit(json_str)
        self._view.page().runJavaScript(
            f"if(typeof updateConverter!=='undefined')updateConverter({json_str});"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Backend B — QPainter cross-section diagram (pure PyQt5 fallback)
# ══════════════════════════════════════════════════════════════════════════════

class _PainterConverterWidget(QWidget):
    """Animated BOF converter cross-section drawn with QPainter.

    Requires no packages beyond PyQt5.  Renders at ~30 FPS via QTimer.
    Reflects the same state keys as the WebEngine backend.
    """

    _STATE_LABELS = {
        'idle':     'ОЖИДАНИЕ',
        'charged':  'ЗАГРУЖЕНО',
        'blowing':  'ПРОДУВКА',
        'complete': 'ГОТОВО',
    }

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMinimumHeight(320)

        self._s: dict = {
            'state':       'idle',
            'metalLevel':  0.0,
            'slagLevel':   0.0,
            'temperature': 1400,
            'blastFlow':   0,
            'metalMass':   0,
            'slagMass':    0,
        }
        self._anim:   float = 0.0
        self._sparks: list  = []   # each: [nx, ny, vx, vy, life]

        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(33)

    # ── public API ────────────────────────────────────────────────────────────
    def update_state(self, state: dict) -> None:
        self._s.update(state)
        if state.get('state') == 'idle':
            self._sparks.clear()

    # ── animation tick ────────────────────────────────────────────────────────
    def _tick(self) -> None:
        self._anim += 0.033
        is_blowing = self._s['state'] == 'blowing'

        if is_blowing and self._s['metalLevel'] > 0:
            if len(self._sparks) < 80 and random.random() < 0.55:
                nx = 0.50 + (random.random() - 0.5) * 0.04
                ny = self._lance_tip_norm()
                vx = (random.random() - 0.5) * 0.016
                vy = (random.random() - 0.5) * 0.016
                lf = 18 + int(random.random() * 28)
                self._sparks.append([nx, ny, vx, vy, lf])

        new_sparks = []
        for sp in self._sparks:
            sp[0] += sp[2]
            sp[1] += sp[3]
            sp[3] += 0.0012   # gravity
            sp[4] -= 1
            if sp[4] > 0:
                new_sparks.append(sp)
        self._sparks = new_sparks

        self.update()

    def _lance_tip_norm(self) -> float:
        """Lance tip Y in [0, 1] (0=top of widget)."""
        if self._s['state'] == 'blowing' and self._s['metalLevel'] > 0:
            metal_h_frac = self._s['metalLevel'] * 0.32
            # body top ~0.17, body bottom ~0.87 in norm coords
            metal_norm_y = 0.87 - metal_h_frac
            return metal_norm_y - 0.06
        return 0.03

    # ── paint ─────────────────────────────────────────────────────────────────
    def paintEvent(self, _event) -> None:  # noqa: N802
        s = self._s
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        is_blowing  = s['state'] == 'blowing'
        is_complete = s['state'] == 'complete'
        is_charged  = s['state'] in ('charged', 'blowing', 'complete')

        # ── background ───────────────────────────────────────────────────────
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor(10, 10, 24))
        bg.setColorAt(1, QColor(16, 12, 28))
        p.fillRect(self.rect(), QBrush(bg))

        # ── geometry constants ───────────────────────────────────────────────
        cx      = w * 0.50
        body_w  = w * 0.78
        neck_w  = body_w * 0.36
        top_w   = body_w * 0.66
        inset   = 8            # lining thickness px

        y_top    = h * 0.07
        y_neck   = h * 0.17
        y_body   = h * 0.83
        y_bot    = h * 0.93

        def _vessel_path(bi: float = 0) -> QPainterPath:
            """Build vessel outline; bi = inset (0=outer, inset=inner)."""
            nw = neck_w - bi * 1.0
            tw = top_w  - bi * 1.2
            bw = body_w - bi * 2.0
            path = QPainterPath()
            path.moveTo(cx - nw/2, y_top   + bi * 0.3)
            path.lineTo(cx - tw/2, y_neck  + bi * 0.3)
            path.lineTo(cx - bw/2, y_body  - bi * 0.5)
            path.quadTo(cx - bw/2, y_bot   - bi * 0.8,
                        cx,        y_bot   - bi * 1.2)
            path.quadTo(cx + bw/2, y_bot   - bi * 0.8,
                        cx + bw/2, y_body  - bi * 0.5)
            path.lineTo(cx + tw/2, y_neck  + bi * 0.3)
            path.lineTo(cx + nw/2, y_top   + bi * 0.3)
            path.closeSubpath()
            return path

        outer = _vessel_path(0)
        inner = _vessel_path(inset)

        # ── outer shell ───────────────────────────────────────────────────────
        sh_g = QLinearGradient(cx - body_w/2, 0, cx + body_w/2, 0)
        sh_g.setColorAt(0.0, QColor(48, 38, 62))
        sh_g.setColorAt(0.3, QColor(68, 56, 85))
        sh_g.setColorAt(0.7, QColor(58, 47, 74))
        sh_g.setColorAt(1.0, QColor(44, 35, 56))
        p.fillPath(outer, QBrush(sh_g))

        # ── inner lining ──────────────────────────────────────────────────────
        li_g = QLinearGradient(cx - body_w/2, 0, cx + body_w/2, 0)
        li_g.setColorAt(0,   QColor(52, 30, 10))
        li_g.setColorAt(0.5, QColor(72, 42, 14))
        li_g.setColorAt(1,   QColor(52, 30, 10))
        p.fillPath(inner, QBrush(li_g))

        # ── metal fill ────────────────────────────────────────────────────────
        if is_charged and s['metalLevel'] > 0:
            mh       = s['metalLevel'] * (y_body - y_neck - 22)
            metal_y  = y_body - 10 - mh

            t = s.get('temperature', 1400)
            f = max(0.0, min(1.0, (t - 1300) / 420))
            mr = int(185 + 70 * f)
            mg_ = int(28 + 100 * f)

            # Width of inner vessel at metal_y
            y_frac     = max(0, (metal_y - y_neck) / max(1, y_body - y_neck))
            inner_half = ((top_w - inset * 1.2)/2
                          + ((body_w - inset * 2)/2 - (top_w - inset * 1.2)/2)
                          * y_frac)

            metal_path = QPainterPath()
            metal_path.moveTo(cx - inner_half, metal_y)
            metal_path.lineTo(cx + inner_half, metal_y)
            bw_i = (body_w - inset * 2) / 2
            metal_path.lineTo(cx + bw_i, y_body - inset * 0.5)
            metal_path.quadTo(cx + bw_i, y_bot - inset * 0.8,
                              cx,        y_bot - inset * 1.2)
            metal_path.quadTo(cx - bw_i, y_bot - inset * 0.8,
                              cx - bw_i, y_body - inset * 0.5)
            metal_path.closeSubpath()

            me_g = QLinearGradient(0, metal_y, 0, y_bot)
            me_g.setColorAt(0,   QColor(mr, mg_, 0, 210))
            me_g.setColorAt(0.4, QColor(int(mr * 0.82), int(mg_ * 0.55), 0, 225))
            me_g.setColorAt(1,   QColor(int(mr * 0.55), 15, 0, 240))
            p.fillPath(metal_path.intersected(inner), QBrush(me_g))

            # shimmer line
            shimmer = math.sin(self._anim * 13) * 1.8 if is_blowing else 0
            surf_y  = metal_y + shimmer
            s_pen   = QPen(QColor(mr + 35, mg_ + 35, 20, 190))
            s_pen.setWidth(2)
            p.setPen(s_pen)
            p.drawLine(int(cx - inner_half), int(surf_y),
                       int(cx + inner_half), int(surf_y))

            # glow above metal surface
            if is_blowing or is_complete:
                gw = inner_half
                gr = QRadialGradient(cx, surf_y, gw * 0.9)
                gr.setColorAt(0, QColor(mr, mg_, 0, 75))
                gr.setColorAt(1, QColor(0, 0, 0, 0))
                glow_p = QPainterPath()
                glow_p.addEllipse(cx - gw, surf_y - 18, gw * 2, 36)
                p.fillPath(glow_p.intersected(inner), QBrush(gr))

            # ── slag layer ────────────────────────────────────────────────────
            if s['slagLevel'] > 0 and mh > 2:
                sl_h  = s['slagLevel'] * 32
                sl_y  = surf_y - sl_h
                y_fs  = max(0, (sl_y - y_neck) / max(1, y_body - y_neck))
                ih_s  = ((top_w - inset * 1.2)/2
                         + ((body_w - inset * 2)/2 - (top_w - inset * 1.2)/2)
                         * y_fs)
                sl_g  = QLinearGradient(0, sl_y, 0, surf_y)
                sl_g.setColorAt(0, QColor(118, 92, 25, 155))
                sl_g.setColorAt(1, QColor(88,  68, 12, 195))
                sl_p  = QPainterPath()
                sl_p.moveTo(cx - ih_s, sl_y)
                sl_p.lineTo(cx + ih_s, sl_y)
                sl_p.lineTo(cx + inner_half, surf_y)
                sl_p.lineTo(cx - inner_half, surf_y)
                sl_p.closeSubpath()
                p.fillPath(sl_p.intersected(inner), QBrush(sl_g))

            self._metal_y      = metal_y
            self._inner_half   = inner_half
        else:
            self._metal_y    = y_body - 10
            self._inner_half = (body_w - inset * 2) / 2

        # ── vessel outline ────────────────────────────────────────────────────
        w_pen = QPen(QColor(0, 168, 205, 150))
        w_pen.setWidth(2)
        p.setPen(w_pen)
        p.drawPath(outer)

        # ── trunnion ring ─────────────────────────────────────────────────────
        ring_y  = y_neck + (y_body - y_neck) * 0.40
        ring_rw = body_w * 0.64
        r_g     = QLinearGradient(cx - ring_rw/2, 0, cx + ring_rw/2, 0)
        r_g.setColorAt(0,   QColor(75, 75, 96, 190))
        r_g.setColorAt(0.5, QColor(108, 106, 128, 230))
        r_g.setColorAt(1,   QColor(75, 75, 96, 190))
        r_pen = QPen(QBrush(r_g), 11)
        r_pen.setCapStyle(Qt.RoundCap)
        p.setPen(r_pen)
        p.drawLine(int(cx - ring_rw/2), int(ring_y),
                   int(cx + ring_rw/2), int(ring_y))
        ax_pen = QPen(QColor(100, 100, 122, 210))
        ax_pen.setWidth(6)
        p.setPen(ax_pen)
        for side in (-1, 1):
            x0 = cx + side * ring_rw / 2
            p.drawLine(int(x0), int(ring_y),
                       int(x0 + side * 14), int(ring_y))

        # ── oxygen lance ──────────────────────────────────────────────────────
        lance_anim = math.sin(self._anim * 8) * 1.5 if is_blowing else 0

        if is_blowing and s['metalLevel'] > 0:
            tip_y = self._metal_y - 28 + lance_anim
        else:
            tip_y = y_top - 14 + lance_anim

        top_y = tip_y - min(100, tip_y + 10)
        l_pen = QPen(QColor(140, 200, 255, 225))
        l_pen.setWidth(4)
        p.setPen(l_pen)
        p.drawLine(int(cx), int(max(-6, top_y)), int(cx), int(tip_y))

        n_pen = QPen(QColor(190, 235, 255, 210))
        n_pen.setWidth(5)
        p.setPen(n_pen)
        p.drawEllipse(int(cx - 4), int(tip_y - 4), 8, 8)

        if is_blowing:
            gr2 = QRadialGradient(cx, tip_y, 22)
            gr2.setColorAt(0, QColor(100, 200, 255, 115))
            gr2.setColorAt(1, QColor(0, 0, 0, 0))
            gp2 = QPainterPath()
            gp2.addEllipse(cx - 22, tip_y - 22, 44, 44)
            p.fillPath(gp2, QBrush(gr2))

        p.setPen(QPen(QColor(130, 225, 255, 185)))
        p.setFont(QFont("Courier New", 8, QFont.Bold))
        p.drawText(int(cx + 7), int(max(15, top_y + 14)), "O₂")

        # ── sparks ────────────────────────────────────────────────────────────
        if is_blowing and self._sparks:
            sp_pen = QPen()
            sp_pen.setWidth(2)
            for sp in self._sparks:
                lf = sp[4]
                alpha = int((lf / 30.0) * 230)
                sp_pen.setColor(QColor(255, int(min(255, 140 + lf * 3)), 0, alpha))
                p.setPen(sp_pen)
                p.drawPoint(int(sp[0] * w), int(sp[1] * h))

        # ── HUD text ──────────────────────────────────────────────────────────
        label = self._STATE_LABELS.get(s['state'], 'ОЖИДАНИЕ')
        if s['state'] == 'complete':
            badge_col = QColor(255, 100, 20, 220)
        elif s['state'] == 'blowing':
            badge_col = QColor(255, 200, 0, 220)
        else:
            badge_col = QColor(0, 200, 240, 220)

        p.setPen(QPen(badge_col))
        p.setFont(QFont("Courier New", 9, QFont.Bold))
        p.drawText(8, 18, label)

        # metrics row
        parts = []
        if s['metalMass'] > 0:
            parts.append(f"Ме {s['metalMass']:.0f}т")
        if s['slagMass'] > 0:
            parts.append(f"Шл {s['slagMass']:.0f}т")
        if s.get('temperature', 0) > 0 and s['state'] in ('blowing', 'complete'):
            parts.append(f"T {s['temperature']:.0f}°C")
        if s.get('blastFlow', 0) > 0:
            parts.append(f"O₂ {s['blastFlow']:.0f}м³")

        if parts:
            p.setPen(QPen(QColor(0, 200, 240, 180)))
            p.setFont(QFont("Courier New", 7))
            p.drawText(8, h - 8, "  |  ".join(parts))

        p.end()


# ══════════════════════════════════════════════════════════════════════════════
# Public alias: pick the best available backend
#   Priority: OpenGL  >  WebEngine  >  QPainter
# ══════════════════════════════════════════════════════════════════════════════

try:
    from converter3d.opengl_widget import ConverterGLPanel as ConverterWidget  # noqa: F401
except Exception:
    if WEBENGINE_AVAILABLE:
        ConverterWidget = _WebEngineConverterWidget
    else:
        ConverterWidget = _PainterConverterWidget
