#!/bin/bash
# Wrapper script to run SMIC Portfolio Analysis with proper environment settings
# This disables hardware acceleration to avoid Vulkan/GPU errors in WSL environments

export QT_QUICK_BACKEND=software
export QT_QPA_PLATFORM=xcb
export QTWEBENGINE_DISABLE_SANDBOX=1

# Disable GPU acceleration
python3 main_app.py --disable-gpu "$@"
