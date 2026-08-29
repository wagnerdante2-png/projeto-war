@echo off
setlocal
cd /d "%~dp0"
title ULTIMECIA War Room

echo ========================================
echo        ULTIMECIA WAR ROOM

echo ========================================
echo.
echo Abrindo em http://localhost:8080 ...
start "" "http://localhost:8080"

where py >nul 2>nul
if %errorlevel%==0 (
  py -m http.server 8080
  goto :end
)

where python >nul 2>nul
if %errorlevel%==0 (
  python -m http.server 8080
  goto :end
)

echo.
echo Python nao foi encontrado nesta maquina.
echo Voce ainda pode abrir o arquivo index.html diretamente no navegador.
echo.
pause

:end
endlocal
