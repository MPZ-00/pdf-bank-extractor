#!/bin/bash
# Build script for PDF Bank Extractor

echo "Building PDF Bank Extractor..."

# Clean previous builds
if [ -d "dist" ]; then
    echo "Cleaning previous builds..."
    rm -rf dist build
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Build executable
echo "Building executable..."
pyinstaller --onefile --name pdf-bank-extractor --clean main.py

if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo "Executable created at: dist/pdf-bank-extractor"
    
    # Generate hash
    echo "Generating SHA256 hash..."
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        powershell -Command "Get-FileHash -Path 'dist/pdf-bank-extractor.exe' -Algorithm SHA256 | Select-Object -ExpandProperty Hash" > dist/pdf-bank-extractor.exe.sha256
    else
        # Unix-like
        sha256sum dist/pdf-bank-extractor > dist/pdf-bank-extractor.sha256
    fi
    
    echo "Build complete with hash verification!"
    echo "Remember to deactivate the virtual environment when done: deactivate"
else
    echo "Build failed!"
    exit 1
fi
