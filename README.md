# SMIC Portfolio Analysis

Official portfolio analysis and tracking software developed as a service to the Student Managed Investment Committee (SMIC) at Georgia College & State University for managing the university endowment fund. This application provides comprehensive portfolio performance analysis, sector allocation tracking, and interactive visualizations for the management of institutional investment assets.

## Project Overview

The SMIC Portfolio Analysis system simulates a portfolio that starts with an initial allocation across 11 Vanguard sector ETFs, fixed income securities, and cash. The system allows strategic swaps from ETFs to individual stocks within each sector, tracking portfolio performance, sector drift, and providing detailed analytics against the S&P 500 benchmark.

## Key Features

- **Portfolio Simulation**: Realistic modeling of ETF-to-stock swaps with natural sector weight drift
- **Performance Analytics**: Comprehensive metrics including CAGR, total returns, drawdowns, and sector allocation changes
- **Interactive Visualizations**: Professional Plotly charts for portfolio value, sector allocation, and performance comparisons
- **Cross-Platform Executables**: Standalone applications for Windows, macOS, and Linux (no Python required)
- **Automated Builds**: CI/CD pipeline via GitHub Actions for all platforms
- **Transaction Management**: Easy-to-use GUI for adding and managing portfolio transactions

## Mathematical Model

### Portfolio Construction

The portfolio simulation follows a realistic drift model:

1. **Initial State**: Portfolio starts with an initial allocation across 11 Vanguard sector ETFs, fixed income securities, and cash. The sector ETFs are not equal-weighted; allocation percentages are determined by the initial investment amounts on the portfolio start date (August 27, 2024). The initial portfolio value is approximately $100,594, with sector allocations ranging from approximately 1.5% to 16% per sector, plus fixed income and cash positions.
2. **ETF-to-Stock Swaps**: When a stock is purchased:
   - The corresponding sector ETF is sold (dollar-neutral swap)
   - The stock is purchased with the same dollar amount
   - Sector weight remains constant at the moment of swap
3. **Natural Drift**: After swaps, sector weights drift naturally based on relative performance of:
   - Remaining ETF holdings
   - Individual stock holdings
   - No rebalancing occurs (realistic buy-and-hold approach)

### Performance Calculations

**Portfolio Value**:

$$V(t) = \sum_{i=1}^{n} u_i(t) \times p_i(t) + C$$

where $u_i(t)$ represents the number of units (shares) of asset $i$ at time $t$, $p_i(t)$ is the price of asset $i$ at time $t$, and $C$ is the cash balance.

**Cumulative Returns**:

$$R_{cum}(t) = \left( \frac{V(t)}{V(0)} - 1 \right) \times 100\%$$

where $V(0)$ is the initial portfolio value.

**CAGR (Compound Annual Growth Rate)**:

$$CAGR = \left( \frac{V_{final}}{V_{initial}} \right)^{\frac{1}{T}} - 1$$

where $T$ is the time period in years.

**Sector Weights**:

$$w_i(t) = \frac{V_i(t)}{V_{total}(t)} \times 100\%$$

where $V_i(t)$ represents the total value of sector $i$ at time $t$ (including both ETF and individual stock holdings within that sector), and $V_{total}(t)$ is the total portfolio value.

### Benchmark Comparison

The S&P 500 ($\text{^GSPC}$) is used as the benchmark, normalized to the portfolio's initial value:

$$V_{benchmark}(t) = \frac{P_{S\&P500}(t)}{P_{S\&P500}(0)} \times V_{initial}$$

This allows for direct dollar-for-dollar comparison while maintaining percentage return accuracy.

## Project Successes

### Technical Achievements

**Automated Cross-Platform Builds**: Successfully implemented GitHub Actions workflows that automatically build executables for Windows, macOS, and Linux on every push

**Professional GUI Application**: Developed a polished PySide6-based desktop application with interactive Plotly visualizations

**Accurate Portfolio Simulation**: Implemented realistic portfolio modeling with proper handling of:
- ETF-to-stock swaps
- Natural sector weight drift
- Cash and fixed income allocations
- Daily portfolio valuation

**Comprehensive Analytics**: Built robust analysis engine that calculates:
- Portfolio performance metrics (CAGR, total returns, drawdowns)
- Sector allocation tracking over time
- ETF vs. individual stock breakdowns
- YTD and full-period comparisons

**Production-Ready Packaging**: Created PyInstaller spec file with proper dependency collection, resulting in self-contained executables (~300-400MB)

### Performance Metrics

- **Build Success Rate**: 100% across all platforms (Windows, macOS, Linux)
- **Code Quality**: Modular architecture with separation of concerns (GUI, analysis, data)
- **User Experience**: Intuitive interface with real-time analysis and interactive charts

