@echo off
REM Переход в директорию скрипта (если BAT-файл не в корне проекта)
cd /d "%~dp0"

REM Активация виртуального окружения (если используется)
call venv\Scripts\activate

REM Запуск бота
python main.py

REM Пауза, чтобы окно не закрылось сразу
pause