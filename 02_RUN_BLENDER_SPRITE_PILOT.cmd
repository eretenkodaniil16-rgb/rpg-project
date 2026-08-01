@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\blender_sprite_factory\run_blender_sprite_pilot.ps1"
if errorlevel 1 (
  echo.
  echo Blender sprite pilot failed. See the error above.
  pause
  exit /b 1
)
echo.
echo Blender sprite pilot completed.
pause
