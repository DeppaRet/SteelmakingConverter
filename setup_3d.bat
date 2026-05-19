@echo off
setlocal
cd /d "%~dp0"
echo Installing PyQt5 + WebEngine into vendor\pyqt ...
python -m pip install -r requirements-3d.txt --target vendor\pyqt --upgrade
if errorlevel 1 (
    echo Install failed.
    exit /b 1
)
echo Done. Restart the application to use Three.js 3D view.
exit /b 0
