#!/bin/bash
# Build script for PDF Bank Extractor

echo "Building PDF Bank Extractor..."

# Clean previous builds
if [ -d "dist" ]; then
    echo "Cleaning previous builds..."
    rm -rf dist build
fi

# Install dependencies if needed
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
else
    echo "Build failed!"
    exit 1
fi
