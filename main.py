#!/usr/bin/env python3
"""PDF Bank Statement Extractor

A Python utility to extract transaction data from German bank statement PDFs.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import pdfplumber

__version__ = "0.1.0"
__author__ = "MPZ-00"

DATE_RE   = re.compile(r"^(\d{2}\.\d{2}\.\d{4})")
AMOUNT_RE = re.compile(r"[-+]?\d{1,3}(?:\.\d{3})*,\d{2}")
STOP_RE = re.compile(r"(Zinsertrag|Neuer Saldo)")

def extract_from_pdf(pdf_path: Path):
    """Extract date and amount pairs from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of (date, amount) tuples
        
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
    stop = False
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                print(f"Warning: PDF file appears to be empty: {pdf_path}", file=sys.stderr)
                return rows
                
            for page in pdf.pages:
                if stop:
                    break
                    
                try:
                    text = page.extract_text() or ""
                except Exception as e:
                    print(f"Warning: Could not extract text from page in {pdf_path}: {e}", file=sys.stderr)
                    continue
                    
                for line in text.splitlines():
                    line = line.strip()
                    if STOP_RE.search(line):
                        stop = True
                        break
                    m_date = DATE_RE.match(line)
                    m_amount = AMOUNT_RE.search(line)
                    if m_date and m_amount:
                        rows.append((m_date.group(1), m_amount.group(0)))
                        
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
        description="Extracts date and amount from bank statement PDFs into a CSV.",
        epilog=f"PDF Bank Statement Extractor v{__version__} by {__author__}"
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("-f", "--file", type=Path, help="Single PDF file")
    src.add_argument("-d", "--dir",  type=Path, help="Folder with PDFs, recursive")
    p.add_argument("-o", "--out", type=Path, default=Path("auszuege.csv"),
                   help="Output CSV path, default: auszuege.csv")
    p.add_argument("--add-filename", action="store_true",
                   help="Include filename in output")
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
    
    out_fields = ["Datum", "Betrag"]
    if args.add_filename:
        out_fields.append("Datei")

    failed_files = []
    total = 0
    
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
                        
                    for d, a in rows:
                        if args.add_filename:
                            writer.writerow([d, a, str(pdf)])
                        else:
                            writer.writerow([d, a])
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

    # Summary
    successful_files = len(files) - len(failed_files)
    print(f"Done. {total} transactions from {successful_files}/{len(files)} file(s) → {args.out}")
    
    if failed_files:
        print(f"\nFailed to process {len(failed_files)} file(s):", file=sys.stderr)
        for pdf, error in failed_files:
            print(f"  {pdf}: {error}", file=sys.stderr)

if __name__ == "__main__":
    main()
