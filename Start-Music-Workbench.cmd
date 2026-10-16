@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launch-next.ps1" -Interface create -Workspace outputs/workbench -Port 8920 %*
if errorlevel 1 pause