## Getting Started

### Prerequisites

- Python 3.8+ (for development)
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/joel-saucedo/SMIC-Portfolio-Analysis.git
cd SMIC-Portfolio-Analysis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main_app.py
```

### Using Pre-built Executables

Download the latest executables from [GitHub Actions](https://github.com/joel-saucedo/SMIC-Portfolio-Analysis/actions):
- Look for the "SMIC_Portfolio_Analysis-Downloads" artifact
- Extract and run the executable for your platform
- No Python installation required!

## Project Structure

```
SMIC/
├── main_app.py              # GUI application (PySide6)
├── analysis_core.py     # Core portfolio analysis engine
├── smic.py                # Standalone analysis script
├── requirements.txt       # Python dependencies
├── SMIC_Portfolio_Analysis.spec  # PyInstaller configuration
├── data/
│   ├── transactions.csv   # Portfolio transaction data
│   └── *.csv              # Generated analysis reports
├── figs/                  # Generated charts (from smic.py)
├── .github/
│   └── workflows/         # CI/CD build workflows
└── build_executable*.sh   # Platform-specific build scripts
```

## Development

### Building Executables Locally

**Linux/macOS**:
```bash
./build_executable.sh        # Linux
./build_executable_macos.sh  # macOS
```

**Windows**:
```cmd
build_executable_windows.bat
```

### Running Analysis

The core analysis can be run independently:
```python
from analysis_core import generate_portfolio_analysis

report, figures, summary_df, ytd_df = generate_portfolio_analysis()
print(report)
```

## Future Development

We are actively working on implementing the following features to enhance the portfolio management capabilities:

### Planned Features

- **Rebalancing Functionality**: Automated rebalancing to target sector allocations with configurable thresholds
- **Stock Selling**: Support for selling individual positions with proper tracking of realized gains/losses
- **Tax-Loss Harvesting**: Identification of tax-loss harvesting opportunities
- **Advanced Analytics**: 
  - Risk metrics (Sharpe ratio, Sortino ratio, beta)
  - Correlation analysis between sectors
  - Attribution analysis (ETF vs. stock performance contribution)
- **Portfolio Optimization**: 
  - Efficient frontier analysis
  - Sector allocation optimization
  - Risk-adjusted return maximization
- **Reporting Enhancements**:
  - Automated PDF report generation
  - Email notifications for significant portfolio changes
  - Customizable report templates
- **Data Integration**:
  - Real-time price updates
  - Dividend tracking and reinvestment
  - Corporate action handling (splits, mergers)

### Contributing

We welcome contributions! Please see our development guidelines and feel free to submit pull requests or open issues for bugs and feature requests.

## Documentation

- **Packaging Guide**: See `PACKAGING.md` for detailed instructions on building executables
- **API Documentation**: Code is well-commented with docstrings explaining key functions
- **Workflow Documentation**: GitHub Actions workflows are documented inline

## Disclaimer

**Conflict of Interest Disclosure**: The developer of this software, Joel Saucedo, serves as a Managing Director for the Student Managed Investment Committee (SMIC) at Georgia College & State University. This software is developed in that capacity for the purpose of managing the university endowment fund.

**Not Financial Advice**: This software is provided for informational and analytical purposes only. The analysis, calculations, and visualizations generated by this software do not constitute financial advice, investment recommendations, or solicitation to buy or sell any securities. All investment decisions should be made in consultation with qualified financial advisors and in accordance with the investment policies and guidelines established by the university and the SMIC board.

**No Warranty**: This software is provided "as is" without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement. The developers and contributors shall not be liable for any damages arising from the use of this software.

## License

This software is licensed under a proprietary license. See [LICENSE](LICENSE) file for full terms and conditions.

**Summary**: Copyright (c) 2025 Joel Saucedo. All rights reserved. This software is proprietary and may not be copied, modified, or distributed without express written permission from Joel Saucedo. Limited educational use at Georgia College & State University is permitted under SMIC supervision.

## Contact

**Developer**: Joel Saucedo  
**Role**: Managing Director, Student Managed Investment Committee  
**Institution**: Georgia College & State University

For questions, issues, technical support, or licensing inquiries regarding this software, please contact Joel Saucedo.

## Acknowledgments

- **Vanguard ETFs**: Sector-based ETF tracking
- **yfinance**: Market data retrieval
- **Plotly**: Interactive visualizations
- **PySide6**: Cross-platform GUI framework
- **Student Managed Investment Committee**: Georgia College & State University

---

**Last Updated**: November 2025  
**Version**: 1.0.0  
**Status**: Active Development
