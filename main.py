#!/usr/bin/env python3
import argparse
import csv
import re
from pathlib import Path

import pdfplumber

DATE_RE   = re.compile(r"^(\d{2}\.\d{2}\.\d{4})")
AMOUNT_RE = re.compile(r"[-+]?\d{1,3}(?:\.\d{3})*,\d{2}")

def extract_from_pdf(pdf_path: Path):
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                m_date = DATE_RE.match(line)
                m_amount = AMOUNT_RE.search(line)
                if m_date and m_amount:
                    rows.append((m_date.group(1), m_amount.group(0)))
    return rows

def collect_files(file: Path | None, folder: Path | None):
    files = []
    if file:
        if file.suffix.lower() == ".pdf" and file.is_file():
            files.append(file)
    if folder:
        files.extend(sorted(p for p in folder.rglob("*.pdf") if p.is_file()))
    return files

def main():
    p = argparse.ArgumentParser(
        description="Extrahiert Datum und Betrag aus Kontoauszug-PDFs in eine CSV."
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("-f", "--file", type=Path, help="Einzelne PDF-Datei")
    src.add_argument("-d", "--dir",  type=Path, help="Ordner mit PDFs, rekursiv")
    p.add_argument("-o", "--out", type=Path, default=Path("auszuege.csv"),
                   help="Pfad zur Ausgabe-CSV, Standard: auszuege.csv")
    p.add_argument("--add-filename", action="store_true",
                   help="Dateiname als zusätzliche Spalte ausgeben")

    args = p.parse_args()

    files = collect_files(args.file, args.dir)
    if not files:
        raise SystemExit("Keine PDF-Dateien gefunden.")

    out_fields = ["Datum", "Betrag"]
    if args.add_filename:
        out_fields.append("Datei")

    with args.out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow(out_fields)

        total = 0
        for pdf in files:
            rows = extract_from_pdf(pdf)
            for d, a in rows:
                if args.add_filename:
                    writer.writerow([d, a, str(pdf)])
                else:
                    writer.writerow([d, a])
                total += 1

    print(f"Fertig. {total} Buchungen aus {len(files)} Datei(en) → {args.out}")

if __name__ == "__main__":
    main()
