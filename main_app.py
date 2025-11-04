#!/usr/bin/env python3
"""
SMIC Portfolio Analysis GUI Application
Professional desktop application with PySide6 and Plotly
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QDateEdit, QTabWidget,
    QMessageBox, QFileDialog
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QDate, QUrl, QCoreApplication
from PySide6.QtGui import QFont
import pandas as pd
from datetime import datetime

# Import our analysis core
try:
    from analysis_core import generate_portfolio_analysis
except ImportError:
    print("Error: analysis_core.py not found. Make sure it's in the same directory.")
    sys.exit(1)


class TransactionForm(QWidget):
    """Widget for adding new transactions"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Add New Transaction")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Form fields
        form_layout = QVBoxLayout()
        
        # Sector
        sector_layout = QHBoxLayout()
        sector_layout.addWidget(QLabel("Sector:"))
        self.sector_input = QLineEdit()
        self.sector_input.setPlaceholderText("e.g., Technology, Healthcare, Financials")
        sector_layout.addWidget(self.sector_input)
        form_layout.addLayout(sector_layout)
        
        # Ticker
        ticker_layout = QHBoxLayout()
        ticker_layout.addWidget(QLabel("Ticker:"))
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("e.g., AAPL, VGT")
        ticker_layout.addWidget(self.ticker_input)
        form_layout.addLayout(ticker_layout)
        
        # Date
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date:"))
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        date_layout.addWidget(self.date_input)
        form_layout.addLayout(date_layout)
        
        # Shares
        shares_layout = QHBoxLayout()
        shares_layout.addWidget(QLabel("Shares:"))
        self.shares_input = QLineEdit()
        self.shares_input.setPlaceholderText("Optional - number of shares")
        shares_layout.addWidget(self.shares_input)
        form_layout.addLayout(shares_layout)
        
        # Purchase Price
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Purchase Price:"))
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Optional - price per share")
        price_layout.addWidget(self.price_input)
        form_layout.addLayout(price_layout)
        
        # Amount Invested
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("Amount Invested ($):"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Required - total dollar amount")
        amount_layout.addWidget(self.amount_input)
        form_layout.addLayout(amount_layout)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Transaction")
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        self.save_button.clicked.connect(self.save_transaction)
        button_layout.addWidget(self.save_button)
        
        self.clear_button = QPushButton("Clear Form")
        self.clear_button.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def save_transaction(self):
        """Save transaction to CSV file"""
        sector = self.sector_input.text().strip()
        ticker = self.ticker_input.text().strip().upper()
        date = self.date_input.date().toString("yyyy-MM-dd")
        shares = self.shares_input.text().strip()
        price = self.price_input.text().strip()
        amount = self.amount_input.text().strip()
        
        # Validation
        if not sector or not ticker or not amount:
            QMessageBox.warning(self, "Validation Error", 
                              "Sector, Ticker, and Amount Invested are required fields.")
            return
        
        try:
            float(amount)
        except ValueError:
            QMessageBox.warning(self, "Validation Error", 
                              "Amount Invested must be a valid number.")
            return
        
        # Prepare row data
        row_data = {
            'sector': sector,
            'ticker': ticker,
            'invest_date': date,
            'shares': float(shares) if shares else '',
            'purchase_price': float(price) if price else '',
            'amount_invested': float(amount)
        }
        
        # Check if CSV exists
        csv_file = 'data/transactions.csv'
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
        else:
            # Create new DataFrame with headers
            df = pd.DataFrame(columns=['sector', 'ticker', 'invest_date', 'shares', 
                                      'purchase_price', 'amount_invested'])
        
        # Append new row
        df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
        
        # Save to CSV
        try:
            df.to_csv(csv_file, index=False)
            QMessageBox.information(self, "Success", 
                                  f"Transaction saved successfully!\n\n"
                                  f"Sector: {sector}\n"
                                  f"Ticker: {ticker}\n"
                                  f"Date: {date}\n"
                                  f"Amount: ${float(amount):,.2f}")
            self.clear_form()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save transaction:\n{str(e)}")
    
    def clear_form(self):
        """Clear all form fields"""
        self.sector_input.clear()
        self.ticker_input.clear()
        self.date_input.setDate(QDate.currentDate())
        self.shares_input.clear()
        self.price_input.clear()
        self.amount_input.clear()


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        # Store dataframes for export
        self.summary_df = None
        self.ytd_df = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("SMIC Portfolio Analysis")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget with tabs
        tabs = QTabWidget()
        
        # Tab 1: Transaction Entry
        transaction_tab = TransactionForm()
        tabs.addTab(transaction_tab, "Add Transaction")
        
        # Tab 2: Analysis & Results
        analysis_tab = self.create_analysis_tab()
        tabs.addTab(analysis_tab, "Analysis & Results")
        
        self.setCentralWidget(tabs)
        
        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        
        open_action = file_menu.addAction('Open Transaction File...')
        open_action.triggered.connect(self.open_transaction_file)
        
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        
        help_menu = menubar.addMenu('Help')
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)
    
    def create_analysis_tab(self):
        """Create the analysis tab with controls and output"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls section
        controls_layout = QHBoxLayout()
        
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-size: 14px; font-weight: bold;")
        self.run_button.clicked.connect(self.run_analysis)
        controls_layout.addWidget(self.run_button)
        
        # Export buttons
        self.export_summary_button = QPushButton("Export Summary CSV")
        self.export_summary_button.clicked.connect(self.export_summary)
        self.export_summary_button.setEnabled(False)  # Disable until analysis is run
        controls_layout.addWidget(self.export_summary_button)
        
        self.export_ytd_button = QPushButton("Export YTD CSV")
        self.export_ytd_button.clicked.connect(self.export_ytd)
        self.export_ytd_button.setEnabled(False)  # Disable until analysis is run
        controls_layout.addWidget(self.export_ytd_button)
        
        controls_layout.addStretch()
        
        status_label = QLabel("Status: Ready")
        status_label.setStyleSheet("color: green; font-weight: bold;")
        controls_layout.addWidget(status_label)
        self.status_label = status_label
        
        layout.addLayout(controls_layout)
        
        # Results section - split view
        results_split = QHBoxLayout()
        
        # Left side: Text report
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Performance Report:"))
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Courier", 10))
        left_panel.addWidget(self.report_text)
        results_split.addLayout(left_panel, 1)
        
        # Right side: Charts (tabs for different charts)
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Interactive Charts:"))
        
        chart_tabs = QTabWidget()
        
        # Sector Allocation Chart
        self.sector_chart_view = QWebEngineView()
        self.sector_chart_view.setMinimumSize(600, 500)
        chart_tabs.addTab(self.sector_chart_view, "Sector Allocation")
        
        # Performance Chart
        self.performance_chart_view = QWebEngineView()
        self.performance_chart_view.setMinimumSize(600, 500)
        chart_tabs.addTab(self.performance_chart_view, "Performance")
        
        # ETF vs Stocks (Area)
        self.etf_chart_view = QWebEngineView()
        self.etf_chart_view.setMinimumSize(600, 500)
        chart_tabs.addTab(self.etf_chart_view, "ETF vs Stocks (Time)")
        
        # ETF vs Stocks (Bar)
        self.bar_chart_view = QWebEngineView()
        self.bar_chart_view.setMinimumSize(600, 500)
        chart_tabs.addTab(self.bar_chart_view, "ETF vs Stocks (Final)")
        
        # Weight Drift
        self.drift_chart_view = QWebEngineView()
        self.drift_chart_view.setMinimumSize(600, 500)
        chart_tabs.addTab(self.drift_chart_view, "Weight Drift")
        
        right_panel.addWidget(chart_tabs)
        results_split.addLayout(right_panel, 1)
        
        layout.addLayout(results_split)
        
        widget.setLayout(layout)
        return widget
    
    def run_analysis(self):
        """Run the portfolio analysis"""
        self.status_label.setText("Status: Running analysis...")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        self.run_button.setEnabled(False)
        QApplication.processEvents()
        
        try:
            # Check if transaction file exists
            if not os.path.exists('data/transactions.csv'):
                QMessageBox.warning(self, "File Not Found", 
                                  "Transaction file not found: data/transactions.csv\n\n"
                                  "Please add transactions first.")
                self.status_label.setText("Status: Error - No transaction file")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                self.run_button.setEnabled(True)
                return
            
            # Run analysis
            report_text, figures, summary_df, ytd_df = generate_portfolio_analysis('data/transactions.csv')
            
            # Store dataframes for export
            self.summary_df = summary_df
            self.ytd_df = ytd_df
            self.export_summary_button.setEnabled(True)
            self.export_ytd_button.setEnabled(True)
            
            # Display report
            self.report_text.setPlainText(report_text)
            
            # Display charts - ensure they load properly
            chart_views = {
                'sector_allocation': self.sector_chart_view,
                'performance': self.performance_chart_view,
                'etf_vs_stocks': self.etf_chart_view,
                'bar_comparison': self.bar_chart_view,
                'weight_drift': self.drift_chart_view
            }
            
            for fig_name, chart_view in chart_views.items():
                if fig_name in figures:
                    try:
                        html = figures[fig_name].to_html(include_plotlyjs='cdn')
                        # Use setHtml with empty QUrl for CDN resources (CDN loads via HTTP)
                        chart_view.setHtml(html, QUrl())
                        QApplication.processEvents()  # Allow GUI to update
                    except Exception as e:
                        # Silently continue if one chart fails, but log it
                        QMessageBox.warning(self, "Chart Load Warning", 
                                          f"Could not load {fig_name} chart: {str(e)}")
            
            self.status_label.setText("Status: Analysis complete!")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
        except Exception as e:
            error_msg = f"Error running analysis:\n\n{str(e)}"
            QMessageBox.critical(self, "Analysis Error", error_msg)
            self.status_label.setText("Status: Error occurred")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.report_text.setPlainText(error_msg)
        
        finally:
            self.run_button.setEnabled(True)
    
    def open_transaction_file(self):
        """Open a different transaction file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Transaction File", "data/", "CSV Files (*.csv)")
        if file_path:
            # Update the default path in analysis_core or pass as parameter
            QMessageBox.information(self, "File Selected", 
                                  f"Selected file: {file_path}\n\n"
                                  "Note: The analysis will use this file when you click 'Run Analysis'.")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About SMIC Portfolio Analysis",
                         "SMIC Portfolio Analysis v1.0\n\n"
                         "Professional portfolio analysis tool with:\n"
                         "• Transaction management\n"
                         "• Performance analysis\n"
                         "• Interactive Plotly charts\n"
                         "• Sector allocation tracking\n\n"
                         "Built with PySide6 and Plotly")
    
    def export_summary(self):
        """Saves the summary_df to a CSV file"""
        if self.summary_df is not None:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Summary Report", "data/smic_statistics_summary.csv", "CSV Files (*.csv)")
            if file_path:
                try:
                    self.summary_df.to_csv(file_path, index=False)
                    QMessageBox.information(self, "Success", f"Summary exported to {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export file: {e}")
    
    def export_ytd(self):
        """Saves the ytd_df to a CSV file"""
        if self.ytd_df is not None:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save YTD Report", "data/smic_sector_etf_vs_stocks_ytd.csv", "CSV Files (*.csv)")
            if file_path:
                try:
                    self.ytd_df.to_csv(file_path, index=False)
                    QMessageBox.information(self, "Success", f"YTD report exported to {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export file: {e}")


def main():
    # Disable hardware acceleration to avoid Vulkan/GPU errors in WSL/headless environments
    # Must set attributes BEFORE creating QApplication
    QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
    
    os.environ['QT_QUICK_BACKEND'] = 'software'
    os.environ['QTWEBENGINE_DISABLE_SANDBOX'] = '1'
    
    # Additional flags to disable GPU acceleration
    if '--disable-gpu' not in sys.argv:
        sys.argv.append('--disable-gpu')
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern, cross-platform look
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
