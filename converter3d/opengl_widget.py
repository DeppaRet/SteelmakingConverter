"""
converter3d/opengl_widget.py
True interactive 3D BOF converter via QOpenGLWidget + PyOpenGL.

Features:
  - Left-drag  : orbit camera (azimuth + elevation)
  - Scroll     : zoom
  - Animated states: idle / charged / blowing / complete (tapping)
  - Tapping animation: converter tilts ~130°, molten metal pours out
  - Sparks, smoke, and pour particles
  - Industrial workshop environment: hall, support frame, ladle car, crane
"""

import math
import random

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QOpenGLWidget, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QSurfaceFormat

try:
    from OpenGL.GL import (
        glBegin, glEnd, glVertex3f, glNormal3f, glColor4f,
        glClearColor, glEnable, glDisable, glClear, glLoadIdentity,
        glPushMatrix, glPopMatrix, glTranslatef, glRotatef,
        glBlendFunc, glPointSize, glLineWidth, glLightf,
        glMaterialfv, glMateriali, glLightfv, glColorMaterial, glShadeModel,
        glViewport, glMatrixMode,
        GL_DEPTH_TEST, GL_BLEND, GL_LIGHTING,
        GL_LIGHT0, GL_LIGHT1, GL_LIGHT2, GL_LIGHT3,
        GL_COLOR_MATERIAL, GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE,
        GL_SPECULAR, GL_SHININESS, GL_SMOOTH, GL_NORMALIZE,
        GL_POSITION, GL_DIFFUSE, GL_AMBIENT,
        GL_LINEAR_ATTENUATION, GL_CONSTANT_ATTENUATION,
        GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
        GL_PROJECTION, GL_MODELVIEW,
        GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN, GL_POINTS, GL_LINES,
        GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
    )
    from OpenGL.GLU import (
        gluPerspective, gluLookAt, gluNewQuadric,
        gluCylinder, gluDisk, gluDeleteQuadric,
    )
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


def _draw_box(cx, cy, cz, wx, wy, wz):
    """Draw an axis-aligned solid box centered at (cx, cy, cz)."""
    hx, hy, hz = wx * 0.5, wy * 0.5, wz * 0.5
    x0, x1 = cx - hx, cx + hx
    y0, y1 = cy - hy, cy + hy
    z0, z1 = cz - hz, cz + hz
    faces = [
        ((0,  1, 0), [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]),
        ((0, -1, 0), [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)]),
        ((0,  0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
        ((0,  0,-1), [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)]),
        ((1,  0, 0), [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)]),
        ((-1, 0, 0), [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]),
    ]
    for normal, verts in faces:
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(*normal)
        for v in verts:
            glVertex3f(*v)
        glEnd()


def _draw_torus_ring(R, r_t, pos_y, seg_maj=40, seg_min=10):
    """Draw a horizontal torus ring centered at y=pos_y."""
    for i in range(seg_maj):
        a0 = i / seg_maj * 2 * math.pi
        a1 = (i + 1) / seg_maj * 2 * math.pi
        glBegin(GL_TRIANGLE_STRIP)
        for j in range(seg_min + 1):
            b = j / seg_min * 2 * math.pi
            for a in (a0, a1):
                x = (R + r_t * math.cos(b)) * math.cos(a)
                z = (R + r_t * math.cos(b)) * math.sin(a)
                y = pos_y + r_t * math.sin(b)
                glNormal3f(math.cos(b) * math.cos(a),
                           math.sin(b),
                           math.cos(b) * math.sin(a))
                glVertex3f(x, y, z)
        glEnd()


def _temp_color(t):
    """Return (R, G, B) for molten metal at temperature t °C."""
    f = max(0.0, min(1.0, (t - 1300) / 400.0))
    return (0.95 + 0.05 * f, 0.25 + 0.45 * f, 0.02)


# ---------------------------------------------------------------------------
# BOF vessel profiles  (r, y)
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

