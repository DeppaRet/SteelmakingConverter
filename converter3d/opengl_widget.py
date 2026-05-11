"""
converter3d/opengl_widget.py
True interactive 3D BOF converter via QOpenGLWidget + PyOpenGL.

Features:
  - Left-drag  : orbit camera (azimuth + elevation)
  - Scroll     : zoom
  - Animated states: idle / charged / blowing / complete (tapping)
  - Tapping animation: converter tilts ~130°, molten metal pours out
  - Sparks & smoke during oxygen blow
"""

import math
import random

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QOpenGLWidget, QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QFont, QSurfaceFormat

try:
    from OpenGL.GL import (
        glBegin, glEnd, glVertex3f, glNormal3f, glColor4f, glColor3f,
        glClearColor, glEnable, glDisable, glClear, glLoadIdentity,
        glPushMatrix, glPopMatrix, glTranslatef, glRotatef, glScalef,
        glBlendFunc, glPointSize, glLineWidth,
        glMaterialfv, glMateriali, glLightfv, glColorMaterial, glShadeModel,
        glViewport, glMatrixMode,
        GL_DEPTH_TEST, GL_BLEND, GL_LIGHTING, GL_LIGHT0, GL_LIGHT1,
        GL_COLOR_MATERIAL, GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE,
        GL_SPECULAR, GL_SHININESS, GL_SMOOTH, GL_NORMALIZE,
        GL_POSITION, GL_DIFFUSE, GL_AMBIENT,
        GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
        GL_PROJECTION, GL_MODELVIEW,
        GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN, GL_POINTS, GL_LINES,
        GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
    )
    from OpenGL.GLU import gluPerspective, gluLookAt, gluNewQuadric, gluCylinder, gluDisk, gluDeleteQuadric
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _draw_revolution(profile, segments=44, inside=False):
    """Render a surface of revolution from a 2-D profile [(r, y), ...]."""
    for i in range(len(profile) - 1):
        r0, y0 = profile[i]
        r1, y1 = profile[i + 1]
        dr = r1 - r0
        dy = y1 - y0
        ln = math.sqrt(dr * dr + dy * dy) or 1e-9
        n_r = dy / ln * (-1 if inside else 1)
        n_y = -dr / ln * (-1 if inside else 1)

        glBegin(GL_TRIANGLE_STRIP)
        for j in range(segments + 1):
            a = j / segments * 2.0 * math.pi
            ct, st = math.cos(a), math.sin(a)
            glNormal3f(n_r * ct, n_y, n_r * st)
            glVertex3f(r0 * ct, y0, r0 * st)
            glNormal3f(n_r * ct, n_y, n_r * st)
            glVertex3f(r1 * ct, y1, r1 * st)
        glEnd()


def _draw_disc(radius, y, segments=44, up=True):
    """Render a horizontal disc."""
    glBegin(GL_TRIANGLE_FAN)
    glNormal3f(0.0, 1.0 if up else -1.0, 0.0)
    glVertex3f(0.0, y, 0.0)
    it = range(segments + 1) if not up else range(segments, -1, -1)
    for i in it:
        a = i / segments * 2.0 * math.pi
        glVertex3f(radius * math.cos(a), y, radius * math.sin(a))
    glEnd()


def _draw_cylinder_capped(r, y_bot, y_top, segments=36):
    """Solid cylinder with both caps."""
    _draw_revolution([(r, y_bot), (r, y_top)], segments)
    _draw_disc(r, y_bot, segments, up=False)
    _draw_disc(r, y_top, segments, up=True)


def _temp_color(t):
    """Return (R, G, B) for molten metal at temperature t °C."""
    f = max(0.0, min(1.0, (t - 1300) / 400.0))
    return (0.95 + 0.05 * f, 0.25 + 0.45 * f, 0.02)


# ---------------------------------------------------------------------------
# BOF outer / inner shell profiles  (r, y)
# ---------------------------------------------------------------------------

OUTER_PROFILE = [
    (0.04, 0.00),
    (0.46, 0.13),
    (0.74, 0.34),
    (0.83, 0.72),
    (0.84, 1.50),
    (0.76, 1.82),
    (0.53, 2.04),
    (0.34, 2.24),
    (0.31, 2.46),
]

INNER_PROFILE = [
    (0.02, 0.02),
    (0.40, 0.15),
    (0.67, 0.36),
    (0.75, 0.73),
    (0.76, 1.49),
    (0.69, 1.81),
    (0.46, 2.02),
    (0.28, 2.22),
    (0.25, 2.44),
]

