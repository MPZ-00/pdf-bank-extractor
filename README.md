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

### Option 1: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Global Installation

```bash
# Install dependencies globally
pip install -r requirements.txt
```

**Note:** Using a virtual environment is recommended to avoid conflicts with other Python projects.

## Usage

**Note:** If using a virtual environment, make sure it's activated before running commands.

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

### Check version
```bash
python main.py --version
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

## Binary Releases

Pre-built executables are available for download from the [Releases](https://github.com/MPZ-00/pdf-bank-extractor/releases) page:

- **Windows**: `pdf-bank-extractor-windows-x64.exe`
- **Linux**: `pdf-bank-extractor-linux-x64`
- **macOS**: `pdf-bank-extractor-macos-x64`

Each release includes SHA256 hash files for integrity verification.

### Using Pre-built Executables

```bash
# Windows
.\pdf-bank-extractor-windows-x64.exe -f statement.pdf

# Linux/macOS (make executable first)
chmod +x pdf-bank-extractor-linux-x64
./pdf-bank-extractor-linux-x64 -f statement.pdf
```

## Building from Source

### Prerequisites
- Python 3.7+
- pip

### Build Executable

The build scripts automatically create and manage a virtual environment for you:

```bash
# Windows
build.bat

# Linux/macOS
chmod +x build.sh
./build.sh
```

**Manual build process:**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Build executable
pyinstaller --onefile --name pdf-bank-extractor --clean main.py

# Deactivate when done
deactivate
```

This creates a single executable file in the `dist/` directory with SHA256 hash verification.

## TODO

- [ ] Add configuration file support for customizable regex patterns
- [ ] Implement comprehensive testing suite
- [ ] Extend regex patterns to support more bank formats
- [ ] Add support for different date formats
- [ ] Improve PDF text extraction for complex layouts

## License

MIT License - see [LICENSE](LICENSE) file for details.

This project is provided "as-is" without warranty of any kind.
