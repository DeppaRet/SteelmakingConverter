"""
converter3d/opengl_widget.py
True interactive 3D BOF converter via QOpenGLWidget + PyOpenGL.

Features:
  - Left-drag  : orbit camera (azimuth + elevation)
  - Scroll     : zoom
  - Animated states: idle / charged / blowing / complete (tapping)
  - Tapping animation: converter tilts ~130°, molten metal pours out
  - Sparks, smoke, and pour particles
  - Realistic vessel: zoned refractory lining, cutaway, procedural textures
  - Scene modes: industrial hall / product (isolated) toggle
"""

import math
import random

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QOpenGLWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
)
from PyQt5.QtGui import QSurfaceFormat, QImage

from converter3d.visual_style import (
    CUTAWAY_PHI_START,
    CUTAWAY_PHI_END,
    LINING_ZONES,
    SAFETY_LAYER_RGB,
    SAFETY_LAYER_SCALE,
    SHELL_RGB,
    SHELL_RING_RGB,
    TAPHOLE_Y,
    TAPHOLE_SHELL_R,
    TAPHOLE_LEN,
    TAPHOLE_PIPE_R,
    TAPHOLE_OUTLET_Z,
    SCENE_HALL,
    SCENE_PRODUCT,
    PRODUCT_BG,
    HALL_BG,
    get_preset,
    set_ui_theme as vs_set_ui_theme,
    PRODUCT_DEFAULT_DIST,
    HALL_DEFAULT_DIST,
    TRUNNION_RGB,
    TRUNNION_Y,
    LADLE_X,
    LADLE_Y,
    LADLE_Z,
    REV_SEGMENTS,
    TORUS_SEG_MAJOR,
    TORUS_SEG_MINOR,
)

try:
    from OpenGL.GL import (
        glBegin, glEnd, glVertex3f, glNormal3f, glColor4f, glTexCoord2f,
        glClearColor, glEnable, glDisable, glClear, glLoadIdentity,
        glPushMatrix, glPopMatrix, glTranslatef, glRotatef,
        glBlendFunc, glPointSize, glLineWidth, glLightf,
        glMaterialfv, glMateriali, glLightfv, glColorMaterial, glShadeModel,
        glViewport, glMatrixMode, glGenTextures, glBindTexture, glTexImage2D,
        glTexParameteri, glTexEnvf,
        GL_DEPTH_TEST, GL_BLEND, GL_LIGHTING,
        GL_LIGHT0, GL_LIGHT1, GL_LIGHT2, GL_LIGHT3,
        GL_COLOR_MATERIAL, GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE,
        GL_SPECULAR, GL_SHININESS, GL_SMOOTH, GL_NORMALIZE,
        GL_POSITION, GL_DIFFUSE, GL_AMBIENT,
        GL_LINEAR_ATTENUATION, GL_CONSTANT_ATTENUATION,
        GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
        GL_PROJECTION, GL_MODELVIEW,
        GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN, GL_QUADS, GL_POINTS, GL_LINES,
        GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
        GL_TEXTURE_2D, GL_RGB, GL_UNSIGNED_BYTE,
        GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_REPEAT,
        GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_LINEAR,
        GL_MODULATE, GL_TEXTURE_ENV_MODE, GL_CLAMP_TO_EDGE,
    )
    from OpenGL.GLU import (
        gluPerspective, gluLookAt, gluNewQuadric,
        gluCylinder, gluDisk, gluDeleteQuadric,
    )
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Procedural textures (QImage → GL)
# ---------------------------------------------------------------------------

