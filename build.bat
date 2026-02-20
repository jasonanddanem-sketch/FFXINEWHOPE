@echo off
echo ============================================
echo   Building New Hope Launcher
echo ============================================

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found on PATH
    pause
    exit /b 1
)

pip install pyinstaller >nul 2>&1

echo Building .exe ...
pyinstaller --onefile --noconsole --name "NewHope Launcher" --icon=icon.ico launcher.py

echo.
if exist "dist\NewHope Launcher.exe" (
    echo SUCCESS: dist\NewHope Launcher.exe
    echo.
    echo Remember to place xiloader.exe next to the launcher .exe
) else (
    echo BUILD FAILED
)
echo.
pause
