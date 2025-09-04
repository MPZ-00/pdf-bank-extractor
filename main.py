#!/usr/bin/env python3
"""PDF Bank Statement Extractor

A Python utility to extract transaction data from German bank statement PDFs.
"""
import argparse
import csv
import re
import sys
import io
from pathlib import Path

import pdfplumber

__version__ = "0.1.0"
__author__ = "MPZ-00"

# Regex patterns for table extraction
HEADER_RE = re.compile(r"(Buchungstag|Valuta|Vorgang|Referenz|Auftraggeber|Empfänger|IBAN|BIC|Buchungstext|Ausgang|Eingang)", re.IGNORECASE)
DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")
AMOUNT_RE = re.compile(r"[-+]?\d{1,3}(?:\.\d{3})*,\d{2}\s*€?")
STOP_RE = re.compile(r"(Zinsertrag|Neuer Saldo)")
IBAN_RE = re.compile(r"[A-Z]{2}\d{18}")
BIC_RE = re.compile(r"[A-Z]{8,11}")
TRANSACTION_TYPE_RE = re.compile(r"(Lastschrift|Überweisung|Gutschrift|Belastung|Dauerauftrag)", re.IGNORECASE)

def extract_from_pdf(pdf_path: Path):
    """Extract full table data from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of transaction rows with all columns
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        PermissionError: If PDF file can't be accessed
        Exception: For other PDF processing errors
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    
    rows = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                print(f"Warning: PDF file appears to be empty: {pdf_path}", file=sys.stderr)
                return rows
                
            for page in pdf.pages:
                page_rows = []
                
                # First try to extract tables directly
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            if row and len(row) >= 4:  # At least 4 columns expected (corrected structure)
                                # Check if this is a data row (has date and amount)
                                row_text = " ".join(str(cell) if cell else "" for cell in row)
                                if DATE_RE.search(row_text) and AMOUNT_RE.search(row_text):
                                    # Clean and format the row
                                    clean_row = []
                                    for cell in row[:5]:  # Take first 5 columns (corrected structure)
                                        clean_row.append(str(cell).strip() if cell else "")
                                    page_rows.append(clean_row)
                
                # Fallback: extract from text if no tables found on this page
                if not page_rows:
                    try:
                        text = page.extract_text() or ""
                    except Exception as e:
                        print(f"Warning: Could not extract text from page in {pdf_path}: {e}", file=sys.stderr)
                        continue
                    
                    lines = text.splitlines()
                    current_transaction = None
                    
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if STOP_RE.search(line):
                            break
                        
                        # Check if this line starts a new transaction (has date and amount)
                        if DATE_RE.search(line) and AMOUNT_RE.search(line):
                            # Save previous transaction if exists
                            if current_transaction:
                                page_rows.append(current_transaction)
                            
                            # Start new transaction
                            date_match = DATE_RE.search(line)
                            date = date_match.group() if date_match else ""
                            
                            # Extract amount (last amount found)
                            amount_matches = list(AMOUNT_RE.finditer(line))
                            amount = amount_matches[-1].group() if amount_matches else ""
                            
                            # Extract transaction type (Vorgang Referenz combined)
                            vorgang_referenz = ""
                            transaction_type_match = TRANSACTION_TYPE_RE.search(line)
                            if transaction_type_match:
                                # Find the full transaction type description
                                type_start = transaction_type_match.start()
                                # Look for the part between transaction type and amount
                                amount_start = amount_matches[-1].start() if amount_matches else len(line)
                                vorgang_referenz = line[type_start:amount_start].strip()
                            
                            # Try to extract sender/recipient info
                            auftraggeber = ""
                            remaining_text = line
                            # Remove already extracted parts
                            for pattern in [date, amount, vorgang_referenz]:
                                if pattern:
                                    remaining_text = remaining_text.replace(pattern, "", 1)
                            
                            # Clean up remaining text for sender info
                            auftraggeber = remaining_text.strip()
                            
                            current_transaction = [
                                date,  # Buchungstag/Valuta
                                vorgang_referenz,  # Vorgang Referenz (combined)
                                auftraggeber,  # Auftraggeber/Empfänger,IBAN/BIC
                                "",  # Buchungstext (will be filled from next lines)
                                amount  # Ausgang/Eingang
                            ]
                            
                        elif current_transaction and line:
                            # This might be additional buchungstext for the current transaction
                            # Append to buchungstext field (index 3)
                            if current_transaction[3]:
                                current_transaction[3] += " " + line
                            else:
                                current_transaction[3] = line
                    
                    # Don't forget the last transaction
                    if current_transaction:
                        page_rows.append(current_transaction)
                
                # Add all rows from this page to the total
                rows.extend(page_rows)
                        
    except PermissionError:
        raise PermissionError(f"Permission denied accessing PDF file: {pdf_path}")
    except Exception as e:
        if "password" in str(e).lower():
            raise Exception(f"PDF file appears to be password-protected: {pdf_path}")
        else:
            raise Exception(f"Error processing PDF file {pdf_path}: {e}")
    
    return rows

def collect_files(file: Path | None, folder: Path | None):
    """Collect PDF files from specified file or folder.
    
    Args:
        file: Single PDF file path
        folder: Folder to search for PDFs recursively
        
    Returns:
        List of valid PDF file paths
        
    Raises:
        FileNotFoundError: If specified file/folder doesn't exist
        PermissionError: If folder can't be accessed
    """
    files = []
    
    if file:
        if not file.exists():
            raise FileNotFoundError(f"File not found: {file}")
        if file.suffix.lower() != ".pdf":
            raise ValueError(f"File is not a PDF: {file}")
        if not file.is_file():
            raise ValueError(f"Path is not a file: {file}")
        files.append(file)
        
    if folder:
        if not folder.exists():
            raise FileNotFoundError(f"Directory not found: {folder}")
        if not folder.is_dir():
            raise ValueError(f"Path is not a directory: {folder}")
            
        try:
            pdf_files = list(folder.rglob("*.pdf"))
            valid_files = [p for p in pdf_files if p.is_file()]
            files.extend(sorted(valid_files))
        except PermissionError:
            raise PermissionError(f"Permission denied accessing directory: {folder}")
        except Exception as e:
            raise Exception(f"Error scanning directory {folder}: {e}")
    
    return files

def main():
    p = argparse.ArgumentParser(
        description="Extracts full table data from bank statement PDFs into a CSV and optionally outputs markdown.",
        epilog=f"PDF Bank Statement Extractor v{__version__} by {__author__}"
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("-f", "--file", type=Path, help="Single PDF file")
    src.add_argument("-d", "--dir",  type=Path, help="Folder with PDFs, recursive")
    p.add_argument("-o", "--out", type=Path, default=Path("auszuege.csv"),
                   help="Output CSV path, default: auszuege.csv")
    p.add_argument("--add-filename", action="store_true",
                   help="Include filename in output")
    p.add_argument("--markdown", type=Path, nargs="?", const="-", default=None,
                   help="Output markdown table to file (or '-' for stdout)")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = p.parse_args()
    
    try:
        files = collect_files(args.file, args.dir)
    except (FileNotFoundError, ValueError, PermissionError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error collecting files: {e}", file=sys.stderr)
        sys.exit(1)
        
    if not files:
        print("Error: No valid PDF files found.", file=sys.stderr)
        sys.exit(1)

    # Check if output directory exists and is writable
    output_dir = args.out.parent
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True)
        except PermissionError:
            print(f"Error: Cannot create output directory: {output_dir}", file=sys.stderr)
            sys.exit(1)
    
    # Column headers matching corrected structure
    out_fields = [
        "Buchungstag/Valuta", "Vorgang Referenz", 
        "Auftraggeber/Empfänger,IBAN/BIC", "Buchungstext", "Ausgang/Eingang"
    ]
    if args.add_filename:
        out_fields.append("Datei")

    failed_files = []
    total = 0
    all_rows = []
    
    try:
        with args.out.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh, delimiter=";")
            writer.writerow(out_fields)

            for pdf in files:
                try:
                    rows = extract_from_pdf(pdf)
                    if not rows:
                        print(f"Warning: No transactions found in {pdf}", file=sys.stderr)
                        continue
                        
                    for row in rows:
                        # Ensure we have 5 columns (corrected structure)
                        while len(row) < 5:
                            row.append("")
                        
                        out_row = row[:5]  # Take first 5 columns
                        if args.add_filename:
                            out_row.append(str(pdf))
                        
                        writer.writerow(out_row)
                        all_rows.append(out_row)
                        total += 1
                        
                except Exception as e:
                    failed_files.append((pdf, str(e)))
                    print(f"Error processing {pdf}: {e}", file=sys.stderr)
                    continue

    except PermissionError:
        print(f"Error: Cannot write to output file: {args.out}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate markdown output if requested
    if args.markdown is not None:
        md_fields = out_fields
        md = io.StringIO()
        md.write("| " + " | ".join(md_fields) + " |\n")
        md.write("| " + " | ".join(["---"] * len(md_fields)) + " |\n")
        for row in all_rows:
            # Escape pipe characters in cells
            escaped_row = [str(cell).replace("|", "\\|") for cell in row]
            md.write("| " + " | ".join(escaped_row) + " |\n")
        
        md_content = md.getvalue()
        
        if args.markdown == Path("-") or str(args.markdown) == "-":
            print("\n" + md_content)
        else:
            try:
                with args.markdown.open("w", encoding="utf-8") as mdfile:
                    mdfile.write(md_content)
                print(f"Markdown table written to: {args.markdown}")
            except Exception as e:
                print(f"Error writing markdown file: {e}", file=sys.stderr)

    # Summary
    successful_files = len(files) - len(failed_files)
    print(f"Done. {total} transactions from {successful_files}/{len(files)} file(s) → {args.out}")
    
    if failed_files:
        print(f"\nFailed to process {len(failed_files)} file(s):", file=sys.stderr)
        for pdf, error in failed_files:
            print(f"  {pdf}: {error}", file=sys.stderr)

if __name__ == "__main__":
    main()
