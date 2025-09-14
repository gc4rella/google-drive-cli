@echo off
REM Google Drive CLI Manager Setup Script for Windows
REM This script sets up the virtual environment and dependencies

echo 🚀 Setting up Google Drive CLI Manager...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.7+ and try again.
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Found Python %PYTHON_VERSION%

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv drive-cli-env
if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment
    echo 💡 Try: pip install virtualenv ^&^& virtualenv drive-cli-env
    pause
    exit /b 1
)
echo ✅ Virtual environment created successfully

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call drive-cli-env\Scripts\activate

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed successfully

echo.
echo 🎉 Setup complete!
echo.
echo 📋 Next steps:
echo 1. Activate the virtual environment:
echo    drive-cli-env\Scripts\activate
echo.
echo 2. Set up Google Drive API credentials:
echo    python main.py setup
echo.
echo 3. Test the connection:
echo    python main.py test
echo.
echo 4. Start analyzing your Drive:
echo    python main.py scan
echo.
echo 💡 To deactivate the virtual environment later, just run: deactivate
pause