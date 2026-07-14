"""
csv_import.py
---------------
Parses an uploaded CSV (e.g. exported from a bank) into transaction
rows ready for insertion into the database. Tries to be forgiving
about column naming, since every bank exports slightly differently.

Expected/recognized columns (case-insensitive, first match wins):
  date:        "date", "transaction date", "posted date"
  description: "description", "desc", "memo", "narration", "details"
  amount:      "amount", "debit", "credit", "value"

Convention: a negative amount (or a value in a "Debit" column) is
treated as an expense; a positive amount (or a value in a "Credit"
column) is treated as income.
"""

import csv
import io
from datetime import datetime

from categorizer import categorize

DATE_COLUMNS = ["date", "transaction date", "posted date", "trans date"]
DESC_COLUMNS = ["description", "desc", "memo", "narration", "details", "payee"]
AMOUNT_COLUMNS = ["amount", "value"]
DEBIT_COLUMNS = ["debit", "withdrawal"]
CREDIT_COLUMNS = ["credit", "deposit"]

DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y"]


class CSVImportError(Exception):
    pass


def _find_column(fieldnames, candidates):
    lower_map = {f.lower().strip(): f for f in fieldnames}
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def _parse_date(value):
    value = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _parse_amount(value):
    if value is None:
        return None
    value = value.replace("$", "").replace(",", "").strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_csv(file_stream):
    """
    Parse an uploaded CSV file into a list of transaction dicts:
        {"date": "YYYY-MM-DD", "description": str, "category": str,
         "amount": float (positive), "txn_type": "income"|"expense"}

    Raises CSVImportError with a human-readable message on failure.
    """
    text = file_stream.read().decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise CSVImportError("Could not read a header row from this CSV.")

    date_col = _find_column(reader.fieldnames, DATE_COLUMNS)
    desc_col = _find_column(reader.fieldnames, DESC_COLUMNS)
    amount_col = _find_column(reader.fieldnames, AMOUNT_COLUMNS)
    debit_col = _find_column(reader.fieldnames, DEBIT_COLUMNS)
    credit_col = _find_column(reader.fieldnames, CREDIT_COLUMNS)

    if not date_col or not desc_col:
        raise CSVImportError(
            "Couldn't find recognizable date/description columns. "
            f"Columns found: {', '.join(reader.fieldnames)}"
        )
    if not amount_col and not (debit_col or credit_col):
        raise CSVImportError(
            "Couldn't find an amount column (or debit/credit columns). "
            f"Columns found: {', '.join(reader.fieldnames)}"
        )

    transactions = []
    skipped = 0

    for row in reader:
        date_str = _parse_date(row.get(date_col, ""))
        description = (row.get(desc_col) or "").strip()

        if amount_col:
            amount = _parse_amount(row.get(amount_col))
            if amount is None:
                skipped += 1
                continue
            txn_type = "income" if amount >= 0 else "expense"
        else:
            debit = _parse_amount(row.get(debit_col)) if debit_col else None
            credit = _parse_amount(row.get(credit_col)) if credit_col else None
            if credit:
                amount, txn_type = credit, "income"
            elif debit:
                amount, txn_type = debit, "expense"
            else:
                skipped += 1
                continue

        if not date_str or not description:
            skipped += 1
            continue

        category = "Income" if txn_type == "income" else categorize(description)

        transactions.append({
            "date": date_str,
            "description": description,
            "category": category,
            "amount": abs(amount),
            "txn_type": txn_type,
        })

    if not transactions:
        raise CSVImportError("No valid transaction rows could be parsed from this file.")

    return transactions, skipped
