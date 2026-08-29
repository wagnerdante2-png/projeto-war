@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ULTIMECIA - Configurar Research Provider

echo.
echo ============================================================
echo  ULTIMECIA RESEARCH PROVIDER - CONFIGURACAO LOCAL
echo ============================================================
echo.
echo Este utilitario grava as configuracoes apenas no seu usuario
 echo Windows. A chave NAO e gravada no repositorio projeto-war.
echo.
set /p BASE=Base URL OpenAI-compatible (ex: https://api.openai.com/v1): 
set /p MODEL=Modelo: 
set /p KEY=API Key: 

if "%BASE%"=="" goto :invalid
if "%MODEL%"=="" goto :invalid
if "%KEY%"=="" goto :invalid

setx ULTIMECIA_LLM_BASE_URL "%BASE%" >nul
setx ULTIMECIA_LLM_MODEL "%MODEL%" >nul
setx ULTIMECIA_LLM_API_KEY "%KEY%" >nul

echo.
echo Configuracao salva no perfil do Windows.
echo Feche esta janela e inicie novamente INICIAR_RESEARCH_RUNNER.bat.
echo A chave nao foi escrita em nenhum arquivo do projeto.
echo.
pause
exit /b 0

:invalid
echo.
echo Configuracao cancelada: todos os campos sao obrigatorios.
pause
exit /b 1
