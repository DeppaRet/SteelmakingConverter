"""
Shared visual constants for BOF converter 3-D renderers.

Used by opengl_widget.py; mirror hex values in converter.html (search: sync visual_style).
"""

import math

# 90° wedge removed; 270° arc kept (opening toward default camera +X/+Z).
CUTAWAY_PHI_START = math.pi * 0.75
CUTAWAY_PHI_LENGTH = math.pi * 1.5
CUTAWAY_PHI_END = CUTAWAY_PHI_START + CUTAWAY_PHI_LENGTH

# Refractory zones by inner-wall height Y (model units).
# Each entry: (y_min, y_max, (r, g, b), hex_for_threejs)
LINING_ZONES = (
    (0.02, 0.35, (0.14, 0.16, 0.26), 0x242a42),
    (0.35, 0.95, (0.62, 0.14, 0.08), 0x9e2414),
    (0.95, 1.80, (0.78, 0.42, 0.12), 0xc86a1e),
    (1.80, 2.50, (0.88, 0.76, 0.18), 0xe0c030),
)

SAFETY_LAYER_RGB = (0.62, 0.68, 0.74)
SAFETY_LAYER_HEX = 0x9eacb8
SAFETY_LAYER_SCALE = 1.028

SHELL_RGB = (0.24, 0.25, 0.28)
SHELL_HEX = 0x3d4048
SHELL_RING_RGB = (0.32, 0.33, 0.36)
SHELL_RING_HEX = 0x52565e

TRUNNION_RGB = (0.42, 0.44, 0.48)
TRUNNION_HEX = 0x6b7078

# Trunnion axis (vessel local); sync converter.html TRUNNION_Y_JS
TRUNNION_Y = 1.20

# Taphole on +X side (local vessel coordinates)
TAPHOLE_Y = 1.02
TAPHOLE_SHELL_R = 0.83
TAPHOLE_LEN = 0.22
TAPHOLE_PIPE_R = 0.055

# Ladle in front of converter (+Z); pour target
LADLE_X = 0.0
LADLE_Y = 1.02
LADLE_Z = 2.15

# Taphole on -Z (tilt about X toward +Z)
TAPHOLE_OUTLET_Z = -(TAPHOLE_SHELL_R + TAPHOLE_LEN)

# Mesh quality
REV_SEGMENTS = 72
TORUS_SEG_MAJOR = 56
TORUS_SEG_MINOR = 12

# Scene modes
SCENE_HALL = "hall"
SCENE_PRODUCT = "product"

PRODUCT_BG = (0.0, 0.0, 0.0, 1.0)
HALL_BG = (0.05, 0.04, 0.09, 1.0)

PRODUCT_DEFAULT_DIST = 6.2
HALL_DEFAULT_DIST = 7.5

CURRENT_UI_THEME = "dark"

