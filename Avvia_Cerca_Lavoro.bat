@echo off
echo =======================================================
echo              APP CERCA LAVORO - AVVIO IN CORSO
echo =======================================================
echo.
echo Avvio della ricerca automatica delle offerte di lavoro...
echo (Questa operazione puo' richiedere alcuni minuti, non chiudere la finestra)
echo.

cd /d "%~dp0"
call .venv\Scripts\python.exe main.py --no-telegram --no-email --no-ai

echo.
echo =======================================================
echo          RICERCA COMPLETATA CON SUCCESSO!
echo =======================================================
echo Puoi trovare i report aggiornati nella cartella "data\reports"
echo.
pause
