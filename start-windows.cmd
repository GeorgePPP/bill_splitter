@echo off
setlocal

set ENV_NAME=bill-splitter
set BACKEND_DIR=backend
set FRONTEND_DIR=frontend

REM ---- CHECK CONDA ----
where conda >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Conda is not installed or not in PATH.
    echo Please run set-up-windows.cmd first.
    exit /b 1
)

REM ---- CHECK IF DIRECTORIES EXIST ----
if not exist "%BACKEND_DIR%" (
    echo [ERROR] Backend directory not found: %BACKEND_DIR%
    echo Please run set-up-windows.cmd first.
    exit /b 1
)

if not exist "%FRONTEND_DIR%" (
    echo [ERROR] Frontend directory not found: %FRONTEND_DIR%
    echo Please run set-up-windows.cmd first.
    exit /b 1
)

REM ---- CHECK IF NODE_MODULES EXISTS ----
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [ERROR] Frontend dependencies not installed.
    echo Please run set-up-windows.cmd first.
    exit /b 1
)

REM ---- CHECK IF CONDA ENV EXISTS ----
call conda env list | findstr /i "%ENV_NAME%" >nul
if errorlevel 1 (
    echo [ERROR] Conda environment "%ENV_NAME%" not found.
    echo Please run set-up-windows.cmd first.
    exit /b 1
)

REM ---- START BACKEND ----
echo [INFO] Starting backend server...
start "Bill Splitter Backend" cmd /k "conda activate %ENV_NAME% && cd %BACKEND_DIR% && python run.py"

REM ---- WAIT A MOMENT FOR BACKEND TO START ----
timeout /t 3 /nobreak >nul

REM ---- START FRONTEND ----
echo [INFO] Starting frontend server...
start "Bill Splitter Frontend" cmd /k "cd %FRONTEND_DIR% && npm run dev"

echo.
echo [SUCCESS] Both backend and frontend are starting in new windows.
echo [INFO] Backend: http://localhost:8000
echo [INFO] Frontend: http://localhost:3000
echo.
echo [TIP] Wait for both servers to fully start before using the app.
echo [TIP] Check the terminal windows for any error messages.

endlocal
pause