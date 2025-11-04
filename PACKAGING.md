# SMIC Portfolio Analysis - Packaging Guide

This guide will help you package the SMIC Portfolio Analysis application into a standalone executable that can be distributed to anyone, even without Python installed.

## Prerequisites

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Install all dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

## Basic Packaging

### Step 1: Simple One-File Executable

The simplest way to package the application:

```bash
pyinstaller --onefile --windowed --name SMIC_Portfolio_Analysis main_app.py
```

**What this does:**
- `--onefile`: Creates a single executable file
- `--windowed`: Hides the console window (no black terminal)
- `--name SMIC_Portfolio_Analysis`: Names the executable

**Output:** The executable will be in the `dist/` folder.

### Step 2: Include Data Directory

**CRITICAL:** The application needs the `data/` directory for `transactions.csv`. Use:

```bash
pyinstaller --onefile --windowed --name SMIC_Portfolio_Analysis --add-data "data:data" main_app.py
```

**What this does:**
- `--add-data "data:data"`: Bundles the `data/` folder into the executable
- The format is `source:destination` where both are `data` in this case

### Step 3: Add an Icon (Optional)

If you have an icon file:

**Windows:**
```bash
pyinstaller --onefile --windowed --name SMIC_Portfolio_Analysis --icon=icon.ico --add-data "data:data" main_app.py
```

**macOS:**
```bash
pyinstaller --onefile --name SMIC_Portfolio_Analysis --icon=icon.icns --add-data "data:data" main_app.py
```

## Advanced Packaging (Recommended)

For better control and to handle hidden imports, use a spec file:

### Step 1: Generate Initial Spec File

```bash
pyinstaller --name SMIC_Portfolio_Analysis main_app.py
```

This creates `SMIC_Portfolio_Analysis.spec`

### Step 2: Edit the Spec File

Open `SMIC_Portfolio_Analysis.spec` and modify it:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_app.py'],
    pathex=[],
    binaries=[],
    datas=[('data', 'data')],  # Add this line: bundle data directory
    hiddenimports=[
        'PySide6.QtWebEngineWidgets',
        'plotly.graph_objects',
        'plotly.subplots',
        'pandas',
        'yfinance',
        'numpy'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SMIC_Portfolio_Analysis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False to hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add path to icon here if you have one, e.g., 'icon.ico'
)
```

### Step 3: Build from Spec File

```bash
pyinstaller SMIC_Portfolio_Analysis.spec
```

## Distribution

### What to Distribute

After building, your `dist/` folder will contain:
- **SMIC_Portfolio_Analysis.exe** (Windows) or **SMIC_Portfolio_Analysis.app** (macOS)

**IMPORTANT:** The executable is self-contained. You can:
1. Zip the executable file
2. Send it to users
3. They can run it directly without any installation

### For Windows Users

1. Create a zip file containing:
   - `SMIC_Portfolio_Analysis.exe`
   - A README file with instructions

2. Users can:
   - Extract the zip
   - Double-click `SMIC_Portfolio_Analysis.exe` to run
   - The app will create a `data/` folder automatically if needed

### For macOS Users

1. Create a zip file containing:
   - `SMIC_Portfolio_Analysis.app`

2. Users may need to:
   - Right-click the app and select "Open" the first time (to bypass Gatekeeper)
   - Or: System Preferences → Security & Privacy → Allow the app

### For Linux Users

```bash
pyinstaller --onefile --name SMIC_Portfolio_Analysis --add-data "data:data" main_app.py
```

The executable will be in `dist/SMIC_Portfolio_Analysis`

## Troubleshooting

### Issue: "ModuleNotFoundError" when running executable

**Solution:** Add the missing module to `hiddenimports` in the spec file, then rebuild.

### Issue: Charts not displaying

**Solution:** Ensure `PySide6.QtWebEngineWidgets` is in `hiddenimports`. The app needs internet connection for Plotly CDN.

### Issue: "data/transactions.csv not found"

**Solution:** Make sure you used `--add-data "data:data"` in the PyInstaller command.

### Issue: Executable is very large (>100MB)

**This is normal!** PyInstaller bundles Python, all dependencies, and Qt libraries. The executable is large but self-contained.

### Issue: Antivirus flags the executable

**Solution:** This is a false positive. You may need to:
1. Sign the executable with a code signing certificate (Windows/macOS)
2. Submit to antivirus vendors for whitelisting
3. Distribute source code instead and let users install Python

## Quick Reference Commands

**Windows (one-file, with data):**
```bash
pyinstaller --onefile --windowed --name SMIC_Portfolio_Analysis --add-data "data:data" main_app.py
```

**macOS (one-file, with data):**
```bash
pyinstaller --onefile --name SMIC_Portfolio_Analysis --add-data "data:data" main_app.py
```

**Linux (one-file, with data):**
```bash
pyinstaller --onefile --name SMIC_Portfolio_Analysis --add-data "data:data" main_app.py
```

## Testing the Executable

Before distributing:

1. **Test on a clean machine** (or VM) without Python installed
2. **Test all features:**
   - Add a transaction
   - Run analysis
   - View all 5 charts
   - Export CSV files
3. **Check file paths:** Ensure the app can create/write to the `data/` folder

## Notes

- The first launch may be slower as PyInstaller extracts files to a temporary directory
- Internet connection is required for Plotly charts (they use CDN for JavaScript)
- Users can add transactions via the GUI - no need to manually edit CSV files
- The executable is platform-specific: Windows exe won't run on macOS, etc.
