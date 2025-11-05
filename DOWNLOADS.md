# 📥 Download Executables

This document explains how to download the built executables for SMIC Portfolio Analysis.

## 🚀 Quick Download

### Option 1: GitHub Actions Artifacts (Recommended)

After each build completes, download the organized package:

1. Go to: https://github.com/joel-saucedo/SMIC-Portfolio-Analysis/actions
2. Find the latest successful workflow run
3. Look for the **"SMIC_Portfolio_Analysis-Downloads"** artifact
4. Download the zip file
5. Extract to get organized folder structure:

```
SMIC_Portfolio_Analysis/
├── windows/
│   └── SMIC_Portfolio_Analysis.exe
├── macos/
│   └── SMIC_Portfolio_Analysis.app
├── linux/
│   └── SMIC_Portfolio_Analysis
└── README.md
```

### Option 2: Individual Platform Downloads

Download individual platform executables:

- **Windows**: Look for "SMIC_Portfolio_Analysis-Windows" artifact
- **macOS**: Look for "SMIC_Portfolio_Analysis-macOS" artifact  
- **Linux**: Look for "SMIC_Portfolio_Analysis-Linux" artifact

### Option 3: GitHub Releases

When a release is created (tagged with `v*`), all executables are packaged together:

1. Go to: https://github.com/joel-saucedo/SMIC-Portfolio-Analysis/releases
2. Download: `SMIC_Portfolio_Analysis-All-Platforms.zip`
3. Or download individual platform zips

## 📁 Folder Structure

The organized download contains:

```
SMIC_Portfolio_Analysis/
├── windows/
│   └── SMIC_Portfolio_Analysis.exe    # Windows executable
├── macos/
│   └── SMIC_Portfolio_Analysis.app    # macOS app bundle (or executable)
├── linux/
│   └── SMIC_Portfolio_Analysis         # Linux executable
└── README.md                           # Usage instructions
```

## 🎯 Usage

### Windows
1. Navigate to `windows/` folder
2. Double-click `SMIC_Portfolio_Analysis.exe`
3. No installation needed!

### macOS
1. Navigate to `macos/` folder
2. Right-click `SMIC_Portfolio_Analysis.app` → Open
   - First time: System may warn - click "Open" to bypass Gatekeeper
3. Or if executable: `chmod +x SMIC_Portfolio_Analysis && ./SMIC_Portfolio_Analysis`

### Linux
1. Navigate to `linux/` folder
2. `chmod +x SMIC_Portfolio_Analysis`
3. `./SMIC_Portfolio_Analysis`

## 📦 What's Included

- ✅ **Self-contained executables** - No Python required
- ✅ **All dependencies bundled** - PySide6, Plotly, pandas, etc.
- ✅ **Data directory** - Included in executable
- ✅ **Ready to run** - Just download and execute

## 🔄 Automatic Packaging

The `package-artifacts.yml` workflow automatically:
- Runs after successful builds
- Downloads all platform executables
- Organizes them into a clean folder structure
- Creates zip files for easy distribution
- Uploads as "SMIC_Portfolio_Analysis-Downloads" artifact

## 📝 Notes

- **File Size**: Executables are large (~300-400MB) because they include Python and all dependencies
- **Internet Required**: Plotly charts use CDN, so internet connection is needed
- **Data Folder**: Application will create `data/` folder automatically on first run
- **Artifact Retention**: Downloads are retained for 30 days in GitHub Actions

## 🔗 Links

- **GitHub Actions**: https://github.com/joel-saucedo/SMIC-Portfolio-Analysis/actions
- **Releases**: https://github.com/joel-saucedo/SMIC-Portfolio-Analysis/releases
- **Repository**: https://github.com/joel-saucedo/SMIC-Portfolio-Analysis

