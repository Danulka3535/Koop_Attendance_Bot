@echo off
:: Set console color (green text on black background)
color 0A

:: Clear the screen
cls

:: Program header
echo =================================================================================
echo                               Starting KAB...
echo =================================================================================
echo.
echo               The program is running. Press Ctrl+C at any time to stop the process.
echo.
echo =================================================================================
echo.

:: Function to check if Python is installed
:check_python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not added to PATH.
    pause
    goto restart_or_exit
)

:: Change directory to the project folder
:change_directory
cd /d C:\TG_Bot\Koop_Attendance_Bot-main\Koop_Attendance_Bot-main || (
    echo Error: Unable to change directory to C:\TG_Bot\Koop_Attendance_Bot-main\Koop_Attendance_Bot-main
    pause
    goto restart_or_exit
)

:: Activate virtual environment
:activate_venv
call .venv\Scripts\activate || (
    echo Error: Unable to activate virtual environment
    pause
    goto restart_or_exit
)

:: Main menu
:main_menu
echo.
echo =================================================================================
echo                                Main Menu
echo =================================================================================
echo.
echo 1. Start KAB
echo 2. View Log File
echo 3. Exit
echo.
set /p choice=Enter your choice (1-3): 

:: Handle user choice
if "%choice%"=="1" goto start_ppsb
if "%choice%"=="2" goto view_log
if "%choice%"=="3" goto exit_program
echo Invalid choice. Please try again.
goto main_menu

:: Start KAB
:start_ppsb
echo Running KAB...
echo Running KAB... > output.log 2>&1
(
    python main.py
) | findstr /r /c:".*" >> output.log 2>&1
if %errorlevel% neq 0 (
    echo Error: Unable to run main.py
    echo Check output.log for details.
    pause
    goto restart_or_exit
)
echo PPSB has finished running.
pause
goto main_menu

:: View Log File
:view_log
if not exist output.log (
    echo Log file does not exist.
    pause
    goto main_menu
)
type output.log
pause
goto main_menu

:: Exit Program
:exit_program
echo Exiting KAB...
exit /b 0

:: Restart or Exit after error
:restart_or_exit
echo.
echo =================================================================================
echo                                Error Occurred
echo =================================================================================
echo.
echo 1. Restart KAB
echo 2. Exit
echo.
set /p choice=Enter your choice (1-2): 

if "%choice%"=="1" goto start_ppsb
if "%choice%"=="2" goto exit_program
echo Invalid choice. Please try again.
goto restart_or_exit