TRUNNION_Y    = 1.20   # height of trunnion ring centre
INNER_BODY_R  = 0.75   # radius in wide body section
INNER_NECK_R  = 0.26   # radius at the top opening
TOP_Y         = 2.44   # y of opening tip
BOT_Y         = 0.02   # y of the very bottom

# metalLevel arrives pre-scaled by 0.62 from OperForm.
# METAL_H_SCALE compensates so the fill visually occupies ~50-55% of vessel height.
METAL_H_SCALE = 2.30
SLAG_H_SCALE  = 0.45


# ---------------------------------------------------------------------------
# Main GL widget
# ---------------------------------------------------------------------------

class ConverterGLWidget(QOpenGLWidget):
    """Interactive 3D BOF converter.

    Public API
    ----------
    update_state(dict)  – push process data; keys:
        state       : 'idle' | 'charged' | 'blowing' | 'complete'
        metalLevel  : 0..1
        slagLevel   : 0..1
        temperature : °C
        blastFlow   : m³/min
        metalMass   : t
        slagMass    : t
    """

    def __init__(self, parent=None):
        fmt = QSurfaceFormat()
        fmt.setSamples(4)                   # 4× MSAA
        fmt.setDepthBufferSize(24)
        QSurfaceFormat.setDefaultFormat(fmt)
        super().__init__(parent)

        self._az  = -30.0    # azimuth  (Y-axis rotation)
        self._el  =  22.0    # elevation (X-axis rotation)
        self._dist = 7.5     # camera distance
        self._last_mouse = None

        self._s = {
            'state':      'idle',
            'metalLevel': 0.0,
            'slagLevel':  0.0,
            'temperature': 1400,
            'blastFlow':  0,
            'metalMass':  0,
            'slagMass':   0,
        }
        self._anim        = 0.0
        self._tilt        = 0.0       # current converter tilt angle (°)
        self._tilt_target = 0.0       # target tilt angle
        self._lance_y     = 4.8       # current lance tip height
        self._lance_tgt   = 4.8
        self._sparks      = []        # [x,y,z, vx,vy,vz, life, max_life]
        self._pour        = []

        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(33)

    # ------------------------------------------------------------------
    def update_state(self, state: dict):
        self._s.update(state)
        st = self._s['state']
        mh = self._s['metalLevel'] * 1.40

        # _lance_y is the Y of the TOP of the visible lance section.
        # Lance tip  = _lance_y - 2.24  (pipe length 2.3, offset 0.06)
        # → to place the tip 0.25 m above the metal surface:
        #   _lance_tgt = BOT_Y + mh + 0.25 + 2.24 = BOT_Y + mh + 2.49
        mh = self._s['metalLevel'] * METAL_H_SCALE
        if st == 'complete':
            self._tilt_target  = 130.0
            self._lance_tgt    = 4.8
        elif st == 'blowing':
            self._tilt_target  = 0.0
            self._lance_tgt    = BOT_Y + mh + 2.49
        else:
            self._tilt_target  = 0.0
            self._lance_tgt    = 4.8

    # ------------------------------------------------------------------
    def _tick(self):
        self._anim += 0.033
        dt = 0.033

        # Smooth lerp for tilt and lance
        self._tilt    += (self._tilt_target  - self._tilt)    * 0.025
        self._lance_y += (self._lance_tgt    - self._lance_y) * 0.04

        blowing = (self._s['state'] == 'blowing')
        _ml, _ = self._effective_levels()
        # Stop pouring once the converter is visually empty (ml near 0)
        tapping = (self._s['state'] == 'complete' and self._tilt > 35.0
                   and _ml > 0.01)

        # --- sparks during blow ---
        # Lance tip is at _lance_y - 2.24  (top offset 0.06, pipe 2.30)
        lance_tip_y = self._lance_y - 2.24
        if blowing and len(self._sparks) < 120:
            for _ in range(4):
                spd = 0.025 + random.random() * 0.05
                ang = random.random() * math.pi * 2
                el  = (random.random() - 0.15) * math.pi * 0.6
                self._sparks.append([
                    0.0, lance_tip_y, 0.0,
                    math.cos(el) * math.cos(ang) * spd,
                    math.cos(el) * math.sin(ang) * spd * 0.4 + 0.015,
                    math.sin(el) * spd,
                    30 + int(random.random() * 25),
                    55,
                ])

        new_s = []
        for sp in self._sparks:
            sp[0] += sp[3]; sp[1] += sp[4]; sp[2] += sp[5]
            sp[4] -= 0.0025    # gravity
            sp[6] -= 1
            if sp[6] > 0:
                new_s.append(sp)
        self._sparks = new_s if blowing else []

        # --- metal pour during tapping ---
        # glRotatef(tilt, 0,0,1) is CCW around Z.  R_z(θ) applied to (0, dy_p):
        #   x' = -dy_p * sin(θ),   y' = dy_p * cos(θ)
        # Opening direction (was +Y): (-sin(θ), cos(θ), 0)
        if tapping and len(self._pour) < 80:
            tr  = math.radians(self._tilt)
            dy_p = TOP_Y - TRUNNION_Y          # 1.24
            wx  = -dy_p * math.sin(tr)         # opening world X
            wy  =  TRUNNION_Y + dy_p * math.cos(tr)  # opening world Y
            # initial velocity along opening direction, gravity does the rest
            ox  = -math.sin(tr) * 0.018
            oy  =  math.cos(tr) * 0.018 - 0.008
            for _ in range(3):
                self._pour.append([
                    wx + (random.random() - 0.5) * 0.16,
                    wy + (random.random() - 0.5) * 0.07,
                    (random.random() - 0.5) * 0.16,
                    ox + (random.random() - 0.5) * 0.007,
                    oy + (random.random() - 0.5) * 0.005,
                    (random.random() - 0.5) * 0.007,
                    40 + int(random.random() * 30),
                    70,
                ])

        new_p = []
        for pp in self._pour:
            pp[0] += pp[3]; pp[1] += pp[4]; pp[2] += pp[5]
            pp[4] -= 0.007
            pp[6] -= 1
            if pp[6] > 0:
                new_p.append(pp)
        self._pour = new_p if tapping else []

        self.update()

    # ------------------------------------------------------------------
    # GL lifecycle
    # ------------------------------------------------------------------

    def initializeGL(self):
        glClearColor(0.04, 0.04, 0.12, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)

        glLightfv(GL_LIGHT0, GL_POSITION, [6.0, 12.0, 6.0, 0.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.15, 1.15, 1.25, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.12, 0.12, 0.18, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.6,  0.6,  0.6,  1.0])

        glLightfv(GL_LIGHT1, GL_POSITION, [-5.0, 4.0, -4.0, 0.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE,  [0.25, 0.25, 0.45, 1.0])
        glLightfv(GL_LIGHT1, GL_AMBIENT,  [0.0,  0.0,  0.0,  1.0])

        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR,  [0.35, 0.35, 0.35, 1.0])
        glMateriali (GL_FRONT_AND_BACK, GL_SHININESS, 50)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, max(1, h))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(44.0, w / max(1, h), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Camera
        gluLookAt(0.0, 1.4, self._dist,
                  0.0, 1.4, 0.0,
                  0.0, 1.0, 0.0)
        glRotatef(self._el, 1.0, 0.0, 0.0)
        glRotatef(self._az, 0.0, 1.0, 0.0)

        self._draw_ground()

        # --- tilting group (vessel + metal + slag + trunnion) ---
        glPushMatrix()
        glTranslatef(0.0,  TRUNNION_Y, 0.0)
        glRotatef(self._tilt, 0.0, 0.0, 1.0)
        glTranslatef(0.0, -TRUNNION_Y, 0.0)

        self._draw_vessel_outer()
        self._draw_vessel_inner()
        self._draw_metal()
        self._draw_slag()
        self._draw_trunnion()

        glPopMatrix()

        # Lance does NOT tilt with converter
        if self._s['state'] != 'complete':
            self._draw_lance()

        # Particles
        self._draw_sparks()
        self._draw_pour()
        self._draw_hud()

    # ------------------------------------------------------------------
    # Scene objects
    # ------------------------------------------------------------------

    def _draw_ground(self):
        glColor4f(0.09, 0.08, 0.11, 1.0)
        _draw_revolution([(1.55, -0.07), (1.55, 0.07)], segments=40)
        _draw_disc(1.55, -0.07, segments=40, up=False)
        _draw_disc(1.55,  0.07, segments=40, up=True)

    def _effective_levels(self):
        """Return (metal_level, slag_level) adjusted for converter tilt.

        Emptying is spread over the full tilt range (5° → 130°) so it looks
        slow and deliberate. The converter is fully empty only at max tilt.
        """
        ml = self._s['metalLevel']
        sl = self._s['slagLevel']
        if self._s['state'] == 'complete' and self._tilt > 5.0:
            # pour_f reaches 1.0 only when tilt reaches 130° (max)
            pour_f = min(1.0, (self._tilt - 5.0) / 125.0)
            ml = ml * (1.0 - pour_f)
            sl = sl * (1.0 - pour_f * 0.85)
        return ml, sl

    def _draw_vessel_outer(self):
        glColor4f(0.30, 0.24, 0.38, 1.0)
        _draw_revolution(OUTER_PROFILE)
        _draw_disc(OUTER_PROFILE[0][0], OUTER_PROFILE[0][1],  up=False)

    def _draw_vessel_inner(self):
        glColor4f(0.38, 0.22, 0.10, 1.0)
        _draw_revolution(INNER_PROFILE, inside=True)

    def _draw_metal(self):
        ml, _ = self._effective_levels()
        if ml <= 0.0:
            return
        mh      = ml * METAL_H_SCALE
        metal_y = BOT_Y + mh
        r, g, b = _temp_color(self._s['temperature'])

        # Profile follows inner shell up to metal surface
        profile = []
        for (ri, yi) in INNER_PROFILE:
            if yi <= metal_y:
                profile.append((ri * 0.985, yi))
        if not profile:
            return
        profile.append((profile[-1][0], metal_y))

        glColor4f(r, g, b, 1.0)
        _draw_revolution(profile)
        _draw_disc(profile[0][0], BOT_Y, up=False)
        # Bright surface disc
        glColor4f(min(1.0, r * 1.25), min(1.0, g * 1.4), b * 0.5, 1.0)
        _draw_disc(profile[-1][0], metal_y, up=True)

    def _draw_slag(self):
        ml, sl = self._effective_levels()
        if sl <= 0.0 or ml <= 0.0:
            return
        metal_y = BOT_Y + ml * METAL_H_SCALE
        slag_h  = sl * SLAG_H_SCALE
        slag_y  = metal_y + slag_h
        ir = 0.74

        glColor4f(0.52, 0.40, 0.10, 0.90)
        _draw_revolution([(ir, metal_y), (ir, slag_y)])
        glColor4f(0.46, 0.35, 0.08, 0.85)
        _draw_disc(ir, slag_y, up=True)

    def _draw_trunnion(self):
        # Ring (torus approximation)
        glColor4f(0.42, 0.44, 0.52, 1.0)
        R, r_t, sm, st = 0.90, 0.068, 52, 14
        for i in range(sm):
            a0 = i       / sm * 2 * math.pi
            a1 = (i + 1) / sm * 2 * math.pi
            glBegin(GL_TRIANGLE_STRIP)
            for j in range(st + 1):
                b = j / st * 2 * math.pi
                for a in (a0, a1):
                    x  = (R + r_t * math.cos(b)) * math.cos(a)
                    z  = (R + r_t * math.cos(b)) * math.sin(a)
                    y  = TRUNNION_Y + r_t * math.sin(b)
                    nx = math.cos(b) * math.cos(a)
                    ny = math.sin(b)
                    nz = math.cos(b) * math.sin(a)
                    glNormal3f(nx, ny, nz)
                    glVertex3f(x, y, z)
            glEnd()

        # Axle pins on both sides
        glColor4f(0.46, 0.48, 0.56, 1.0)
        for side in (-1, 1):
            glPushMatrix()
            glTranslatef(side * 1.12, TRUNNION_Y, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            q = gluNewQuadric()
            gluCylinder(q, 0.055, 0.055, 0.28, 14, 1)
            gluDeleteQuadric(q)
            glPopMatrix()

    def _draw_lance(self):
        # gluCylinder draws along local +Z.  glRotatef(90, X) maps Z → -Y (down). ✓
        q = gluNewQuadric()
        top_y  = self._lance_y + 0.06
        tip_y  = self._lance_y - 2.24   # = top_y - 2.30

        # Main pipe
        glColor4f(0.55, 0.76, 0.88, 1.0)
        glPushMatrix()
        glTranslatef(0.0, top_y, 0.0)
        glRotatef(90.0, 1.0, 0.0, 0.0)   # Z → -Y (downward)
        gluCylinder(q, 0.027, 0.025, 2.3, 14, 1)
        glPopMatrix()

        # Cooling pipes (3 thin pipes around main pipe)
        glColor4f(0.45, 0.65, 0.78, 1.0)
        for ang_deg in (0, 120, 240):
            a = math.radians(ang_deg)
            ox, oz = 0.04 * math.cos(a), 0.04 * math.sin(a)
            glPushMatrix()
            glTranslatef(ox, top_y, oz)
            glRotatef(90.0, 1.0, 0.0, 0.0)
            gluCylinder(q, 0.010, 0.010, 2.3, 8, 1)
            glPopMatrix()

        # Nozzle head: cone at lance tip, narrowing downward
        glColor4f(0.65, 0.55, 0.35, 1.0)
        glPushMatrix()
        glTranslatef(0.0, tip_y, 0.0)
        glRotatef(90.0, 1.0, 0.0, 0.0)   # cone extends downward
        gluCylinder(q, 0.052, 0.0, 0.14, 16, 1)
        glPopMatrix()
        gluDeleteQuadric(q)

    def _draw_sparks(self):
        if not self._sparks:
            return
        glDisable(GL_LIGHTING)
        glPointSize(3.5)
        glBegin(GL_POINTS)
        for sp in self._sparks:
            f = sp[6] / max(1, sp[7])
            glColor4f(1.0, 0.65 * f + 0.35, 0.0, f)
            glVertex3f(sp[0], sp[1], sp[2])
        glEnd()
        glEnable(GL_LIGHTING)

    def _draw_pour(self):
        if not self._pour:
            return
        glDisable(GL_LIGHTING)
        glPointSize(5.0)
        r, g, b = _temp_color(self._s['temperature'])
        glBegin(GL_POINTS)
        for pp in self._pour:
            f = pp[6] / max(1, pp[7])
            glColor4f(r, g * (0.3 + 0.7 * f), b, 0.92 * f)
            glVertex3f(pp[0], pp[1], pp[2])
        glEnd()
        glEnable(GL_LIGHTING)

    def _draw_hud(self):
        """Overlay text drawn via QPainter on top of the GL scene."""
        from PyQt5.QtGui import QPainter, QColor, QFont
        from PyQt5.QtCore import QRect, Qt

        s = self._s
        state_label = {
            'idle':     'Ожидание',
            'charged':  'Завалка',
            'blowing':  'Продувка',
            'complete': 'Выпуск',
        }.get(s['state'], s['state'])

        lines = [
            state_label,
            f"Металл: {s['metalMass']:.0f} т",
            f"Шлак:   {s['slagMass']:.0f} т",
            f"Темп.:  {s['temperature']:.0f} °C",
        ]
        if s['blastFlow']:
            lines.append(f"Расход: {s['blastFlow']:.0f} м³/мин")
        if abs(self._tilt) > 1:
            lines.append(f"Наклон: {self._tilt:.0f}°")

        p = QPainter(self)
        p.setFont(QFont("Arial", 9))
        p.setPen(QColor(200, 220, 255, 220))
        x, y = 10, 14
        for ln in lines:
            p.drawText(x, y, ln)
            y += 16
        p.end()

    # ------------------------------------------------------------------
    # Mouse / wheel interaction
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        self._last_mouse = event.pos()

    def mouseReleaseEvent(self, event):
        self._last_mouse = None

    def mouseMoveEvent(self, event):
        if self._last_mouse is not None:
            dx = event.x() - self._last_mouse.x()
            dy = event.y() - self._last_mouse.y()
            self._az += dx * 0.5
            self._el += dy * 0.35
            self._el = max(-88.0, min(88.0, self._el))
            self._last_mouse = event.pos()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120.0
        self._dist = max(2.5, min(16.0, self._dist - delta * 0.45))


# ---------------------------------------------------------------------------
# Public wrapper widget (adds title label above GL canvas)
# ---------------------------------------------------------------------------

class ConverterGLPanel(QWidget):
    """Container: dark title + QOpenGLWidget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("3D Конвертер  (ЛКМ — вращение, колесо — масштаб)")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "background:#12101a; color:#8fb8d8; "
            "font:bold 10px 'Arial'; padding:4px;"
        )
        layout.addWidget(title)

        self._gl = ConverterGLWidget()
        layout.addWidget(self._gl, stretch=1)

    def update_state(self, state: dict):
        self._gl.update_state(state)
