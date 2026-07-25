@echo off
chcp 65001 >nul
title Chatbot WhatsApp - Agente Haceb
cd /d "%~dp0"

echo ============================================================
echo   Conectando el agente Haceb a tu WhatsApp
echo ============================================================
echo.
echo  1) Arrancando el agente (ventana aparte)...
start "Agente Haceb (no cerrar)" /d "%~dp0.." python -m channels.whatsapp
timeout /t 7 >nul

echo  2) Abriendo WhatsApp. Va a aparecer un CODIGO QR aqui abajo.
echo.
echo     En tu celular:  WhatsApp  ^>  Ajustes  ^>  Dispositivos vinculados
echo                     ^>  Vincular un dispositivo  ^>  escanea el QR
echo.
echo  (si el QR expira, aparece uno nuevo solo)
echo ------------------------------------------------------------
echo.

node bot.js

echo.
echo El bot se detuvo. Cierra esta ventana o presiona una tecla.
pause >nul
