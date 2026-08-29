@echo off
setlocal
cd /d "%~dp0"
title ULTIMECIA War Room

echo ========================================
echo        ULTIMECIA WAR ROOM
echo ========================================
echo.

echo Iniciando servidor local...

where powershell >nul 2>nul
if %errorlevel%==0 (
  start "ULTIMECIA War Room Server" powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0war-room-server.ps1" -Port 8080
  timeout /t 2 /nobreak >nul
  start "" "http://localhost:8080"
  goto :end
)

where py >nul 2>nul
if %errorlevel%==0 (
  start "ULTIMECIA War Room Server" cmd /k py -m http.server 8080
  timeout /t 2 /nobreak >nul
  start "" "http://localhost:8080"
  goto :end
)

where python >nul 2>nul
if %errorlevel%==0 (
  start "ULTIMECIA War Room Server" cmd /k python -m http.server 8080
  timeout /t 2 /nobreak >nul
  start "" "http://localhost:8080"
  goto :end
)

echo.
echo Nao foi possivel iniciar um servidor local automaticamente.
echo Abrindo a versao direta como contingencia...
start "" "%~dp0index.html"
pause

:end
endlocal
