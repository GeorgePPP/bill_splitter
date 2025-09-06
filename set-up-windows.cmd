@echo off
setlocal enabledelayedexpansion

REM ---- CONFIG ----
set ENV_NAME=bill-splitter
set PYTHON_VERSION=3.11
set BACKEND_DIR=backend
set FRONTEND_DIR=frontend

REM ---- CHECK CONDA ----
where conda >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Conda is not installed or not in PATH.
    echo Please install Miniconda or Anaconda first.
    exit /b 1
)

REM ---- CHECK/CREATE CONDA ENV ----
conda env list | findstr /i "%ENV_NAME%" >nul
if errorlevel 1 (
    echo [INFO] Creating conda environment "%ENV_NAME%" with Python %PYTHON_VERSION%...
    conda create -y -n %ENV_NAME% python=%PYTHON_VERSION%
) else (
    echo [INFO] Conda environment "%ENV_NAME%" already exists.
)

REM ---- ACTIVATE ENV ----
call conda activate %ENV_NAME%
if errorlevel 1 (
    echo [ERROR] Failed to activate conda environment.
    exit /b 1
)

REM ---- CHECK PYTHON ----
python --version >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not available in the conda environment.
    exit /b 1
)

REM ---- INSTALL PYTHON DEPENDENCIES ----
cd "%BACKEND_DIR%"
if errorlevel 1 (
    echo [ERROR] Failed to navigate to backend directory.
    exit /b 1
)

echo [INFO] Installing Python dependencies...
echo [INFO] Upgrading pip...
pip install --upgrade pip >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    cd ..
    exit /b 1
)

echo [INFO] Installing requirements...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies.
    echo [INFO] Check the requirements.txt file for any issues.
    cd ..
    exit /b 1
) else (
    echo [INFO] Python dependencies installed successfully.
)
cd ..

REM ---- CHECK NODE/NPM ----
where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org/ and try again.
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] npm is not installed or not in PATH.
    echo Please install Node.js which includes npm and try again.
    exit /b 1
)

REM ---- CHECK NODE VERSION ----
echo [INFO] Checking Node.js version...
node --version
if errorlevel 1 (
    echo [ERROR] Failed to get Node.js version.
    exit /b 1
)

REM ---- CHECK IF FRONTEND DIRECTORY EXISTS ----
if not exist "%FRONTEND_DIR%" (
    echo [ERROR] Frontend directory not found: %FRONTEND_DIR%
    exit /b 1
)

REM ---- CHECK PACKAGE.JSON ----
if not exist "%FRONTEND_DIR%\package.json" (
    echo [ERROR] package.json not found in frontend directory.
    exit /b 1
)

REM ---- INSTALL FRONTEND DEPENDENCIES ----
cd "%FRONTEND_DIR%"
if errorlevel 1 (
    echo [ERROR] Failed to navigate to frontend directory.
    exit /b 1
)

echo [INFO] Installing frontend dependencies...
npm install
set NPM_EXIT_CODE=!errorlevel!
if !NPM_EXIT_CODE! neq 0 (
    echo [ERROR] Failed to install frontend dependencies.
    echo [INFO] Check the package.json file for any issues.
    cd ..
    exit /b 1
)
echo [INFO] Frontend dependencies installed successfully.
cd ..

REM ---- CHECK VITE ----
cd "%FRONTEND_DIR%"
echo [INFO] Checking Vite availability...
npx vite --version >nul 2>nul
if errorlevel 1 (
    echo [WARNING] Vite not found, but this should be installed with npm install.
    echo Continuing anyway...
) else (
    echo [INFO] Vite is available.
)
cd ..

echo.
echo [SUCCESS] Setup complete!
echo.
echo [INFO] Environment: %ENV_NAME%
echo [INFO] Python: Available in conda environment
echo [INFO] Node.js: Available
echo [INFO] Frontend dependencies: Installed
echo.
echo To start the app, run: start-windows.cmd

endlocal
pause