def _make_brick_texture(size=256):
    """Brick diffuse map with mortar grid and colour noise."""
    img = QImage(size, size, QImage.Format_RGB32)
    rows, cols = 8, 4
    brick_h = size // rows
    brick_w = size // cols
    mortar = 5
    for y in range(size):
        for x in range(size):
            row = y // brick_h
            col = (x + (row % 2) * (brick_w // 2)) // brick_w
            lx = x % brick_w
            ly = y % brick_h
            if lx < mortar or ly < mortar or lx >= brick_w - mortar or ly >= brick_h - mortar:
                r, g, b = 72, 68, 62
            else:
                n = ((x * 13 + y * 7 + row * 31) % 17) - 8
                r = min(255, max(0, 168 + n))
                g = min(255, max(0, 118 + n // 2))
                b = min(255, max(0, 72 + n // 3))
            img.setPixel(x, y, (255 << 24) | (r << 16) | (g << 8) | b)
    return img


def _make_metal_texture(size=128):
    """Subtle cast-steel grain for outer shell."""
    img = QImage(size, size, QImage.Format_RGB32)
    for y in range(size):
        for x in range(size):
            n = ((x * 17 + y * 23) % 11) - 5
            v = min(255, max(0, 108 + n))
            img.setPixel(x, y, (255 << 24) | (v << 16) | (v << 8) | (v + 2))
    return img


def _upload_texture_2d(qimg, repeat=True):
    """Upload QImage as GL_RGB texture (must be 3 bytes/pixel for glTexImage2D)."""
    img = qimg.convertToFormat(QImage.Format_RGB888)
    w, h = img.width(), img.height()
    nbytes = img.sizeInBytes() if hasattr(img, 'sizeInBytes') else w * h * 3
    ptr = img.bits()
    ptr.setsize(nbytes)

    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    wrap = GL_REPEAT if repeat else GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap)
    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_RGB,
        w, h, 0,
        GL_RGB, GL_UNSIGNED_BYTE, ptr,
    )
    glBindTexture(GL_TEXTURE_2D, 0)
    return tex


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _draw_revolution(
    profile, segments=44, inside=False,
    phi_start=None, phi_end=None, tex_u_scale=1.0, tex_v_scale=1.0,
):
    """Surface of revolution; optional angular range for cutaway."""
    if phi_start is None:
        phi_start = 0.0
    if phi_end is None:
        phi_end = 2.0 * math.pi
    y_min = profile[0][1]
    y_max = profile[-1][1]
    y_span = max(y_max - y_min, 1e-6)

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
            a = phi_start + (phi_end - phi_start) * j / segments
            ct, st = math.cos(a), math.sin(a)
            u = (a - phi_start) / (phi_end - phi_start) * tex_u_scale
            glNormal3f(n_r * ct, n_y, n_r * st)
            glTexCoord2f(u, (y0 - y_min) / y_span * tex_v_scale)
            glVertex3f(r0 * ct, y0, r0 * st)
            glTexCoord2f(u, (y1 - y_min) / y_span * tex_v_scale)
            glVertex3f(r1 * ct, y1, r1 * st)
        glEnd()


def _draw_cut_cap(profile, phi, inside=False):
    """Seal the cut face at angle phi along the profile."""
    nx = math.cos(phi) * (-1 if inside else 1)
    nz = math.sin(phi) * (-1 if inside else 1)
    glBegin(GL_QUADS)
    for i in range(len(profile) - 1):
        r0, y0 = profile[i]
        r1, y1 = profile[i + 1]
        glNormal3f(nx, 0.0, nz)
        glTexCoord2f(0.0, y0)
        glVertex3f(r0 * math.cos(phi), y0, r0 * math.sin(phi))
        glTexCoord2f(1.0, y0)
        glVertex3f(r1 * math.cos(phi), y1, r1 * math.sin(phi))
        glNormal3f(nx, 0.0, nz)
        glTexCoord2f(1.0, y1)
        glVertex3f(r1 * math.cos(phi), y1, r1 * math.sin(phi))
        glTexCoord2f(0.0, y1)
        glVertex3f(r0 * math.cos(phi), y0, r0 * math.sin(phi))
    glEnd()


def _draw_disc(radius, y, segments=44, up=True, phi_start=None, phi_end=None):
    """Horizontal disc; optional partial arc."""
    if phi_start is None:
        phi_start = 0.0
    if phi_end is None:
        phi_end = 2.0 * math.pi
    glBegin(GL_TRIANGLE_FAN)
    glNormal3f(0.0, 1.0 if up else -1.0, 0.0)
    glTexCoord2f(0.5, 0.5)
    glVertex3f(0.0, y, 0.0)
    nseg = max(3, int(segments * (phi_end - phi_start) / (2 * math.pi)))
    for i in range(nseg + 1):
        a = phi_start + (phi_end - phi_start) * i / nseg
        glTexCoord2f(0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a))
        glVertex3f(radius * math.cos(a), y, radius * math.sin(a))
    glEnd()


def _draw_cylinder_capped(r, y_bot, y_top, segments=36, phi_start=None, phi_end=None):
    _draw_revolution(
        [(r, y_bot), (r, y_top)], segments,
        phi_start=phi_start, phi_end=phi_end,
    )
    _draw_disc(r, y_bot, segments, up=False, phi_start=phi_start, phi_end=phi_end)
    _draw_disc(r, y_top, segments, up=True, phi_start=phi_start, phi_end=phi_end)


def _draw_box(cx, cy, cz, wx, wy, wz):
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


def _draw_torus_ring(R, r_t, pos_y, seg_maj=40, seg_min=10, phi_start=None, phi_end=None):
    if phi_start is None:
        phi_start = 0.0
    if phi_end is None:
        phi_end = 2.0 * math.pi
    nmaj = max(3, int(seg_maj * (phi_end - phi_start) / (2 * math.pi)))
    for i in range(nmaj):
        a0 = phi_start + (phi_end - phi_start) * i / nmaj
        a1 = phi_start + (phi_end - phi_start) * (i + 1) / nmaj
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


def _profile_y_band(profile, y_min, y_max):
    """Extract profile segment for y in [y_min, y_max] with interpolated ends."""
    if y_max <= y_min:
        return []

    def interp(r0, y0, r1, y1, y):
        if abs(y1 - y0) < 1e-9:
            return r0, y
        t = (y - y0) / (y1 - y0)
        return r0 + t * (r1 - r0), y

    pts = []
    for i in range(len(profile) - 1):
        r0, y0 = profile[i]
        r1, y1 = profile[i + 1]
        lo, hi = min(y0, y1), max(y0, y1)
        if hi < y_min or lo > y_max:
            continue
        seg_lo = max(y_min, lo)
        seg_hi = min(y_max, hi)
        p_lo = interp(r0, y0, r1, y1, seg_lo)
        p_hi = interp(r0, y0, r1, y1, seg_hi)
        if not pts or abs(pts[-1][1] - p_lo[1]) > 1e-5 or abs(pts[-1][0] - p_lo[0]) > 1e-5:
            pts.append(p_lo)
        if abs(p_hi[1] - p_lo[1]) > 1e-5 or abs(p_hi[0] - p_lo[0]) > 1e-5:
            pts.append(p_hi)
    if len(pts) < 2:
        return []
    return pts


def _scaled_profile(profile, scale):
    return [(r * scale, y) for r, y in profile]


def _temp_color(t):
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

TOP_Y        = 2.44
BOT_Y        = 0.02
METAL_H_SCALE = 2.30
METAL_LEVEL_VISUAL = 1.28
METAL_H_BOOST = 1.15
SLAG_H_SCALE  = 0.45
LANCE_SUBMERGE = 0.38

_PHI0 = CUTAWAY_PHI_START
_PHI1 = CUTAWAY_PHI_END


# ---------------------------------------------------------------------------
# Main GL widget
# ---------------------------------------------------------------------------

class ConverterGLWidget(QOpenGLWidget):
    """Interactive 3D BOF converter with industrial workshop environment."""

    def __init__(self, parent=None):
        fmt = QSurfaceFormat()
        fmt.setSamples(4)
        fmt.setDepthBufferSize(24)
        QSurfaceFormat.setDefaultFormat(fmt)
        super().__init__(parent)

        self._az   = -30.0
        self._el   =  22.0
        self._dist = HALL_DEFAULT_DIST
        self._last_mouse = None
        self._scene_mode = SCENE_HALL
        self._clear_bg = HALL_BG
        self._tex_brick = None
        self._tex_metal = None
        self._textures_ready = False
        self._textures_ok = False
        self._use_textures = False
        self._ladle_fill = 0.0

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

    def set_scene_mode(self, mode: str):
        if mode not in (SCENE_HALL, SCENE_PRODUCT):
            return
        self._scene_mode = mode
        if mode == SCENE_PRODUCT:
            self._dist = min(self._dist, PRODUCT_DEFAULT_DIST)
        self._apply_clear_color()
        self.update()

    def toggle_scene_mode(self):
        self.set_scene_mode(
            SCENE_PRODUCT if self._scene_mode == SCENE_HALL else SCENE_HALL
        )

    def _world_point_tilted(self, lx, ly, lz=0.0):
        """Vessel-local point → world coords after X-tilt (pour toward +Z)."""
        tr = math.radians(self._tilt)
        py = ly - TRUNNION_Y
        c, s = math.cos(tr), math.sin(tr)
        wy = TRUNNION_Y + py * c - lz * s
        wz = py * s + lz * c
        return lx, wy, wz

    def _taphole_outlet_world(self):
        """Outer end of taphole spout (-Z side)."""
        return self._world_point_tilted(0.0, TAPHOLE_Y, TAPHOLE_OUTLET_Z)

    def _apply_clear_color(self):
        preset = get_preset()
        self._clear_bg = (
            preset["product_bg"]
            if self._scene_mode == SCENE_PRODUCT
            else preset["hall_bg"]
        )
        if self.isValid():
            self.makeCurrent()
            glClearColor(*self._clear_bg)
            self.doneCurrent()

    def set_ui_theme(self, theme: str) -> None:
        vs_set_ui_theme(theme)
        self._apply_clear_color()
        self.update()

    # ------------------------------------------------------------------
    def update_state(self, state: dict):
        self._s.update(state)
        st = self._s['state']
        if st == 'complete':
            self._tilt_target = 130.0
            self._lance_tgt   = 4.8
        elif st == 'blowing':
            self._tilt_target = 0.0
            mh = self._metal_height_units(self._s['metalLevel'])
            metal_top = BOT_Y + mh
            sh = self._s['slagLevel'] * SLAG_H_SCALE
            bath_top = metal_top + sh if sh > 0.01 and mh > 0.03 else metal_top
            tip_y = max(BOT_Y + 0.40, bath_top - LANCE_SUBMERGE)
            self._lance_tgt = tip_y + 2.24
        else:
            self._tilt_target = 0.0
            self._lance_tgt   = 4.8

    # ------------------------------------------------------------------
    def _tick(self):
        self._anim += 0.033

        self._tilt    += (self._tilt_target - self._tilt)    * 0.025
        self._lance_y += (self._lance_tgt   - self._lance_y) * 0.04

        blowing  = (self._s['state'] == 'blowing')
        _ml, _   = self._effective_levels()
        tapping  = (self._s['state'] == 'complete'
                    and self._tilt > 35.0 and _ml > 0.01)

        lance_tip_y = self._lance_y - 2.24

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

        if tapping and len(self._pour) < 120:
            sx, sy, sz = self._taphole_outlet_world()
            dx = LADLE_X - sx
            dy = LADLE_Y - sy
            dz = LADLE_Z - sz
            dist = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
            spd = 0.042 + random.random() * 0.028
            for _ in range(6):
                self._pour.append([
                    sx + (random.random() - 0.5) * 0.06,
                    sy + (random.random() - 0.5) * 0.04,
                    sz + (random.random() - 0.5) * 0.06,
                    dx / dist * spd + (random.random() - 0.5) * 0.012,
                    dy / dist * spd * 0.55 + (random.random() - 0.5) * 0.010,
                    dz / dist * spd + (random.random() - 0.5) * 0.012,
                    42 + int(random.random() * 38),
                    80,
                ])
            self._ladle_fill = min(
                1.0,
                self._ladle_fill + 0.018 * (self._tilt / 130.0),
            )

        new_p = []
        for pp in self._pour:
            pp[0] += pp[3]
            pp[1] += pp[4]
            pp[2] += pp[5]
            pp[3] += (LADLE_X - pp[0]) * 0.0012
            pp[5] += (LADLE_Z - pp[2]) * 0.0012
            pp[4] -= 0.011
            pp[6] -= 1
            if pp[6] > 0 and pp[1] > 0.05:
                new_p.append(pp)
        self._pour = new_p if tapping else []
        if not tapping and self._s['state'] != 'complete':
            self._ladle_fill = 0.0

        self.update()

    # ------------------------------------------------------------------
    def _setup_textures(self):
        if self._textures_ready:
            return
        try:
            self._tex_brick = _upload_texture_2d(_make_brick_texture())
            self._tex_metal = _upload_texture_2d(_make_metal_texture())
            glTexEnvf(GL_TEXTURE_ENV_MODE, GL_MODULATE)
            self._textures_ok = True
        except Exception:
            self._tex_brick = None
            self._tex_metal = None
            self._textures_ok = False
        self._textures_ready = True

    def _bind_tex(self, tex_id):
        if not self._textures_ok or tex_id is None:
            return
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_id)

    def _unbind_tex(self):
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

    def _apply_hall_lights(self):
        hl = get_preset()["hall_lights"]
        glEnable(GL_LIGHT2)
        glEnable(GL_LIGHT3)
        glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 12.0, 5.0, 0.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, list(hl["L0_diffuse"]))
        glLightfv(GL_LIGHT0, GL_AMBIENT, list(hl["L0_ambient"]))
        glLightfv(GL_LIGHT1, GL_POSITION, [-5.0, 5.0, -5.0, 0.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, list(hl["L1_diffuse"]))
        glLightfv(GL_LIGHT2, GL_POSITION, [0.0, 7.5, 1.5, 1.0])
        glLightfv(GL_LIGHT2, GL_DIFFUSE, list(hl["L2_diffuse"]))
        glLightfv(GL_LIGHT3, GL_POSITION, [-3.5, 6.5, 0.5, 1.0])
        glLightfv(GL_LIGHT3, GL_DIFFUSE, list(hl["L3_diffuse"]))

    def _apply_product_lights(self):
        pl = get_preset()["product_lights"]
        glDisable(GL_LIGHT2)
        glDisable(GL_LIGHT3)
        glLightfv(GL_LIGHT0, GL_POSITION, [4.0, 8.0, 6.0, 0.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, list(pl["L0_diffuse"]))
        glLightfv(GL_LIGHT0, GL_AMBIENT, list(pl["L0_ambient"]))
        glLightfv(GL_LIGHT1, GL_POSITION, [-6.0, 3.0, -4.0, 0.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, list(pl["L1_diffuse"]))

    def initializeGL(self):
        glClearColor(*self._clear_bg)
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
        self._apply_hall_lights()
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.75, 0.75, 0.75, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR,  [0.50, 0.50, 0.52, 1.0])
        glMateriali(GL_FRONT_AND_BACK, GL_SHININESS, 78)
        self._setup_textures()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, max(1, h))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(44.0, w / max(1, h), 0.1, 80.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        if self._scene_mode == SCENE_PRODUCT:
            self._apply_product_lights()
        else:
            self._apply_hall_lights()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        gluLookAt(0.0, 1.4, self._dist,
                  0.0, 1.4, 0.0,
                  0.0, 1.0, 0.0)
        glRotatef(self._el, 1.0, 0.0, 0.0)
        glRotatef(self._az, 0.0, 1.0, 0.0)

        if self._scene_mode == SCENE_HALL:
            self._draw_hall()
            self._draw_converter_frame()
            self._draw_ladle()
            self._draw_ladle_molten()

        glPushMatrix()
        glTranslatef(0.0, TRUNNION_Y, 0.0)
        glRotatef(self._tilt, 1.0, 0.0, 0.0)
        glTranslatef(0.0, -TRUNNION_Y, 0.0)

        self._draw_vessel_outer()
        self._draw_vessel_inner()
        self._draw_taphole()
        self._draw_metal()
        self._draw_slag()
        self._draw_trunnion()

        glPopMatrix()

        if self._s['state'] != 'complete':
            self._draw_lance()
            if self._scene_mode == SCENE_HALL:
                self._draw_fume_hood()

        self._draw_sparks()
        self._draw_smoke()
        self._draw_pour()
        self._draw_hud()

    # ------------------------------------------------------------------
    # Scene objects (hall mode)
    # ------------------------------------------------------------------

    def _draw_hall(self):
        glColor4f(0.14, 0.13, 0.16, 1.0)
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0, 1, 0)
        glVertex3f(0, -0.12, 0)
        for v in [(-11, -0.12, -11), (11, -0.12, -11),
                  (11, -0.12,  11), (-11, -0.12,  11), (-11, -0.12, -11)]:
            glVertex3f(*v)
        glEnd()

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

        glColor4f(0.30, 0.29, 0.38, 1.0)
        for cx, cz in [(-4.8, -4.2), (-4.8, 4.2), (4.8, -4.2), (4.8, 4.2)]:
            _draw_box(cx, 4.8, cz, 0.20, 9.6, 0.26)
            _draw_box(cx, 4.8, cz, 0.34, 9.6, 0.07)

        glColor4f(0.26, 0.25, 0.34, 1.0)
        for z in [-4.2, 0.0, 4.2]:
            _draw_box(0, 9.55, z, 10.6, 0.20, 0.20)
        _draw_box(0, 9.55, 0, 0.20, 0.20, 10.0)

        glColor4f(0.75, 0.58, 0.06, 1.0)
        _draw_box(2.0, 8.80, 0, 0.36, 0.58, 10.5)
        glColor4f(0.62, 0.48, 0.05, 1.0)
        for z_end in (-4.8, 4.8):
            _draw_box(2.0, 9.06, z_end, 1.3, 0.24, 0.32)

        glColor4f(0.38, 0.36, 0.46, 1.0)
        _draw_box(2.0, 6.8, 0, 0.22, 0.36, 0.22)
        glColor4f(0.32, 0.31, 0.40, 1.0)
        _draw_box(2.0, 7.8, 0, 0.05, 1.96, 0.05)

        glColor4f(0.22, 0.20, 0.28, 1.0)
        for lx in (0.0, -2.8):
            _draw_box(lx, 7.10, 0.5, 0.28, 0.22, 0.28)
            glColor4f(0.38, 0.35, 0.22, 1.0)
            glPushMatrix()
            glTranslatef(lx, 6.98, 0.5)
            _draw_revolution([(0.22, 0.0), (0.36, -0.14)], segments=24)
            glPopMatrix()

        glColor4f(0.10, 0.09, 0.12, 1.0)
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0, 0, 1)
        glVertex3f(0, 4.5, -10.0)
        for v in [(-11, -0.12, -10.0), (11, -0.12, -10.0),
                  (11, 10.0, -10.0), (-11, 10.0, -10.0), (-11, -0.12, -10.0)]:
            glVertex3f(*v)
        glEnd()

        glColor4f(0.11, 0.10, 0.13, 1.0)
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(1, 0, 0)
        glVertex3f(-10.0, 4.5, 0)
        for v in [(-10.0, -0.12, -11), (-10.0, -0.12, 11),
                  (-10.0, 10.0, 11), (-10.0, 10.0, -11), (-10.0, -0.12, -11)]:
            glVertex3f(*v)
        glEnd()

    def _draw_converter_frame(self):
        glColor4f(0.18, 0.17, 0.23, 1.0)
        _draw_box(0, -0.13, 0, 5.0, 0.28, 3.6)
        glColor4f(0.16, 0.15, 0.21, 1.0)
        _draw_revolution([(1.62, -0.08), (1.62, 0.11)], segments=52)
        _draw_disc(1.62, -0.08, segments=52, up=False)
        _draw_disc(1.62,  0.11, segments=52, up=True)

        glColor4f(0.33, 0.31, 0.43, 1.0)
        for side in (-1, 1):
            cx = side * 1.72
            glPushMatrix()
            glTranslatef(cx, 0, 0)
            _draw_cylinder_capped(0.115, 0.11, 3.42, segments=18)
            glPopMatrix()
            glColor4f(0.40, 0.38, 0.50, 1.0)
            glPushMatrix()
            glTranslatef(cx, TRUNNION_Y, 0)
            glRotatef(90, 0, 0, 1)
            _draw_cylinder_capped(0.215, -0.20, 0.20, segments=20)
            glPopMatrix()
            glColor4f(0.28, 0.27, 0.36, 1.0)
            _draw_box(cx, 3.43, 0, 0.34, 0.10, 0.34)
            glColor4f(0.33, 0.31, 0.43, 1.0)

        glColor4f(0.36, 0.34, 0.46, 1.0)
        _draw_box(0, 3.50, 0, 3.65, 0.16, 0.22)
        glColor4f(0.28, 0.27, 0.36, 1.0)
        for z_off in (-0.55, 0.55):
            _draw_box(0, 1.75, z_off, 3.0, 0.08, 0.09)
        _draw_box(0, 2.20, 0, 3.55, 0.07, 0.18)

    def _draw_ladle(self):
        glPushMatrix()
        glTranslatef(LADLE_X, -0.12, LADLE_Z)
        glColor4f(0.20, 0.18, 0.25, 1.0)
        _draw_box(0, 0.14, 0, 1.50, 0.30, 1.10)
        glColor4f(0.24, 0.23, 0.30, 1.0)
        for wx, wz in [(-0.48, -0.40), (0.48, -0.40), (-0.48, 0.40), (0.48, 0.40)]:
            _draw_box(wx, 0.11, wz, 0.20, 0.22, 0.15)
        glColor4f(0.35, 0.34, 0.42, 1.0)
        for rx in (-0.55, 0.55):
            _draw_box(rx, -0.01, 0, 0.07, 0.10, 2.0)
        glColor4f(0.38, 0.36, 0.47, 1.0)
        for tz in (-0.44, 0.44):
            _draw_box(0, 0.88, tz, 1.70, 0.07, 0.07)

        glPushMatrix()
        glTranslatef(0, 0.30, 0)
        ladle_outer = [(0.44, 0.00), (0.50, 0.07), (0.58, 0.55), (0.60, 0.76), (0.62, 0.84)]
        glColor4f(0.30, 0.27, 0.36, 1.0)
        _draw_revolution(ladle_outer, segments=REV_SEGMENTS)
        _draw_disc(0.44, 0.0, segments=REV_SEGMENTS, up=False)
        glColor4f(0.38, 0.36, 0.48, 1.0)
        _draw_torus_ring(0.61, 0.032, 0.84, seg_maj=TORUS_SEG_MAJOR, seg_min=TORUS_SEG_MINOR)
        glColor4f(0.34, 0.32, 0.43, 1.0)
        for ry in (0.22, 0.50, 0.72):
            _draw_torus_ring(
                0.58 + ry * 0.035, 0.022, ry,
                seg_maj=TORUS_SEG_MAJOR, seg_min=TORUS_SEG_MINOR,
            )
        ladle_inner = [(0.37, 0.02), (0.43, 0.08), (0.50, 0.56), (0.52, 0.80)]
        glColor4f(0.22, 0.13, 0.08, 1.0)
        _draw_revolution(ladle_inner, segments=REV_SEGMENTS, inside=True)
        glPopMatrix()
        glPopMatrix()

    def _draw_ladle_molten(self):
        """Molten steel accumulating in the ladle during tapping."""
        if self._ladle_fill <= 0.02:
            return
        r, g, b = _temp_color(self._s['temperature'])
        fill_h = 0.08 + self._ladle_fill * 0.62
        glPushMatrix()
        glTranslatef(LADLE_X, -0.12, LADLE_Z)
        glTranslatef(0.0, 0.30, 0.0)
        glColor4f(r, g, b, 0.96)
        glDisable(GL_LIGHTING)
        _draw_revolution(
            [(0.14, 0.06), (0.46, fill_h)], segments=40,
        )
        glColor4f(min(1.0, r * 1.25), min(1.0, g * 1.35), b * 0.35, 0.9)
        _draw_disc(0.44, fill_h, segments=40, up=True)
        glEnable(GL_LIGHTING)
        glPopMatrix()

    def _draw_fume_hood(self):
        glColor4f(0.24, 0.22, 0.31, 1.0)
        hood_profile = [
            (0.22, 6.50), (0.22, 3.10), (0.38, 2.72), (0.52, 2.52),
        ]
        _draw_revolution(hood_profile, segments=32)
        _draw_disc(0.22, 6.50, segments=32, up=True)
        glColor4f(0.30, 0.28, 0.38, 1.0)
        for ry in (3.3, 3.9, 4.5, 5.1, 5.7):
            _draw_torus_ring(0.245, 0.028, ry, seg_maj=24, seg_min=7)
        _draw_torus_ring(0.28, 0.040, 3.10, seg_maj=28, seg_min=8)

    def _effective_levels(self):
        ml = self._s['metalLevel']
        sl = self._s['slagLevel']
        if self._s['state'] == 'complete' and self._tilt > 5.0:
            pour_f = min(1.0, (self._tilt - 5.0) / 125.0)
            ml = ml * (1.0 - pour_f)
            sl = sl * (1.0 - pour_f * 0.85)
        return ml, sl

    def _metal_height_units(self, metal_level: float) -> float:
        vis = min(1.0, metal_level * METAL_LEVEL_VISUAL + 0.06)
        return vis * METAL_H_SCALE * METAL_H_BOOST

    def _draw_vessel_outer(self):
        r, g, b = SHELL_RGB
        glColor4f(r * 1.05, g * 1.05, b * 1.08, 1.0)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.62, 0.62, 0.66, 1.0])
        glMateriali(GL_FRONT_AND_BACK, GL_SHININESS, 72)
        if self._use_textures:
            self._setup_textures()
            if self._textures_ok:
                self._bind_tex(self._tex_metal)
        _draw_revolution(
            OUTER_PROFILE, segments=REV_SEGMENTS,
            phi_start=_PHI0, phi_end=_PHI1,
        )
        _draw_cut_cap(OUTER_PROFILE, _PHI0)
        _draw_cut_cap(OUTER_PROFILE, _PHI1)
        if self._use_textures and self._textures_ok:
            self._unbind_tex()
        _draw_disc(
            OUTER_PROFILE[0][0], OUTER_PROFILE[0][1],
            segments=REV_SEGMENTS, up=False, phi_start=_PHI0, phi_end=_PHI1,
        )

        glColor4f(*SHELL_RING_RGB, 1.0)
        for (ring_r, ring_y) in [(0.86, 0.55), (0.86, 1.10), (0.82, 1.68)]:
            _draw_torus_ring(
                ring_r, 0.028, ring_y,
                seg_maj=TORUS_SEG_MAJOR, seg_min=TORUS_SEG_MINOR,
                phi_start=_PHI0, phi_end=_PHI1,
            )
        _draw_torus_ring(
            0.60, 0.030, 0.10,
            seg_maj=TORUS_SEG_MAJOR, seg_min=TORUS_SEG_MINOR,
            phi_start=_PHI0, phi_end=_PHI1,
        )
        rim = [(0.28, 2.42), (0.35, 2.44), (0.35, 2.54), (0.28, 2.54)]
        _draw_revolution(
            rim, segments=REV_SEGMENTS, phi_start=_PHI0, phi_end=_PHI1,
        )

    def _draw_vessel_inner(self):
        safety = _scaled_profile(INNER_PROFILE, SAFETY_LAYER_SCALE)
        sr, sg, sb = SAFETY_LAYER_RGB
        glColor4f(sr, sg, sb, 1.0)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.12, 0.12, 0.14, 1.0])
        glMateriali(GL_FRONT_AND_BACK, GL_SHININESS, 18)
        _draw_revolution(
            safety, inside=True, segments=REV_SEGMENTS,
            phi_start=_PHI0, phi_end=_PHI1,
        )
        _draw_cut_cap(safety, _PHI0, inside=True)
        _draw_cut_cap(safety, _PHI1, inside=True)

        for y_min, y_max, rgb, _hx in LINING_ZONES:
            band = _profile_y_band(INNER_PROFILE, y_min, y_max)
            if len(band) < 2:
                continue
            glColor4f(rgb[0] * 1.08, rgb[1] * 1.06, rgb[2] * 1.04, 1.0)
            _draw_revolution(
                band, inside=True, segments=REV_SEGMENTS,
                phi_start=_PHI0, phi_end=_PHI1,
            )

    def _draw_taphole(self):
        """Taphole on -Z side (forward pour toward +Z)."""
        cy = TAPHOLE_Y
        cz = TAPHOLE_SHELL_R
        glPushMatrix()
        glTranslatef(0.0, cy, -cz)
        glRotatef(90.0, 1.0, 0.0, 0.0)
        glColor4f(*SHELL_RGB, 1.0)
        q = gluNewQuadric()
        gluCylinder(q, TAPHOLE_PIPE_R, TAPHOLE_PIPE_R * 0.92, TAPHOLE_LEN, 24, 1)
        glColor4f(0.55, 0.28, 0.12, 1.0)
        gluDisk(q, TAPHOLE_PIPE_R * 0.85, 0.0, 12, 1)
        glPopMatrix()
        gluDeleteQuadric(q)

    def _draw_metal(self):
        ml, _ = self._effective_levels()
        if ml <= 0.0:
            return
        mh      = self._metal_height_units(ml)
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
        _draw_revolution(profile, segments=REV_SEGMENTS)
        _draw_disc(profile[0][0], BOT_Y, up=False)

        shimmer = math.sin(self._anim * 14) * 0.002 if self._s['state'] == 'blowing' else 0
        glColor4f(min(1.0, r * 1.3), min(1.0, g * 1.45), b * 0.4, 1.0)
        _draw_disc(profile[-1][0], metal_y + shimmer, up=True)

    def _draw_slag(self):
        ml, sl = self._effective_levels()
        if sl <= 0.0 or ml <= 0.0:
            return
        metal_y = BOT_Y + self._metal_height_units(ml)
        slag_y  = metal_y + sl * SLAG_H_SCALE
        ir = 0.74

        glColor4f(0.52, 0.40, 0.10, 0.90)
        _draw_revolution([(ir, metal_y), (ir, slag_y)])
        glColor4f(0.46, 0.35, 0.08, 0.85)
        _draw_disc(ir, slag_y, up=True)

    def _draw_trunnion(self):
        glColor4f(*TRUNNION_RGB, 1.0)
        _draw_torus_ring(0.91, 0.070, TRUNNION_Y, seg_maj=52, seg_min=14)
        q = gluNewQuadric()
        for side in (-1, 1):
            glPushMatrix()
            glTranslatef(side * 1.13, TRUNNION_Y, 0.0)
            glRotatef(90.0, 0.0, 0.0, 1.0)
            gluCylinder(q, 0.058, 0.058, 0.30, 14, 1)
            glPopMatrix()
        gluDeleteQuadric(q)

    def _draw_lance(self):
        top_y = self._lance_y + 0.06
        tip_y = self._lance_y - 2.24

        glColor4f(0.55, 0.76, 0.88, 1.0)
        glPushMatrix()
        glTranslatef(0.0, top_y, 0.0)
        glRotatef(90.0, 1.0, 0.0, 0.0)
        q = gluNewQuadric()
        gluCylinder(q, 0.027, 0.025, 2.3, 14, 1)
        glPopMatrix()

        glColor4f(0.50, 0.70, 0.84, 1.0)
        _draw_box(0, top_y + 0.11, 0, 0.14, 0.20, 0.14)

        glColor4f(0.45, 0.65, 0.78, 1.0)
        for ang_deg in (0, 120, 240):
            a = math.radians(ang_deg)
            ox, oz = 0.042 * math.cos(a), 0.042 * math.sin(a)
            glPushMatrix()
            glTranslatef(ox, top_y, oz)
            glRotatef(90.0, 1.0, 0.0, 0.0)
            gluCylinder(q, 0.010, 0.010, 2.28, 8, 1)
            glPopMatrix()

        glColor4f(0.68, 0.58, 0.36, 1.0)
        glPushMatrix()
        glTranslatef(0.0, tip_y, 0.0)
        glRotatef(90.0, 1.0, 0.0, 0.0)
        gluCylinder(q, 0.054, 0.0, 0.15, 16, 1)
        glPopMatrix()

        glColor4f(0.55, 0.46, 0.28, 1.0)
        _draw_torus_ring(0.038, 0.012, tip_y + 0.02, seg_maj=20, seg_min=6)

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
        if self._s['state'] != 'complete' or self._tilt < 20.0:
            return
        if not self._pour:
            return
        r, g, b = _temp_color(self._s['temperature'])
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)

        if self._pour:
            glPointSize(8.0)
            glBegin(GL_POINTS)
            for pp in self._pour:
                f = pp[6] / max(1, pp[7])
                glColor4f(
                    min(1.0, r * (0.85 + 0.15 * f)),
                    g * (0.35 + 0.65 * f),
                    b * 0.15,
                    0.88 * f,
                )
                glVertex3f(pp[0], pp[1], pp[2])
            glEnd()

        glEnable(GL_LIGHTING)

    def _draw_hud(self):
        from PyQt5.QtGui import QPainter, QColor, QFont

        s = self._s
        state_label = {
            'idle':     'Ожидание',
            'charged':  'Завалка',
            'blowing':  'Продувка',
            'complete': 'Выпуск',
        }.get(s['state'], s['state'])

        mode_label = 'Продукт' if self._scene_mode == SCENE_PRODUCT else 'Цех'
        lines = [
            state_label,
            f"Вид: {mode_label}",
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


class ConverterGLPanel(QWidget):
    """Container: title, scene toggle, QOpenGLWidget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._title = QLabel("3D конвертер")
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setToolTip("ЛКМ — вращение, колесо мыши — масштаб")
        layout.addWidget(self._title)

        bar = QHBoxLayout()
        bar.setContentsMargins(6, 2, 6, 2)
        self._mode_btn = QPushButton("Вид: Цех")
        self._mode_btn.clicked.connect(self._on_toggle_mode)
        bar.addWidget(self._mode_btn)
        bar.addStretch()
        layout.addLayout(bar)

        self._gl = ConverterGLWidget()
        layout.addWidget(self._gl, stretch=1)
        self._apply_chrome_theme()

    def _apply_chrome_theme(self):
        try:
            import app_theme
            from theme_settings import get_theme
            theme = get_theme()
            self._title.setStyleSheet(app_theme.converter_chrome_qss(theme))
            t = app_theme.tokens(theme)
            self._mode_btn.setStyleSheet(
                f"background:{t['chrome_bg']}; color:{t['chrome_text']}; "
                f"border:1px solid {t['input_border']}; padding:3px 10px; font:9px Arial;"
            )
        except ImportError:
            pass

    def set_ui_theme(self, theme: str) -> None:
        self._gl.set_ui_theme(theme)
        self._apply_chrome_theme()

    def _on_toggle_mode(self):
        self._gl.toggle_scene_mode()
        if self._gl._scene_mode == SCENE_PRODUCT:
            self._mode_btn.setText("Вид: Продукт")
        else:
            self._mode_btn.setText("Вид: Цех")

    def update_state(self, state: dict):
        self._gl.update_state(state)
