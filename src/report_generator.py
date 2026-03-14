"""
Report Generator for the Fraud Analysis Application.

Generates Excel, CSV, and PDF reports from aggregated transaction data,
as well as audit logs for processing sessions.
"""

from datetime import datetime
from typing import List, Optional
import csv
import io
import pandas as pd

from src.models import AggregatedAccount, ProcessingStats


class ReportGenerator:
    """Generator for creating reports in various formats."""
    
    # Column headers for output files
    OUTPUT_COLUMNS = [
        "Fraudster Bank Account Number",
        "All Acknowledgement Numbers",
        "ACK Count",
        "Bank Name",
        "IFSC Code",
        "Address",
        "District",
        "State",
        "Total Transactions",
        "Total Amount",
        "Total Disputed Amount",
        "Risk Score"
    ]
    
    def _accounts_to_dataframe(
        self, 
        accounts: List[AggregatedAccount]
    ) -> pd.DataFrame:
        """
        Convert list of AggregatedAccount objects to a DataFrame.
        
        Args:
            accounts: List of AggregatedAccount objects.
            
        Returns:
            DataFrame with standardized column names.
        """
        if not accounts:
            return pd.DataFrame(columns=self.OUTPUT_COLUMNS)
        
        data = []
        for account in accounts:
            # Count ACK numbers by splitting the string
            # Handle both comma and semicolon separators
            ack_numbers = account.acknowledgement_numbers
            if ack_numbers and ack_numbers.strip():
                # Replace semicolons with commas, then split
                ack_str = ack_numbers.replace(';', ',')
                ack_count = len([a.strip() for a in ack_str.split(',') if a.strip()])
            else:
                ack_count = 0
            
            data.append({
                "Fraudster Bank Account Number": account.account_number,
                "All Acknowledgement Numbers": account.acknowledgement_numbers,
                "ACK Count": ack_count,
                "Bank Name": account.bank_name,
                "IFSC Code": account.ifsc_code,
                "Address": account.address,
                "District": account.district,
                "State": account.state,
                "Total Transactions": account.total_transactions,
                "Total Amount": account.total_amount,
                "Total Disputed Amount": account.total_disputed_amount,
                "Risk Score": account.risk_score
            })
        
        return pd.DataFrame(data, columns=self.OUTPUT_COLUMNS)

    
    def generate_excel(
        self, 
        accounts: List[AggregatedAccount], 
        filepath: str
    ) -> None:
        """
        Generate summary Excel file from aggregated accounts.
        
        Creates an Excel file with columns: Fraudster Bank Account Number,
        Bank Name, IFSC Code, Address, Total Transactions, 
        All Acknowledgement Numbers, Total Amount, Total Disputed Amount, Risk Score.
        
        Args:
            accounts: List of AggregatedAccount objects to export.
            filepath: Path where the Excel file should be saved.
        """
        df = self._accounts_to_dataframe(accounts)
        # Ensure account number is stored as string to preserve leading zeros
        if "Fraudster Bank Account Number" in df.columns:
            df["Fraudster Bank Account Number"] = df["Fraudster Bank Account Number"].astype(str)
        df.to_excel(filepath, index=False, engine='openpyxl')
    
    def generate_excel_bytes(
        self, 
        accounts: List[AggregatedAccount]
    ) -> bytes:
        """
        Generate summary Excel file as bytes (for streaming downloads).
        
        Args:
            accounts: List of AggregatedAccount objects to export.
            
        Returns:
            Excel file content as bytes.
        """
        df = self._accounts_to_dataframe(accounts)
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_csv(
        self, 
        accounts: List[AggregatedAccount], 
        filepath: str
    ) -> None:
        """
        Generate summary CSV file from aggregated accounts.
        
        Args:
            accounts: List of AggregatedAccount objects to export.
            filepath: Path where the CSV file should be saved.
        """
        df = self._accounts_to_dataframe(accounts)
        # Ensure account number is stored as string to preserve leading zeros
        if "Fraudster Bank Account Number" in df.columns:
            df["Fraudster Bank Account Number"] = df["Fraudster Bank Account Number"].astype(str)
        df.to_csv(filepath, index=False)
    
    def generate_csv_bytes(
        self, 
        accounts: List[AggregatedAccount]
    ) -> bytes:
        """
        Generate summary CSV file as bytes (for streaming downloads).
        
        Args:
            accounts: List of AggregatedAccount objects to export.
            
        Returns:
            CSV file content as bytes.
        """
        df = self._accounts_to_dataframe(accounts)
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        return buffer.getvalue().encode('utf-8')

    
    def generate_audit_log(
        self,
        input_filename: str,
        rows_processed: int,
        errors_encountered: List[str],
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Generate audit log content for a processing session.
        
        The audit log includes: timestamp, input filename, rows processed count,
        and any errors encountered during processing.
        
        Args:
            input_filename: Name of the input file that was processed.
            rows_processed: Number of rows that were processed.
            errors_encountered: List of error messages encountered during processing.
            timestamp: Processing timestamp (defaults to current time).
            
        Returns:
            Audit log content as a string.
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        log_lines = [
            "=" * 60,
            "FRAUD ANALYSIS PROCESSING AUDIT LOG",
            "=" * 60,
            "",
            f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Input File: {input_filename}",
            f"Rows Processed: {rows_processed}",
            "",
            "-" * 60,
            "ERRORS ENCOUNTERED",
            "-" * 60,
        ]
        
        if errors_encountered:
            for i, error in enumerate(errors_encountered, 1):
                log_lines.append(f"{i}. {error}")
        else:
            log_lines.append("No errors encountered during processing.")
        
        log_lines.extend([
            "",
            "-" * 60,
            "END OF AUDIT LOG",
            "-" * 60,
        ])
        
        return "\n".join(log_lines)
    
    def generate_audit_log_from_stats(
        self,
        stats: ProcessingStats,
        errors_encountered: Optional[List[str]] = None
    ) -> str:
        """
        Generate audit log content from ProcessingStats object.
        
        Args:
            stats: ProcessingStats object containing processing information.
            errors_encountered: Optional list of error messages.
            
        Returns:
            Audit log content as a string.
        """
        return self.generate_audit_log(
            input_filename=stats.input_filename,
            rows_processed=stats.rows_processed,
            errors_encountered=errors_encountered or [],
            timestamp=stats.processing_timestamp
        )

    
    def generate_pdf(
        self,
        accounts: List[AggregatedAccount],
        stats: ProcessingStats,
        filepath: str,
        quality_metrics: Optional[dict] = None
    ) -> None:
        """
        Generate PDF report with summary statistics, top 20 accounts table,
        data quality metrics, and processing timestamp.
        
        Args:
            accounts: List of AggregatedAccount objects (should be sorted).
            stats: ProcessingStats object with summary statistics.
            filepath: Path where the PDF file should be saved.
            quality_metrics: Optional dictionary with data quality metrics.
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        )
        
        # Create document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Build document content
        story = []
        
        # Title
        story.append(Paragraph("Fraud Analysis Report", title_style))
        story.append(Spacer(1, 0.25*inch))
        
        # Processing timestamp
        timestamp_str = stats.processing_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        story.append(Paragraph(f"Generated: {timestamp_str}", normal_style))
        story.append(Paragraph(f"Input File: {stats.input_filename}", normal_style))
        story.append(Spacer(1, 0.25*inch))
        
        # Summary Statistics Section
        story.append(Paragraph("Summary Statistics", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        summary_data = [
            ["Metric", "Value"],
            ["Total Input Rows", str(stats.total_input_rows)],
            ["Rows Processed", str(stats.rows_processed)],
            ["Rows with Errors", str(stats.rows_with_errors)],
            ["Unique Fraudster Accounts", str(stats.unique_accounts)],
            ["Total Fraud Amount", f"₹{stats.total_fraud_amount:,.2f}"],
            ["Total Disputed Amount", f"₹{stats.total_disputed_amount:,.2f}"],
            ["Average Amount per Account", f"₹{stats.average_amount_per_account:,.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.25*inch))
        
        # Data Quality Metrics Section (if provided)
        if quality_metrics:
            story.append(Paragraph("Data Quality Metrics", heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            quality_data = [["Metric", "Value"]]
            for key, value in quality_metrics.items():
                if isinstance(value, float):
                    quality_data.append([key, f"{value:.2%}"])
                else:
                    quality_data.append([key, str(value)])
            
            quality_table = Table(quality_data, colWidths=[3*inch, 3*inch])
            quality_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(quality_table)
            story.append(Spacer(1, 0.25*inch))
        
        # Top 20 Fraudster Accounts Section
        story.append(Paragraph("Top 20 Fraudster Accounts by Amount", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Get top 20 accounts
        top_accounts = accounts[:20] if len(accounts) > 20 else accounts
        
        if top_accounts:
            # Table headers
            table_data = [[
                "Account Number",
                "Bank Name",
                "IFSC Code",
                "Transactions",
                "Total Amount",
                "Risk Score"
            ]]
            
            # Add account rows
            for account in top_accounts:
                table_data.append([
                    account.account_number,
                    account.bank_name[:20] + "..." if len(account.bank_name) > 20 else account.bank_name,
                    account.ifsc_code,
                    str(account.total_transactions),
                    f"₹{account.total_amount:,.2f}",
                    f"{account.risk_score:.1f}"
                ])
            
            # Create table with column widths
            col_widths = [1.8*inch, 1.5*inch, 1.2*inch, 1*inch, 1.5*inch, 0.8*inch]
            accounts_table = Table(table_data, colWidths=col_widths)
            accounts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Transactions column
                ('ALIGN', (4, 1), (4, -1), 'RIGHT'),   # Amount column
                ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Risk score column
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            story.append(accounts_table)
        else:
            story.append(Paragraph("No accounts to display.", normal_style))
        
        # Build PDF
        doc.build(story)

    
    def generate_pdf_bytes(
        self,
        accounts: List[AggregatedAccount],
        stats: ProcessingStats,
        quality_metrics: Optional[dict] = None
    ) -> bytes:
        """
        Generate PDF report as bytes (for streaming downloads).
        
        Args:
            accounts: List of AggregatedAccount objects (should be sorted).
            stats: ProcessingStats object with summary statistics.
            quality_metrics: Optional dictionary with data quality metrics.
            
        Returns:
            PDF file content as bytes.
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        )
        
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Build document content
        story = []
        
        # Title
        story.append(Paragraph("Fraud Analysis Report", title_style))
        story.append(Spacer(1, 0.25*inch))
        
        # Processing timestamp
        timestamp_str = stats.processing_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        story.append(Paragraph(f"Generated: {timestamp_str}", normal_style))
        story.append(Paragraph(f"Input File: {stats.input_filename}", normal_style))
        story.append(Spacer(1, 0.25*inch))
        
        # Summary Statistics Section
        story.append(Paragraph("Summary Statistics", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        summary_data = [
            ["Metric", "Value"],
            ["Total Input Rows", str(stats.total_input_rows)],
            ["Rows Processed", str(stats.rows_processed)],
            ["Rows with Errors", str(stats.rows_with_errors)],
            ["Unique Fraudster Accounts", str(stats.unique_accounts)],
            ["Total Fraud Amount", f"₹{stats.total_fraud_amount:,.2f}"],
            ["Total Disputed Amount", f"₹{stats.total_disputed_amount:,.2f}"],
            ["Average Amount per Account", f"₹{stats.average_amount_per_account:,.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.25*inch))
        
        # Data Quality Metrics Section (if provided)
        if quality_metrics:
            story.append(Paragraph("Data Quality Metrics", heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            quality_data = [["Metric", "Value"]]
            for key, value in quality_metrics.items():
                if isinstance(value, float):
                    quality_data.append([key, f"{value:.2%}"])
                else:
                    quality_data.append([key, str(value)])
            
            quality_table = Table(quality_data, colWidths=[3*inch, 3*inch])
            quality_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(quality_table)
            story.append(Spacer(1, 0.25*inch))
        
        # Top 20 Fraudster Accounts Section
        story.append(Paragraph("Top 20 Fraudster Accounts by Amount", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Get top 20 accounts
        top_accounts = accounts[:20] if len(accounts) > 20 else accounts
        
        if top_accounts:
            # Table headers
            table_data = [[
                "No.",
                "Account Number",
                "Bank Name",
                "IFSC Code",
                "Transactions",
                "Total Amount",
                "Risk Score"
            ]]
            
            # Add account rows
            for i, account in enumerate(top_accounts, 1):
                table_data.append([
                    str(i),
                    account.account_number,
                    account.bank_name[:25] + "..." if len(account.bank_name) > 25 else account.bank_name,
                    account.ifsc_code,
                    str(account.total_transactions),
                    f"₹{account.total_amount:,.2f}",
                    f"{account.risk_score:.1f}"
                ])
            
            # Create table with column widths
            col_widths = [0.4*inch, 1.8*inch, 2.2*inch, 1.2*inch, 1*inch, 1.5*inch, 0.8*inch]
            accounts_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Define professional colors
            primary_color = colors.HexColor("#1A237E") # Deep Indigo
            header_text = colors.whitesmoke
            row_even = colors.HexColor("#F5F5F5")
            row_odd = colors.white
            border_color = colors.HexColor("#BDBDBD")
            
            accounts_table.setStyle(TableStyle([
                # Header Style
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), header_text),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                
                # Content Style
                ('ALIGN', (0, 1), (0, -1), 'CENTER'), # No.
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),   # Account
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),   # Bank
                ('ALIGN', (3, 1), (3, -1), 'CENTER'), # IFSC
                ('ALIGN', (4, 1), (4, -1), 'CENTER'), # Txns
                ('ALIGN', (5, 1), (5, -1), 'RIGHT'),  # Amount
                ('ALIGN', (6, 1), (6, -1), 'CENTER'), # Risk
                
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Alternating Row Colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [row_odd, row_even]),
                
                # Borders
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor("#0D47A1")), # Thick line below header
            ]))
            story.append(accounts_table)
        else:
            story.append(Paragraph("No accounts to display.", normal_style))
        
        # Build PDF
        doc.build(story)
        
        buffer.seek(0)
        return buffer.getvalue()
