# PDF Bank Statement Extractor

A Python utility to extract transaction data (dates and amounts) from bank statement PDFs and export them to CSV format.

## Features

- Extract transaction dates and amounts from PDF bank statements
- Process single PDF files or entire directories recursively
- Export data to CSV format with customizable delimiter
- Optional filename inclusion in output
- Automatic stopping at specific keywords (e.g., "Zinsertrag", "Neuer Saldo")

## Requirements

- Python 3.7+
- pdfplumber library for PDF text extraction

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Extract from a single PDF file
```bash
python main.py -f statement.pdf
```

### Extract from all PDFs in a directory (recursive)
```bash
python main.py -d /path/to/pdf/directory
```

### Specify custom output file
```bash
python main.py -f statement.pdf -o my_transactions.csv
```

### Include filename in output
```bash
python main.py -d /path/to/pdfs --add-filename
```

## Command Line Options

- `-f, --file`: Process a single PDF file
- `-d, --dir`: Process all PDF files in a directory (recursive)
- `-o, --out`: Specify output CSV file (default: `auszuege.csv`)
- `--add-filename`: Include the source filename in the CSV output

## Output Format

The generated CSV file contains the following columns:
- **Datum**: Transaction date (DD.MM.YYYY format)
- **Betrag**: Transaction amount (German number format with comma as decimal separator)
- **Datei**: Source filename (only when `--add-filename` is used)

## How It Works

The tool uses regular expressions to identify:
- **Dates**: Lines starting with DD.MM.YYYY format
- **Amounts**: Numbers in German format (e.g., 1.234,56 or -123,45)
- **Stop conditions**: Processing stops when encountering "Zinsertrag" or "Neuer Saldo"

## Example

```bash
python main.py -d bank_statements/ --add-filename -o transactions_2024.csv
```

This will:
1. Process all PDF files in the `bank_statements/` directory
2. Include filenames in the output
3. Save results to `transactions_2024.csv`

## License

This project is provided as-is for educational and personal use.