TRUNNION_Y   = 1.20
INNER_BODY_R = 0.75
INNER_NECK_R = 0.26
TOP_Y        = 2.44
BOT_Y        = 0.02
METAL_H_SCALE = 2.30
SLAG_H_SCALE  = 0.45


# ---------------------------------------------------------------------------
# Main GL widget
# ---------------------------------------------------------------------------

class ConverterGLWidget(QOpenGLWidget):
    """Interactive 3D BOF converter with industrial workshop environment.

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
        fmt.setSamples(4)
        fmt.setDepthBufferSize(24)
        QSurfaceFormat.setDefaultFormat(fmt)
        super().__init__(parent)

        self._az   = -30.0
        self._el   =  22.0
        self._dist =   7.5
        self._last_mouse = None

        self._s = {
            'state':       'idle',
            'metalLevel':  0.0,
            'slagLevel':   0.0,
            'temperature': 1400,
            'blastFlow':   0,
            'metalMass':   0,
            'slagMass':    0,
        }
        self._anim        = 0.0
        self._tilt        = 0.0
        self._tilt_target = 0.0
        self._lance_y     = 4.8
        self._lance_tgt   = 4.8
        self._sparks: list = []
        self._smoke:  list = []
        self._pour:   list = []

        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(33)

    # ------------------------------------------------------------------
    def update_state(self, state: dict):
        self._s.update(state)
        st = self._s['state']
        mh = self._s['metalLevel'] * METAL_H_SCALE

        if st == 'complete':
            self._tilt_target = 130.0
            self._lance_tgt   = 4.8
        elif st == 'blowing':
            self._tilt_target = 0.0
            self._lance_tgt   = BOT_Y + mh + 2.49
        else:
            self._tilt_target = 0.0
            self._lance_tgt   = 4.8

    # ------------------------------------------------------------------
    def _tick(self):
        self._anim += 0.033
        dt = 0.033

        self._tilt    += (self._tilt_target - self._tilt)    * 0.025
        self._lance_y += (self._lance_tgt   - self._lance_y) * 0.04

        blowing  = (self._s['state'] == 'blowing')
        _ml, _   = self._effective_levels()
        tapping  = (self._s['state'] == 'complete'
                    and self._tilt > 35.0 and _ml > 0.01)

        lance_tip_y = self._lance_y - 2.24

        # --- sparks during blow ---
        if blowing and len(self._sparks) < 140:
            for _ in range(5):
                spd = 0.022 + random.random() * 0.055
                ang = random.random() * math.pi * 2
                el  = (random.random() - 0.15) * math.pi * 0.65
                self._sparks.append([
                    0.0, lance_tip_y, 0.0,
                    math.cos(el) * math.cos(ang) * spd,
                    math.cos(el) * math.sin(ang) * spd * 0.4 + 0.012,
                    math.sin(el) * spd,
                    28 + int(random.random() * 30),
                    58,
                ])

        new_s = []
        for sp in self._sparks:
            sp[0] += sp[3]; sp[1] += sp[4]; sp[2] += sp[5]
            sp[4] -= 0.0025
            sp[6] -= 1
            if sp[6] > 0:
                new_s.append(sp)
        self._sparks = new_s if blowing else []

        # --- smoke puffs ---
        show_smoke = blowing or self._s['state'] == 'complete'
        if show_smoke and len(self._smoke) < 45:
            if random.random() < 0.40:
                sx = (random.random() - 0.5) * 0.30
                sz = (random.random() - 0.5) * 0.30
                self._smoke.append([
                    sx, TOP_Y + 0.15, sz,
                    (random.random() - 0.5) * 0.003,
                    0.007 + random.random() * 0.007,
                    (random.random() - 0.5) * 0.003,
                    55 + int(random.random() * 45),
                    100,
                ])

        new_sm = []
        for sm in self._smoke:
            sm[0] += sm[3]; sm[1] += sm[4]; sm[2] += sm[5]
            sm[3] += (random.random() - 0.5) * 0.0004
            sm[5] += (random.random() - 0.5) * 0.0004
            sm[6] -= 1
            if sm[6] > 0:
                new_sm.append(sm)
        self._smoke = new_sm if show_smoke else []

        # --- pour stream during tapping ---
        if tapping and len(self._pour) < 90:
            tr  = math.radians(self._tilt)
            dy_p = TOP_Y - TRUNNION_Y
            wx  = -dy_p * math.sin(tr)
            wy  =  TRUNNION_Y + dy_p * math.cos(tr)
            ox  = -math.sin(tr) * 0.018
            oy  =  math.cos(tr) * 0.018 - 0.008
            for _ in range(4):
                self._pour.append([
                    wx + (random.random() - 0.5) * 0.18,
                    wy + (random.random() - 0.5) * 0.08,
                    (random.random() - 0.5) * 0.18,
                    ox + (random.random() - 0.5) * 0.007,
                    oy + (random.random() - 0.5) * 0.006,
                    (random.random() - 0.5) * 0.007,
                    38 + int(random.random() * 32),
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
        glClearColor(0.05, 0.04, 0.09, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_LIGHT2)
        glEnable(GL_LIGHT3)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)

        # Main overhead directional (cool white)
        glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 12.0, 5.0, 0.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.05, 1.05, 1.15, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.10, 0.10, 0.14, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.75, 0.75, 0.75, 1.0])

        # Cool blue fill from left-back
        glLightfv(GL_LIGHT1, GL_POSITION, [-5.0, 5.0, -5.0, 0.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE,  [0.18, 0.20, 0.38, 1.0])
        glLightfv(GL_LIGHT1, GL_AMBIENT,  [0.0,  0.0,  0.0,  1.0])

        # Warm sodium-vapor industrial point light suspended from ceiling
        glLightfv(GL_LIGHT2, GL_POSITION, [0.0, 7.5, 1.5, 1.0])
        glLightfv(GL_LIGHT2, GL_DIFFUSE,  [0.55, 0.42, 0.14, 1.0])
        glLightfv(GL_LIGHT2, GL_AMBIENT,  [0.04, 0.03, 0.01, 1.0])
        glLightfv(GL_LIGHT2, GL_SPECULAR, [0.22, 0.17, 0.05, 1.0])
        glLightf(GL_LIGHT2, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(GL_LIGHT2, GL_LINEAR_ATTENUATION, 0.06)

        # Second warm lamp above the ladle side
        glLightfv(GL_LIGHT3, GL_POSITION, [-3.5, 6.5, 0.5, 1.0])
        glLightfv(GL_LIGHT3, GL_DIFFUSE,  [0.38, 0.30, 0.10, 1.0])
        glLightfv(GL_LIGHT3, GL_AMBIENT,  [0.0,  0.0,  0.0,  1.0])
        glLightf(GL_LIGHT3, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(GL_LIGHT3, GL_LINEAR_ATTENUATION, 0.10)

        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR,  [0.45, 0.45, 0.45, 1.0])
        glMateriali (GL_FRONT_AND_BACK, GL_SHININESS, 70)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, max(1, h))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(44.0, w / max(1, h), 0.1, 80.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        gluLookAt(0.0, 1.4, self._dist,
                  0.0, 1.4, 0.0,
                  0.0, 1.0, 0.0)
        glRotatef(self._el, 1.0, 0.0, 0.0)
        glRotatef(self._az, 0.0, 1.0, 0.0)

        self._draw_hall()
        self._draw_converter_frame()
        self._draw_ladle()

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

        # Lance and fume hood only when not tapping
        if self._s['state'] != 'complete':
            self._draw_lance()
            self._draw_fume_hood()

        self._draw_sparks()
        self._draw_smoke()
        self._draw_pour()
        self._draw_hud()

    # ------------------------------------------------------------------
    # Scene objects
    # ------------------------------------------------------------------

    def _draw_hall(self):
        """Industrial workshop: floor, grid lines, columns, trusses, crane."""
        # Large concrete floor
        glColor4f(0.14, 0.13, 0.16, 1.0)
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0, 1, 0)
        glVertex3f(0, -0.12, 0)
        for v in [(-11, -0.12, -11), (11, -0.12, -11),
                  (11, -0.12,  11), (-11, -0.12,  11), (-11, -0.12, -11)]:
            glVertex3f(*v)
        glEnd()

        # Floor grid lines
        glDisable(GL_LIGHTING)
        glLineWidth(1.0)
        glColor4f(0.21, 0.20, 0.27, 1.0)
        for i in range(-10, 11, 2):
            fi = float(i)
            glBegin(GL_LINES)
            glVertex3f(fi, -0.112, -11.0)
            glVertex3f(fi, -0.112,  11.0)
            glEnd()
            glBegin(GL_LINES)
            glVertex3f(-11.0, -0.112, fi)
            glVertex3f( 11.0, -0.112, fi)
            glEnd()
        glEnable(GL_LIGHTING)

        # I-beam columns at four corners
        glColor4f(0.30, 0.29, 0.38, 1.0)
        for cx, cz in [(-4.8, -4.2), (-4.8, 4.2), (4.8, -4.2), (4.8, 4.2)]:
            _draw_box(cx, 4.8, cz, 0.20, 9.6, 0.26)   # web
            _draw_box(cx, 4.8, cz, 0.34, 9.6, 0.07)   # flanges

        # Ceiling truss beams (three transverse + one longitudinal)
        glColor4f(0.26, 0.25, 0.34, 1.0)
        for z in [-4.2, 0.0, 4.2]:
            _draw_box(0, 9.55, z, 10.6, 0.20, 0.20)
        _draw_box(0, 9.55, 0, 0.20, 0.20, 10.0)

        # Overhead crane bridge girder (industrial yellow)
        glColor4f(0.75, 0.58, 0.06, 1.0)
        _draw_box(2.0, 8.80, 0, 0.36, 0.58, 10.5)

        # Crane end trucks
        glColor4f(0.62, 0.48, 0.05, 1.0)
        for z_end in (-4.8, 4.8):
            _draw_box(2.0, 9.06, z_end, 1.3, 0.24, 0.32)

        # Crane hook block
        glColor4f(0.38, 0.36, 0.46, 1.0)
        _draw_box(2.0, 6.8, 0, 0.22, 0.36, 0.22)
        # Wire rope
        glColor4f(0.32, 0.31, 0.40, 1.0)
        _draw_box(2.0, 7.8, 0, 0.05, 1.96, 0.05)

        # Suspended lamp housings (two lamps)
        glColor4f(0.22, 0.20, 0.28, 1.0)
        for lx in (0.0, -2.8):
            _draw_box(lx, 7.10, 0.5, 0.28, 0.22, 0.28)
            # Lamp shade (wide cone rim)
            glColor4f(0.38, 0.35, 0.22, 1.0)
            glPushMatrix()
            glTranslatef(lx, 6.98, 0.5)
            _draw_revolution([(0.22, 0.0), (0.36, -0.14)], segments=24)
            glPopMatrix()

        # Back wall
        glColor4f(0.10, 0.09, 0.12, 1.0)
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0, 0, 1)
        glVertex3f(0, 4.5, -10.0)
        for v in [(-11, -0.12, -10.0), (11, -0.12, -10.0),
                  (11, 10.0, -10.0), (-11, 10.0, -10.0), (-11, -0.12, -10.0)]:
            glVertex3f(*v)
        glEnd()

        # Left wall
        glColor4f(0.11, 0.10, 0.13, 1.0)
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(1, 0, 0)
        glVertex3f(-10.0, 4.5, 0)
        for v in [(-10.0, -0.12, -11), (-10.0, -0.12, 11),
                  (-10.0, 10.0, 11), (-10.0, 10.0, -11), (-10.0, -0.12, -11)]:
            glVertex3f(*v)
        glEnd()

    def _draw_converter_frame(self):
        """Converter support cradle: base slab, bearing columns, ring platform."""
        # Base platform slab
        glColor4f(0.18, 0.17, 0.23, 1.0)
        _draw_box(0, -0.13, 0, 5.0, 0.28, 3.6)

        # Circular ring platform directly under vessel
        glColor4f(0.16, 0.15, 0.21, 1.0)
        _draw_revolution([(1.62, -0.08), (1.62, 0.11)], segments=52)
        _draw_disc(1.62, -0.08, segments=52, up=False)
        _draw_disc(1.62,  0.11, segments=52, up=True)

        # Two main bearing support columns (one on each side of trunnion)
        glColor4f(0.33, 0.31, 0.43, 1.0)
        for side in (-1, 1):
            cx = side * 1.72

            # Column shaft
            glPushMatrix()
            glTranslatef(cx, 0, 0)
            _draw_cylinder_capped(0.115, 0.11, 3.42, segments=18)
            glPopMatrix()

            # Bearing housing (horizontal cylinder along the axle)
            glColor4f(0.40, 0.38, 0.50, 1.0)
            glPushMatrix()
            glTranslatef(cx, TRUNNION_Y, 0)
            glRotatef(90, 0, 0, 1)          # rotate Y-axis tube → X-axis
            _draw_cylinder_capped(0.215, -0.20, 0.20, segments=20)
            glPopMatrix()

            # Column top cap plate
            glColor4f(0.28, 0.27, 0.36, 1.0)
            _draw_box(cx, 3.43, 0, 0.34, 0.10, 0.34)

            glColor4f(0.33, 0.31, 0.43, 1.0)

        # Top cross-beam connecting the two columns
        glColor4f(0.36, 0.34, 0.46, 1.0)
        _draw_box(0, 3.50, 0, 3.65, 0.16, 0.22)

        # Diagonal cross-bracing (front and back pairs)
        glColor4f(0.28, 0.27, 0.36, 1.0)
        for z_off in (-0.55, 0.55):
            _draw_box(0, 1.75, z_off, 3.0, 0.08, 0.09)

        # Horizontal stiffener at mid-height
        _draw_box(0, 2.20, 0, 3.55, 0.07, 0.18)

    def _draw_ladle(self):
        """Steel ladle on a wheeled ladle car, positioned for tapping."""
        glPushMatrix()
        glTranslatef(-2.40, -0.12, 0.50)

        # Ladle car frame
        glColor4f(0.20, 0.18, 0.25, 1.0)
        _draw_box(0, 0.14, 0, 1.50, 0.30, 1.10)

        # Four wheels (box approximation)
        glColor4f(0.24, 0.23, 0.30, 1.0)
        for wx, wz in [(-0.48, -0.40), (0.48, -0.40),
                       (-0.48,  0.40), (0.48,  0.40)]:
            _draw_box(wx, 0.11, wz, 0.20, 0.22, 0.15)

        # Rail track sections (two rails under the car)
        glColor4f(0.35, 0.34, 0.42, 1.0)
        for rx in (-0.55, 0.55):
            _draw_box(rx, -0.01, 0, 0.07, 0.10, 2.0)

        # Ladle trunnion lifting bars
        glColor4f(0.38, 0.36, 0.47, 1.0)
        for tz in (-0.44, 0.44):
            _draw_box(0, 0.88, tz, 1.70, 0.07, 0.07)

        # --- Ladle vessel ---
        glPushMatrix()
        glTranslatef(0, 0.30, 0)

        # Outer shell (slightly truncated cone)
        ladle_outer = [
            (0.44, 0.00),
            (0.50, 0.07),
            (0.58, 0.55),
            (0.60, 0.76),
            (0.62, 0.84),
        ]
        glColor4f(0.30, 0.27, 0.36, 1.0)
        _draw_revolution(ladle_outer, segments=40)
        _draw_disc(0.44, 0.0, segments=40, up=False)

        # Rim ring
        glColor4f(0.38, 0.36, 0.48, 1.0)
        _draw_torus_ring(0.61, 0.032, 0.84, seg_maj=34, seg_min=8)

        # Reinforcement rings on shell
        glColor4f(0.34, 0.32, 0.43, 1.0)
        for ry in (0.22, 0.50, 0.72):
            _draw_torus_ring(0.58 + ry * 0.035, 0.022, ry, seg_maj=28, seg_min=6)

        # Inner refractory (dark brown, inside view)
        ladle_inner = [
            (0.37, 0.02),
            (0.43, 0.08),
            (0.50, 0.56),
            (0.52, 0.80),
        ]
        glColor4f(0.22, 0.13, 0.08, 1.0)
        _draw_revolution(ladle_inner, segments=36, inside=True)

        glPopMatrix()   # end ladle vessel
        glPopMatrix()   # end ladle group

    def _draw_fume_hood(self):
        """Fume extraction hood above the converter mouth."""
        # Hood funnel (widens going down to capture fumes)
        glColor4f(0.24, 0.22, 0.31, 1.0)
        hood_profile = [
            (0.22, 6.50),   # duct exits to ceiling
            (0.22, 3.10),   # duct bottom
            (0.38, 2.72),   # funnel flare
            (0.52, 2.52),   # funnel mouth (just above vessel top)
        ]
        _draw_revolution(hood_profile, segments=32)
        _draw_disc(0.22, 6.50, segments=32, up=True)

        # Reinforcement rings on duct
        glColor4f(0.30, 0.28, 0.38, 1.0)
        for ry in (3.3, 3.9, 4.5, 5.1, 5.7):
            _draw_torus_ring(0.245, 0.028, ry, seg_maj=24, seg_min=7)

        # Flange joint at duct base
        _draw_torus_ring(0.28, 0.040, 3.10, seg_maj=28, seg_min=8)

    def _effective_levels(self):
        ml = self._s['metalLevel']
        sl = self._s['slagLevel']
        if self._s['state'] == 'complete' and self._tilt > 5.0:
            pour_f = min(1.0, (self._tilt - 5.0) / 125.0)
            ml = ml * (1.0 - pour_f)
            sl = sl * (1.0 - pour_f * 0.85)
        return ml, sl

    def _draw_vessel_outer(self):
        glColor4f(0.32, 0.26, 0.40, 1.0)
        _draw_revolution(OUTER_PROFILE)
        _draw_disc(OUTER_PROFILE[0][0], OUTER_PROFILE[0][1], up=False)

        # Horizontal reinforcement rings welded on the shell body
        glColor4f(0.42, 0.38, 0.52, 1.0)
        for (ring_r, ring_y) in [(0.86, 0.55), (0.86, 1.10), (0.82, 1.68)]:
            _draw_torus_ring(ring_r, 0.028, ring_y, seg_maj=44, seg_min=8)

        # Bottom rim band
        glColor4f(0.38, 0.33, 0.48, 1.0)
        _draw_torus_ring(0.60, 0.030, 0.10, seg_maj=36, seg_min=7)

        # Top rim ring
        glColor4f(0.45, 0.42, 0.56, 1.0)
        _draw_revolution([
            (0.28, 2.42), (0.35, 2.44),
            (0.35, 2.54), (0.28, 2.54),
        ], segments=60)

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

        # Bright surface disc with slight shimmer
        shimmer = math.sin(self._anim * 14) * 0.002 if self._s['state'] == 'blowing' else 0
        glColor4f(min(1.0, r * 1.3), min(1.0, g * 1.45), b * 0.4, 1.0)
        _draw_disc(profile[-1][0], metal_y + shimmer, up=True)

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
        # Trunnion ring (torus)
        glColor4f(0.44, 0.46, 0.56, 1.0)
        _draw_torus_ring(0.91, 0.070, TRUNNION_Y, seg_maj=52, seg_min=14)

        # Axle pins on both sides
        glColor4f(0.48, 0.50, 0.60, 1.0)
        q = gluNewQuadric()
        for side in (-1, 1):
            glPushMatrix()
            glTranslatef(side * 1.13, TRUNNION_Y, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            gluCylinder(q, 0.058, 0.058, 0.30, 14, 1)
            glPopMatrix()
        gluDeleteQuadric(q)

    def _draw_lance(self):
        top_y  = self._lance_y + 0.06
        tip_y  = self._lance_y - 2.24

        # Main pipe
        glColor4f(0.55, 0.76, 0.88, 1.0)
        glPushMatrix()
        glTranslatef(0.0, top_y, 0.0)
        glRotatef(90.0, 1.0, 0.0, 0.0)
        q = gluNewQuadric()
        gluCylinder(q, 0.027, 0.025, 2.3, 14, 1)
        glPopMatrix()

        # Coolant manifold block at top
        glColor4f(0.50, 0.70, 0.84, 1.0)
        _draw_box(0, top_y + 0.11, 0, 0.14, 0.20, 0.14)

        # Three outer cooling pipes
        glColor4f(0.45, 0.65, 0.78, 1.0)
        for ang_deg in (0, 120, 240):
            a = math.radians(ang_deg)
            ox, oz = 0.042 * math.cos(a), 0.042 * math.sin(a)
            glPushMatrix()
            glTranslatef(ox, top_y, oz)
            glRotatef(90.0, 1.0, 0.0, 0.0)
            gluCylinder(q, 0.010, 0.010, 2.28, 8, 1)
            glPopMatrix()

        # Nozzle head (cone, narrows downward)
        glColor4f(0.68, 0.58, 0.36, 1.0)
        glPushMatrix()
        glTranslatef(0.0, tip_y, 0.0)
        glRotatef(90.0, 1.0, 0.0, 0.0)
        gluCylinder(q, 0.054, 0.0, 0.15, 16, 1)
        glPopMatrix()

        # Nozzle skirt / diffuser ring
        glColor4f(0.55, 0.46, 0.28, 1.0)
        _draw_torus_ring(0.038, 0.012, tip_y + 0.02, seg_maj=20, seg_min=6)

        # Lance guide clamp (visible in neck area)
        glColor4f(0.40, 0.56, 0.68, 1.0)
        guide_y = TOP_Y + 0.35
        _draw_revolution([(0.042, guide_y - 0.04), (0.042, guide_y + 0.04)], segments=20)
        _draw_torus_ring(0.048, 0.018, guide_y, seg_maj=20, seg_min=6)

        gluDeleteQuadric(q)

    def _draw_sparks(self):
        if not self._sparks:
            return
        glDisable(GL_LIGHTING)
        glPointSize(3.5)
        glBegin(GL_POINTS)
        for sp in self._sparks:
            f = sp[6] / max(1, sp[7])
            glColor4f(1.0, 0.55 * f + 0.45, 0.0, f)
            glVertex3f(sp[0], sp[1], sp[2])
        glEnd()
        glEnable(GL_LIGHTING)

    def _draw_smoke(self):
        if not self._smoke:
            return
        glDisable(GL_LIGHTING)
        glPointSize(7.0)
        glBegin(GL_POINTS)
        for sm in self._smoke:
            f = sm[6] / max(1, sm[7])
            alpha = f * 0.32
            glColor4f(0.55 + 0.10 * f, 0.52 + 0.08 * f, 0.50 + 0.05 * f, alpha)
            glVertex3f(sm[0], sm[1], sm[2])
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
        from PyQt5.QtGui import QPainter, QColor, QFont
        from PyQt5.QtCore import Qt

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
        self._dist = max(2.5, min(18.0, self._dist - delta * 0.50))


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
