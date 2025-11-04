#!/bin/bash
# Build script for SMIC Portfolio Analysis standalone executable
# This creates a single file executable that doesn't require Python

set -e  # Exit on error

echo "=================================================================================="
echo "Building SMIC Portfolio Analysis Standalone Executable"
echo "=================================================================================="

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

echo ""
echo "Step 1: Cleaning previous builds..."
rm -rf build/ dist/ *.spec 2>/dev/null || true

echo ""
echo "Step 2: Building standalone executable..."
echo "This may take a few minutes..."

pyinstaller \
    --onefile \
    --windowed \
    --name "SMIC_Portfolio_Analysis" \
    --add-data "data:data" \
    --hidden-import PySide6.QtWebEngineWidgets \
    --hidden-import plotly.graph_objects \
    --hidden-import plotly.subplots \
    --hidden-import pandas \
    --hidden-import yfinance \
    --hidden-import numpy \
    --hidden-import plotly \
    --exclude-module torch \
    --exclude-module torchvision \
    --exclude-module torchaudio \
    --exclude-module tensorflow \
    --exclude-module keras \
    --exclude-module skimage \
    --exclude-module sklearn \
    --exclude-module scipy \
    --exclude-module sympy \
    --exclude-module numba \
    --exclude-module cupy \
    --exclude-module jupyter \
    --exclude-module IPython \
    --exclude-module matplotlib \
    --exclude-module seaborn \
    --exclude-module PIL \
    --exclude-module cv2 \
    --exclude-module opencv \
    --collect-all PySide6 \
    --collect-all plotly \
    main_app.py

echo ""
echo "=================================================================================="
if [ -f "dist/SMIC_Portfolio_Analysis" ] || [ -f "dist/SMIC_Portfolio_Analysis.exe" ]; then
    echo "✅ BUILD SUCCESSFUL!"
    echo "=================================================================================="
    echo ""
    echo "Your executable is in the 'dist/' folder:"
    ls -lh dist/SMIC_Portfolio_Analysis* 2>/dev/null || ls -lh dist/*.exe 2>/dev/null
    echo ""
    echo "To distribute:"
    echo "  1. Go to the 'dist/' folder"
    echo "  2. Zip the executable file"
    echo "  3. Share it with users"
    echo ""
    echo "Users can run it directly - no Python installation needed!"
else
    echo "❌ Build failed. Check the output above for errors."
    exit 1
fi
echo "=================================================================================="
