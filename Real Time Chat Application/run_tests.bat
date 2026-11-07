@echo off
cd /d "%~dp0"
title DjangoChat - Test Runner
echo Running DjangoChat test suite...
venv\Scripts\python.exe manage.py test
pause

