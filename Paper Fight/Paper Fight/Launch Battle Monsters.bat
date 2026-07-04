@echo off
setlocal
cd /d "%~dp0"

if exist "%~dp0.venv\Scripts\pythonw.exe" (
    "%~dp0.venv\Scripts\pythonw.exe" "%~dp0battle_gui.py"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0battle_gui.py"
) else (
    where pythonw >nul 2>nul
    if not errorlevel 1 (
        pythonw "%~dp0battle_gui.py"
    ) else (
        python "%~dp0battle_gui.py"
    )
)
