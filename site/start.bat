@echo off
cd /d "%~dp0"
title Radioport: keep this window open while you listen
where py >nul 2>nul && (set PY=py) || (set PY=python)
rem open the browser once the server below is listening
start "" /b cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8077/"
%PY% serve.py 8077
