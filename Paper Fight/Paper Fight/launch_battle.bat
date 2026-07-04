@echo off
cd /d "%~dp0"
call ".venv\Scripts\activate.bat"
python battle_gui.py
