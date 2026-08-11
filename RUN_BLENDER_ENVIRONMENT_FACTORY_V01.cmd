@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\blender_environment_factory\run_blender_environment_factory_v01.ps1" %*
set "FACTORY_EXIT=%ERRORLEVEL%"
endlocal & exit /b %FACTORY_EXIT%
