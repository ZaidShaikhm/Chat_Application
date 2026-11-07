@echo off
cd /d "%~dp0"
title DjangoChat - Real-Time Server
echo =======================================================
echo  DjangoChat Real-Time Server (MCA Academic Project)
echo =======================================================
echo Starting Daphne ASGI Server with WebSockets...
echo Open http://127.0.0.1:8000 in your browser when ready.
echo Press CTRL+C to stop the server.
echo =======================================================
echo.
venv\Scripts\python.exe manage.py runserver
pause

