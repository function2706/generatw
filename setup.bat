@echo off
setlocal

set REQUIRED_VERSION=3.12

echo Checking Python %REQUIRED_VERSION% availability...
py -%REQUIRED_VERSION% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python %REQUIRED_VERSION% is not installed.
    pause
    exit /b 1
)
echo Python %REQUIRED_VERSION% found.

echo Creating virtual environment...
py -%REQUIRED_VERSION% -m venv venv

echo Activating venv...
call venv\Scripts\activate

echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Done. Close me...
pause
