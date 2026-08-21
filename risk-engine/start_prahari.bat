@echo off
title PRAHARI Web Server
cd /d "%~dp0"
echo Starting PRAHARI Development Server...
cmd /c "npm run dev"
pause