# sync visual_style — mirror in converter.html UI_THEMES
THEME_PRESETS = {
    "dark": {
        "hall_bg": HALL_BG,
        "product_bg": PRODUCT_BG,
        "shell_rgb": SHELL_RGB,
        "shell_ring_rgb": SHELL_RING_RGB,
        "trunnion_rgb": TRUNNION_RGB,
        "hall_lights": {
            "L0_diffuse": (1.05, 1.05, 1.15, 1.0),
            "L0_ambient": (0.10, 0.10, 0.14, 1.0),
            "L1_diffuse": (0.18, 0.20, 0.38, 1.0),
            "L2_diffuse": (0.55, 0.42, 0.14, 1.0),
            "L3_diffuse": (0.38, 0.30, 0.10, 1.0),
        },
        "product_lights": {
            "L0_diffuse": (1.15, 1.12, 1.08, 1.0),
            "L0_ambient": (0.22, 0.22, 0.24, 1.0),
            "L1_diffuse": (0.35, 0.38, 0.42, 1.0),
        },
        "html": {
            "hallBg": 0x0D0A17,
            "productBg": 0x000000,
            "hemiSky": 0xC4D0EC,
            "hemiGround": 0x221810,
            "hemiIntensity": 0.78,
            "ambient": 0x9098B0,
            "ambientIntensity": 0.42,
            "sunIntensity": 2.35,
            "fillColor": 0x506890,
            "fillIntensity": 1.05,
            "keyColor": 0xD8DCE8,
            "keyIntensity": 0.72,
            "lamp1Color": 0xFFA030,
            "lamp1Intensity": 4.2,
            "lamp2Color": 0xFF9020,
            "lamp2Intensity": 3.2,
            "concrete": 0x22202C,
            "steelDark": 0x3A3850,
            "steelMed": 0x48466A,
            "steelLight": 0x626078,
            "shell": 0x4A4E58,
            "wall": 0x0E0D16,
            "hudBg": "rgba(8,8,20,0.92)",
            "hudBorder": "rgba(0,200,240,0.55)",
            "hudText": "#00c8f0",
            "pageBg": "#06060f",
        },
    },
    "light": {
        "hall_bg": (0.91, 0.93, 0.96, 1.0),
        "product_bg": (0.85, 0.88, 0.92, 1.0),
        "shell_rgb": (0.52, 0.54, 0.58),
        "shell_ring_rgb": (0.62, 0.64, 0.68),
        "trunnion_rgb": (0.58, 0.60, 0.64),
        "hall_lights": {
            "L0_diffuse": (1.0, 1.0, 1.0, 1.0),
            "L0_ambient": (0.45, 0.48, 0.52, 1.0),
            "L1_diffuse": (0.55, 0.58, 0.62, 1.0),
            "L2_diffuse": (0.75, 0.65, 0.35, 1.0),
            "L3_diffuse": (0.65, 0.55, 0.30, 1.0),
        },
        "product_lights": {
            "L0_diffuse": (1.05, 1.05, 1.02, 1.0),
            "L0_ambient": (0.55, 0.58, 0.62, 1.0),
            "L1_diffuse": (0.50, 0.54, 0.58, 1.0),
        },
        "html": {
            "hallBg": 0xE8ECF4,
            "productBg": 0xD8DDE8,
            "hemiSky": 0xF0F4FC,
            "hemiGround": 0xC8B8A8,
            "hemiIntensity": 1.05,
            "ambient": 0xB8C0D0,
            "ambientIntensity": 0.55,
            "sunIntensity": 2.0,
            "fillColor": 0xA0B0C8,
            "fillIntensity": 0.85,
            "keyColor": 0xFFFFFF,
            "keyIntensity": 0.65,
            "lamp1Color": 0xFFD080,
            "lamp1Intensity": 2.2,
            "lamp2Color": 0xFFC060,
            "lamp2Intensity": 1.6,
            "concrete": 0xB8BCC8,
            "steelDark": 0x6A6E78,
            "steelMed": 0x7A7E88,
            "steelLight": 0x9098A8,
            "shell": 0x788090,
            "wall": 0xD0D8E4,
            "hudBg": "rgba(255,255,255,0.92)",
            "hudBorder": "rgba(0,120,168,0.55)",
            "hudText": "#0078a8",
            "pageBg": "#e8ecf4",
        },
    },
}


def normalize_ui_theme(name: str | None) -> str:
    return "light" if name and str(name).strip().lower() == "light" else "dark"


def get_preset(theme: str | None = None) -> dict:
    key = normalize_ui_theme(theme or CURRENT_UI_THEME)
    return THEME_PRESETS[key]


def set_ui_theme(name: str) -> str:
    """Switch global 3D/UI palette; returns normalized theme id."""
    global CURRENT_UI_THEME, HALL_BG, PRODUCT_BG
    global SHELL_RGB, SHELL_RING_RGB, TRUNNION_RGB
    key = normalize_ui_theme(name)
    CURRENT_UI_THEME = key
    p = THEME_PRESETS[key]
    HALL_BG = p["hall_bg"]
    PRODUCT_BG = p["product_bg"]
    SHELL_RGB = p["shell_rgb"]
    SHELL_RING_RGB = p["shell_ring_rgb"]
    TRUNNION_RGB = p["trunnion_rgb"]
    return key


def zone_color_for_y(y: float):
    """Return (r,g,b) for a given height, or last zone color."""
    for y_min, y_max, rgb, _hex in LINING_ZONES:
        if y_min <= y < y_max:
            return rgb
    return LINING_ZONES[-1][2]
