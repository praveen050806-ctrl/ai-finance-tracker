# AI Finance Tracker

A Flask web app for tracking personal income and expenses, with automatic
transaction categorization, budget tracking, and rule-based spending
insights — no external AI API key required, all data stored locally in
SQLite.

## What it does

- **Add transactions** manually, or **import a CSV** exported from your bank.
- **Auto-categorizes** expenses using keyword matching (e.g. "Starbucks" →
  Food & Dining, "Netflix" → Subscriptions).
- **Dashboard** with income/expense/net/savings-rate summary and a
  category spending breakdown for any month.
- **Budgets**: set a monthly limit per category and see spend-vs-limit at a glance.
- **Insights**: plain-English notes generated from your data —
  month-over-month spending changes, over-budget categories, detected
  recurring/subscription payments, and savings-rate commentary.

## Project structure

```
ai-finance-tracker/
├── app.py               # Flask routes
├── db.py                  # SQLite schema + CRUD (no ORM)
├── categorizer.py           # Keyword-based auto-categorization
├── csv_import.py              # Bank CSV parsing (flexible column names)
├── insights.py                  # Summaries, budgets, recurring-payment detection
├── requirements.txt
├── templates/
│   ├── index.html                 # Dashboard
│   ├── transactions.html            # List + add-transaction form
│   ├── upload.html                    # CSV import
│   └── budgets.html                     # Budget management
├── static/style.css
├── data/                    # SQLite database lives here (gitignored)
└── README.md
```

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/<your-username>/ai-finance-tracker.git
   cd ai-finance-tracker
   ```

2. **Create a virtual environment (recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**

   ```bash
   python app.py
   ```

5. Open **http://127.0.0.1:5000**. The SQLite database (`data/finance.db`)
   is created automatically on first run.

## How it works

- **Storage** (`db.py`): plain `sqlite3`, two tables — `transactions` and
  `budgets`. No ORM, so there's nothing extra to install or configure.
- **Categorization** (`categorizer.py`): a keyword dictionary maps common
  merchant/description terms to categories (Groceries, Food & Dining,
  Transport, Subscriptions, etc.) — easy to extend for your own spending habits.
- **CSV import** (`csv_import.py`): tolerant of different bank export
  formats — recognizes several common column names for date/description/
  amount, or separate debit/credit columns.
- **Insights** (`insights.py`): all rule-based —
  - Savings rate = (income − expenses) / income
  - Month-over-month expense comparison
  - Recurring payment detection: same description + similar amount seen
    in 2+ different months
  - Budget-vs-actual comparison per category

## Extending this project

- Plug in the Anthropic API to turn the raw `insights.generate_insights()`
  data into a more conversational monthly summary, or to answer freeform
  questions about your spending.
- Add multi-user support with authentication.
- Add data visualization with Chart.js for trend lines over time.
- Support multiple accounts/currencies.
- Add an "export to CSV" for tax season.
- Bank API integration (e.g. Plaid) for automatic transaction syncing
  instead of manual CSV export/import.

## License

MIT — feel free to use this project as a portfolio piece or a starting point
for something bigger.
