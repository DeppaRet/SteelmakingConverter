"""
Qt / QtWebEngine bootstrap — must run before PyQt5 and QtWebEngine imports.

Fixes on Windows:
  - "DLL load failed" when PyQt5 and PyQtWebEngine sit in different site-packages.
  - Chromium ICU crash when WebEngine DLLs live under a non-ASCII user profile path.

Prefer a bundled copy under ``<repo>/vendor/pyqt`` (ASCII path, single Qt build).
Install once::

    pip install PyQt5 PyQtWebEngine PyQtWebEngine-Qt5 -r requirements-3d.txt \\
        --target vendor/pyqt
"""

from __future__ import annotations

import os
import site
import sys

_bootstrapped = False


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _vendor_pyqt_site() -> str | None:
    """Project-local PyQt5 + WebEngine (recommended on Windows)."""
    vendor = os.path.join(_repo_root(), "vendor", "pyqt")
    if os.path.isfile(os.path.join(vendor, "PyQt5", "__init__.py")):
        return vendor
    return None


def bootstrap_qt() -> None:
    """Register Qt DLL directories and Chromium flags (idempotent)."""
    global _bootstrapped
    if _bootstrapped:
        return
    _bootstrapped = True

    vendor = _vendor_pyqt_site()
    if vendor and vendor not in sys.path:
        sys.path.insert(0, vendor)

    if sys.platform == "win32":
        _bootstrap_windows_dll_paths(vendor)

    flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    defaults = ["--no-sandbox"]
    for f in defaults:
        if f not in flags:
            flags = (flags + " " + f).strip()
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = flags


def _bootstrap_windows_dll_paths(vendor_site: str | None) -> None:
    if not hasattr(os, "add_dll_directory"):
        return

    seen: set[str] = set()

    def _add_bin(bin_dir: str) -> None:
        if not os.path.isdir(bin_dir) or bin_dir in seen:
            return
        seen.add(bin_dir)
        try:
            os.add_dll_directory(bin_dir)
        except OSError:
            pass
        path = os.environ.get("PATH", "")
        if bin_dir not in path.split(os.pathsep):
            os.environ["PATH"] = bin_dir + os.pathsep + path

    if vendor_site:
        qt5 = os.path.join(vendor_site, "PyQt5", "Qt5")
        _add_bin(os.path.join(qt5, "bin"))
        proc = os.path.join(qt5, "bin", "QtWebEngineProcess.exe")
        if os.path.isfile(proc):
            os.environ["QTWEBENGINEPROCESS_PATH"] = proc
        return

    candidates: list[str] = []
    try:
        candidates.append(site.getusersitepackages())
    except Exception:
        pass
    try:
        candidates.extend(site.getsitepackages())
    except Exception:
        pass

    for sp in candidates:
        if not sp:
            continue
        for pkg in ("PyQt5", "PyQtWebEngine", "PyQtWebEngine-Qt5"):
            _add_bin(os.path.join(sp, pkg, "Qt5", "bin"))
