@echo off
rem Starts the Lyra world (Vira + the town) and opens it in your browser.
cd /d "%~dp0game"
echo Starting Lyra world at http://localhost:8123
echo Close this window to stop the server.
start "" http://localhost:8123
python serve.py 8123
pause
