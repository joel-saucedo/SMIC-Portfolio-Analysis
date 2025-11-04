@echo off
REM Build script for SMIC Portfolio Analysis standalone executable (Windows)
REM This creates a .exe file that doesn't require Python

echo ==================================================================================
echo Building SMIC Portfolio Analysis Standalone Executable (Windows)
echo ==================================================================================

REM Check if PyInstaller is installed
python -m pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

echo.
echo Step 1: Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo.
echo Step 2: Building standalone executable...
echo This may take a few minutes...

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "SMIC_Portfolio_Analysis" ^
    --add-data "data;data" ^
    --hidden-import PySide6.QtWebEngineWidgets ^
    --hidden-import plotly.graph_objects ^
    --hidden-import plotly.subplots ^
    --hidden-import pandas ^
    --hidden-import yfinance ^
    --hidden-import numpy ^
    --hidden-import plotly ^
    --exclude-module torch ^
    --exclude-module torchvision ^
    --exclude-module torchaudio ^
    --exclude-module tensorflow ^
    --exclude-module keras ^
    --exclude-module skimage ^
    --exclude-module sklearn ^
    --exclude-module scipy ^
    --exclude-module sympy ^
    --exclude-module numba ^
    --exclude-module cupy ^
    --exclude-module jupyter ^
    --exclude-module IPython ^
    --exclude-module matplotlib ^
    --exclude-module seaborn ^
    --exclude-module PIL ^
    --exclude-module cv2 ^
    --exclude-module opencv ^
    --collect-all PySide6 ^
    --collect-all plotly ^
    main_app.py

echo.
echo ==================================================================================
if exist "dist\SMIC_Portfolio_Analysis.exe" (
    echo BUILD SUCCESSFUL!
    echo ==================================================================================
    echo.
    echo Your executable is in the 'dist\' folder:
    dir dist\SMIC_Portfolio_Analysis.exe
    echo.
    echo To distribute:
    echo   1. Go to the 'dist\' folder
    echo   2. Zip the SMIC_Portfolio_Analysis.exe file
    echo   3. Share it with users
    echo.
    echo Users can run it directly - no Python installation needed!
) else (
    echo Build failed. Check the output above for errors.
    exit /b 1
)
echo ==================================================================================
