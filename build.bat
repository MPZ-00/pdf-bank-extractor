@echo off
REM Build script for PDF Bank Extractor (Windows)

echo Building PDF Bank Extractor...

REM Clean previous builds
if exist "dist" (
    echo Cleaning previous builds...
    rmdir /s /q dist
    rmdir /s /q build
)

REM Create and activate virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Build executable
echo Building executable...
pyinstaller --onefile --name pdf-bank-extractor --clean main.py

if %errorlevel% == 0 (
    echo Build successful!
    echo Executable created at: dist\pdf-bank-extractor.exe
    
    REM Generate hash
    echo Generating SHA256 hash...
    powershell -Command "Get-FileHash -Path 'dist\pdf-bank-extractor.exe' -Algorithm SHA256 | Select-Object -ExpandProperty Hash" > dist\pdf-bank-extractor.exe.sha256
    
    echo Build complete with hash verification!
    echo Remember to deactivate the virtual environment when done: deactivate
) else (
    echo Build failed!
    exit /b 1
)
