import sys
from cx_Freeze import setup, Executable

# Замените "ваш_скрипт.py" на имя вашего скрипта Python
executables = [Executable("main.py", base = "Win32GUI", icon="E:/repos/SteelmakingConverter/Pictures/steel_ico.ico")]

# Здесь можно указать другие параметры сборки
build_exe_options = {
    "include_files": ["dev.ini", "pictures"],
    "excludes": [],
}

setup(
    name="Converter",
    version="1.0",
    description="Описание вашего приложения",
    options={"build_exe": build_exe_options},
    executables=executables
)
