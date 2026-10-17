@echo off
setlocal
if not exist "%~dp0Music Workbench.exe" powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build-launcher.ps1"
if exist "%~dp0Music Workbench.exe" start "" "%~dp0Music Workbench.exe" %*
