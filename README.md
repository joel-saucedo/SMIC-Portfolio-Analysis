# SMIC Portfolio Analysis GUI

A professional desktop application for analyzing and tracking your SMIC portfolio performance with interactive Plotly charts and comprehensive reporting.

## Features

- **Transaction Management**: Easy-to-use form for adding new portfolio transactions
- **Performance Analysis**: Comprehensive portfolio performance metrics vs S&P 500 benchmark
- **Interactive Charts**: Beautiful Plotly charts for sector allocation and performance tracking
- **Real-time Updates**: Run analysis on-demand with live results
- **Cross-platform**: Works on Windows, macOS, and Linux

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `pandas` - Data manipulation
- `yfinance` - Market data download
- `plotly` - Interactive charts
- `PySide6` - GUI framework
- `PySide6-WebEngine` - Web view for Plotly charts

### Step 2: Run the Application

**Option 1: Using the wrapper script (Recommended for WSL/Linux):**
```bash
./run_app.sh
```

**Option 2: Direct Python execution:**
```bash
python3 main_app.py
```

**Note:** If you encounter Vulkan/GPU errors, the application automatically disables hardware acceleration. You may see harmless error messages in the terminal (like "Failed to connect to the bus") - these do not affect functionality.

## Usage

### Adding Transactions

1. Click on the **"Add Transaction"** tab
2. Fill in the form:
   - **Sector**: e.g., "Technology", "Healthcare", "Financials"
   - **Ticker**: Stock or ETF symbol (e.g., "AAPL", "VGT")
   - **Date**: Transaction date
   - **Shares**: Number of shares (optional)
   - **Purchase Price**: Price per share (optional)
   - **Amount Invested**: Total dollar amount (required)
3. Click **"Save Transaction"**

### Running Analysis

1. Click on the **"Analysis & Results"** tab
2. Click the **"Run Analysis"** button
3. View results:
   - **Left Panel**: Text report with performance metrics
   - **Right Panel**: Interactive Plotly charts
     - **Sector Allocation**: Stacked area chart showing sector weights over time
     - **Performance**: Portfolio value and cumulative returns vs S&P 500

### Chart Interaction

The Plotly charts are fully interactive:
- **Hover**: See detailed values at any point
- **Zoom**: Click and drag to zoom in
- **Pan**: Use toolbar buttons or click and drag
- **Reset**: Click the reset button in the toolbar
- **Export**: Save charts as PNG images

## Project Structure

```
SMIC/
├── main_app.py              # GUI application (PySide6)
├── analysis_core.py         # Core analysis logic
├── smic.py                  # Original script (standalone)
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── data/
│   └── transactions.csv     # Transaction data
└── figs/                    # Generated charts (from smic.py)
```

## Packaging as Standalone Application

To create a standalone executable that doesn't require Python to be installed:

### Install PyInstaller

```bash
pip install pyinstaller
```

### Create Executable

**Windows:**
```bash
pyinstaller --onefile --windowed --name "SMIC_Portfolio_Analysis" main_app.py
```

**macOS/Linux:**
```bash
pyinstaller --onefile --name "SMIC_Portfolio_Analysis" main_app.py
```

### Additional Options

For a more complete package with an icon:

```bash
# Windows
pyinstaller --onefile --windowed --icon=icon.ico --name "SMIC_Portfolio_Analysis" main_app.py

# macOS
pyinstaller --onefile --icon=icon.icns --name "SMIC_Portfolio_Analysis" main_app.py
```

The executable will be in the `dist/` folder.

### Note for PyInstaller

You may need to create a spec file for more complex packaging. If you encounter issues with PySide6-WebEngine, you may need to explicitly include it:

```python
# Create spec file: pyinstaller --onefile main_app.py
# Then edit the spec file and add:

hiddenimports=[
    'PySide6.QtWebEngineWidgets',
    'plotly.graph_objects',
    'plotly.subplots'
]
```

## Troubleshooting

### Issue: "QWebEngineView not found"

**Solution**: Make sure PySide6-WebEngine is installed:
```bash
pip install PySide6-WebEngine
```

### Issue: Charts not displaying

**Solution**: 
1. Check that you have an internet connection (Plotly uses CDN for JavaScript)
2. Ensure PySide6-WebEngine is properly installed
3. Check the console for error messages

### Issue: "Transaction file not found"

**Solution**: 
1. Ensure `data/transactions.csv` exists
2. Add at least one transaction using the "Add Transaction" tab
3. The `data/` directory will be created automatically

### Issue: Price data download fails

**Solution**:
1. Check your internet connection
2. Verify ticker symbols are correct
3. Some tickers may not be available in yfinance

## Development

### Running Tests

You can test the core analysis function independently:

```python
from analysis_core import generate_portfolio_analysis

report, figures, summary_df, ytd_df = generate_portfolio_analysis()
print(report)
```

### Modifying Charts

Edit `analysis_core.py` to customize chart styling or add new visualizations. The `figures` dictionary can contain any number of Plotly figure objects.

### Adding Features

The modular design makes it easy to extend:
- `analysis_core.py`: Add new analysis calculations
- `main_app.py`: Add new GUI components or tabs
- Transaction form: Add validation or new fields

## License

This project is for personal/internal use.

## Support

For issues or questions, please check the troubleshooting section above or review the code comments for implementation details.
