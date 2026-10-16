@echo off
rem Murdoku test build: serves the game on http://127.0.0.1:4173/ and opens it.
rem Close this window to stop.
cd /d "%~dp0site"
echo Murdoku test build: http://127.0.0.1:4173/  (close this window to stop)
start "" cmd /c "timeout /t 2 /nobreak >nul & start "" http://127.0.0.1:4173/"
py -3 -m http.server 4173 --bind 127.0.0.1 2>nul || python -m http.server 4173 --bind 127.0.0.1
echo.
echo Python was not found. Install it from https://www.python.org/downloads/ and run this file again.
pause
