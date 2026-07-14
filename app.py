"""
app.py
-------
Flask web application for the AI Finance Tracker.

Routes:
  GET  /                       -> dashboard (summary, breakdown, insights)
  GET  /transactions             -> list + add-transaction form
  POST /transactions/add           -> add a manual transaction
  POST /transactions/<id>/delete     -> delete a transaction
  GET  /upload                         -> CSV import form
  POST /upload                           -> parse + bulk-insert a CSV
  GET  /budgets                            -> view/set category budgets
  POST /budgets/set                          -> set a budget for a category
  POST /budgets/<category>/delete              -> remove a budget

Run locally with:
    python app.py
Then open http://127.0.0.1:5000
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

import db
import insights
from categorizer import categorize, get_all_categories
from csv_import import parse_csv, CSVImportError

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

db.init_db()


@app.route("/", methods=["GET"])
def index():
    month = request.args.get("month") or insights.current_month()
    summary = insights.monthly_summary(month)
    breakdown = insights.category_breakdown(month)
    notes = insights.generate_insights(month)
    months = db.get_all_months()
    if month not in months:
        months = sorted(months + [month], reverse=True)

    return render_template(
        "index.html",
        summary=summary,
        breakdown=breakdown,
        notes=notes,
        months=months,
        selected_month=month,
    )


@app.route("/transactions", methods=["GET"])
def transactions():
    month = request.args.get("month")
    rows = db.get_transactions(month=month)
    months = db.get_all_months()
    categories = get_all_categories()
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template(
        "transactions.html",
        rows=rows,
        months=months,
        selected_month=month,
        categories=categories,
        today=today,
    )


@app.route("/transactions/add", methods=["POST"])
def add_transaction():
    date = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()
    amount_raw = request.form.get("amount", "").strip()
    txn_type = request.form.get("txn_type", "expense")
    category_override = request.form.get("category", "").strip()

    if not date or not description or not amount_raw:
        flash("Please fill in date, description, and amount.")
        return redirect(url_for("transactions"))

    try:
        amount = abs(float(amount_raw))
    except ValueError:
        flash("Amount must be a number.")
        return redirect(url_for("transactions"))

    if txn_type == "income":
        category = "Income"
    else:
        category = category_override or categorize(description)

    db.add_transaction(date, description, category, amount, txn_type)
    flash(f"Added: {description} (${amount:.2f}, {category})")
    return redirect(url_for("transactions"))


@app.route("/transactions/<int:txn_id>/delete", methods=["POST"])
def delete_transaction(txn_id):
    db.delete_transaction(txn_id)
    flash("Transaction deleted.")
    return redirect(url_for("transactions"))


@app.route("/upload", methods=["GET"])
def upload():
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload_submit():
    if "csv_file" not in request.files or request.files["csv_file"].filename == "":
        flash("Please choose a CSV file to upload.")
        return redirect(url_for("upload"))

    file = request.files["csv_file"]

    try:
        parsed, skipped = parse_csv(file.stream)
    except CSVImportError as e:
        flash(str(e))
        return redirect(url_for("upload"))

    rows = [
        (t["date"], t["description"], t["category"], t["amount"], t["txn_type"])
        for t in parsed
    ]
    db.add_transactions_bulk(rows)

    msg = f"Imported {len(rows)} transaction(s)."
    if skipped:
        msg += f" Skipped {skipped} row(s) that couldn't be parsed."
    flash(msg)
    return redirect(url_for("transactions"))


@app.route("/budgets", methods=["GET"])
def budgets():
    month = insights.current_month()
    status = insights.budget_status(month)
    budgeted_categories = {b["category"] for b in status}
    available_categories = [c for c in get_all_categories() if c not in budgeted_categories and c != "Income"]
    return render_template(
        "budgets.html", status=status, available_categories=available_categories, month=month
    )


@app.route("/budgets/set", methods=["POST"])
def set_budget():
    category = request.form.get("category", "").strip()
    limit_raw = request.form.get("monthly_limit", "").strip()

    if not category or not limit_raw:
        flash("Please choose a category and enter a limit.")
        return redirect(url_for("budgets"))

    try:
        limit = abs(float(limit_raw))
    except ValueError:
        flash("Budget limit must be a number.")
        return redirect(url_for("budgets"))

    db.set_budget(category, limit)
    flash(f"Budget set: {category} — ${limit:.2f}/month")
    return redirect(url_for("budgets"))


@app.route("/budgets/<category>/delete", methods=["POST"])
def delete_budget(category):
    db.delete_budget(category)
    flash(f"Removed budget for {category}.")
    return redirect(url_for("budgets"))


if __name__ == "__main__":
    app.run(debug=True)
