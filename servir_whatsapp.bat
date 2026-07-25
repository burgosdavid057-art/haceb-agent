@echo off
REM Doble clic aqui para dejar el canal WhatsApp listo (agente + URL publica).
REM Deja esta ventana abierta. Pasa la URL que aparece a tu companero.
cd /d "%~dp0"
title Canal WhatsApp - Agente Haceb
python servir_whatsapp.py
echo.
echo El canal se detuvo. Cierra esta ventana o presiona una tecla para salir.
pause >nul
