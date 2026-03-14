# 🔍 Fraud Analysis Tool

A comprehensive Streamlit-based web application designed for **Gujarat Cyber Police** and law enforcement cybercrime departments to analyze, consolidate, and manage fraud transaction data from Excel files.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Installation](#installation)
- [Usage](#usage)
- [Module Details](#module-details)
- [Database Integration](#database-integration)
- [Security](#security)

---

## 🎯 Overview

This application processes fraud transaction data from multiple Excel/CSV files, aggregates transactions by fraudster bank account numbers, and generates comprehensive reports. It's optimized for handling large datasets (millions of rows) with fast, vectorized operations.

---

## ✨ Key Features

### 1. 📤 Multi-File Upload & Processing
- Upload **1 to 50 Excel/CSV files** simultaneously using Ctrl+Click
- Supports `.xlsx`, `.xls`, and `.csv` formats
- Maximum file size: **200MB per file**
- Automatic file validation and error handling
- Progress tracking during file processing

### 2. 🔗 Smart Column Detection
- **Fuzzy matching** algorithm using RapidFuzz library
- Auto-detects columns with **80%+ confidence threshold**
- Supports various column naming conventions:
  - Bank Account Number (account no, bank ac no, a/c no, etc.)
  - Acknowledgement Number (ack no, ref no, etc.)
  - Amount (transaction amount, txn amount, fraud amount)
  - Disputed Amount (disputed, claim amount, chargeback)
  - IFSC Code, Bank Name, Address, District, State
- Manual override for ambiguous mappings
- Confidence scores displayed for each detected column

### 3. ⚙️ Data Processing Engine
- **Vectorized pandas operations** for high performance
- Data cleaning:
  - Remove empty rows
  - Trim whitespace from all fields
  - Standardize account numbers (remove spaces, dashes)
  - Parse currency amounts (handles ₹, Rs, INR, USD, etc.)
- Validation:
  - Account number format (9-18 digits)
  - IFSC code format (11 alphanumeric characters)
  - Amount validation (positive numbers)
  - Duplicate acknowledgement detection

### 4. 📊 Aggregation by Account
- Groups all transactions by **Fraudster Bank Account Number**
- Collects **ALL unique ACK numbers** for each account
- Calculates:
  - Total Transactions count
  - Total Amount
  - Total Disputed Amount
  - ACK Count (distinct acknowledgement numbers)
  - Risk Score (based on transaction count and amount)
- Preserves Bank Name, IFSC Code, Address, District, State

### 5. 📈 Results Dashboard
- **Summary Statistics**:
  - Total Input Rows
  - Unique Accounts
  - Total Fraud Amount
  - Average Amount per Account
  - Rows with Errors
- **Top Accounts** by fraud amount
- Interactive data table with filtering

### 6. 📥 Report Generation
- **Excel Report** (.xlsx) - Full data with all columns
- **CSV Report** (.csv) - For data analysis tools
- **PDF Report** - Summary with top 20 accounts, statistics, quality metrics
- **Audit Log** (.txt) - Processing timestamp, errors, row counts

### 7. 🗄️ MySQL Database Integration
- Save aggregated results to MySQL database
- **Data integrity verification** with checksums
- **Batch processing** (10,000 records per batch)
- Features:
  - Save datasets with custom names
  - Load and view saved datasets
  - Advanced filtering (by account, bank, district, state, amount range)
  - Sorting by any column
  - Delete datasets
  - Verify data integrity
  - Export filtered data to Excel/CSV

### 8. 📍 District Data Download
- **Victim Data (Gujarat)**: Filter by 33 Gujarat districts
- **Suspect Data (All India)**: Browse by State → District or search
- **Match Victim & Suspect**: Match records by ACK number
- **Remove Duplicates**: Remove duplicate ACK numbers from files
- Optimized for millions of rows with vectorized operations

### 9. 📂 Merge Excel Files
- Upload **1 to 15 Excel files**
- Auto-detect columns (Account No, ACK No, Amount, etc.)
- Merge and aggregate by account number
- Download combined summary as Excel/CSV
- Handles files with different column names

### 10. 📎 Simple Excel Merger
- Combine multiple Excel/CSV files into one
- Files must have same column structure
- Row-by-row concatenation
- Download merged file as Excel or CSV

### 11. 📞 Call Notice Data Merge
- Match records from two files based on **mobile numbers**
- Normalizes mobile numbers (handles country codes, scientific notation)
- Calculates **time difference** between Call Date and Entry Date
- Output includes:
  - Acknowledgement Number
  - Mobile Number
  - Call Date
  - Entry Date
  - Time Difference (H:MM:SS format)
  - Average time difference

### 12. 🔄 Transaction ID & Bank Matcher
- Match records from two files based on **Transaction ID** and **Bank Name**
- **File 1**: Complaint data with Transaction ID and Bank Name columns
- **File 2**: Bank data with Action column (extracts bank name), Transaction ID, Account Number, Transaction Date
- Smart extraction:
  - Extracts bank name from "Money Transfer To :HDFC Bank" → "HDFC Bank"
  - Extracts transaction ID from "Transaction Id :AXNPN35101489308" → "AXNPN35101489308"
- Adds **Account Number** and **Transaction Date** from File 2 to File 1
- Output maintains original File 1 column order with new columns inserted after Transaction ID

---

## 🚀 Installation

### Prerequisites
- Python 3.8+
- MySQL Server (for database features)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
- streamlit
- pandas
- openpyxl
- xlrd
- rapidfuzz
- mysql-connector-python
- reportlab (for PDF generation)

---

## 💻 Usage

### Start the Application
```bash
streamlit run src/app.py
```

Or use the launcher:
```bash
launcher.bat
```

### Workflow
1. **Upload Files** - Select 1-50 Excel/CSV files
2. **Column Mapping** - Verify auto-detected columns or manually map
3. **Processing** - Clean, validate, and aggregate data
4. **Results** - View dashboard, download reports, save to database

---

## 📁 Module Details

| Module | Description |
|--------|-------------|
| `app.py` | Main Streamlit application with navigation |
| `upload_service.py` | File upload validation and reading |
| `column_detector.py` | Fuzzy matching for column detection |
| `data_processor.py` | Data cleaning and standardization |
| `validation_engine.py` | Data validation and quality checks |
| `aggregation_engine.py` | Group by account and calculate totals |
| `report_generator.py` | Excel, CSV, PDF, and audit log generation |
| `dashboard.py` | Statistics calculation and filtering |
| `database_service.py` | MySQL database operations |
| `district_data.py` | District-wise data filtering and matching |
| `merge_files.py` | Multi-file merge with aggregation |
| `excel_merger.py` | Simple file concatenation |
| `call_notice_data_merge.py` | Mobile number matching with time calculation |
| `transaction_matcher.py` | Transaction ID & Bank Name matching |
| `session_manager.py` | In-memory session management |
| `models.py` | Data models and type definitions |

---

## 🗄️ Database Integration

### Configuration
Default MySQL settings:
- Host: `localhost`
- Port: `3306`
- User: `root`
- Database: `gujarat_cyber_police`

### Tables
- **datasets** - Metadata for saved datasets
- **aggregated_accounts** - Aggregated fraud account data

### Features
- Automatic table creation
- Transaction-based saves with rollback on error
- SHA256 checksum for data integrity
- Indexed columns for fast queries

---

## 🔒 Security

- **In-memory processing** - No data stored on server after session ends
- **Session timeout** - 30 minutes of inactivity
- **Data validation** - Input sanitization and format checks
- **Database transactions** - Atomic operations with rollback

---

## 📊 Output Columns

The aggregated output includes:
1. Fraudster Bank Account Number
2. All Acknowledgement Numbers (semicolon-separated)
3. ACK Count
4. Bank Name
5. IFSC Code
6. Address
7. District
8. State
9. Total Transactions
10. Total Amount
11. Total Disputed Amount
12. Risk Score

---

## 🛠️ Technical Specifications

- **Max File Size**: 200MB
- **Max Files**: 50 (upload), 15 (merge)
- **Supported Formats**: .xlsx, .xls, .csv
- **Database Batch Size**: 10,000 records
- **Session Timeout**: 30 minutes
- **Account Number Length**: 9-18 digits
- **IFSC Code Length**: 11 characters

---

## 📞 Support

For Gujarat Cyber Police internal use.

---

*Built with Streamlit, Pandas, and MySQL*
