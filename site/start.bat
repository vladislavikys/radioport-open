@echo off
cd /d "%~dp0"
start "" http://localhost:8077/index.html
py serve.py 8077
