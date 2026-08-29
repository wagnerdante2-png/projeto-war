@echo off
setlocal
cd /d "%~dp0"
title ULTIMECIA Research Runner
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 runner\research_runner.py
) else (
  python runner\research_runner.py
)
if errorlevel 1 (
  echo.
  echo Nao foi possivel iniciar o Research Runner. Verifique se Python 3 esta disponivel.
  pause
)
endlocal
