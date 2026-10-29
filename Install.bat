@echo off
rem Radioport installer: double-click this file. Details: docs\SETUP.md
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
echo.
pause