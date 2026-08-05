@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_blender_heart_cycle.ps1" -RenderAnimation -AnimationResolution 360 -SampleStep 2
if errorlevel 1 pause
endlocal
