"""
insights.py
-------------
Rule-based analysis over the transactions in the database: monthly
summaries, category breakdowns, budget tracking, recurring-payment
detection, and plain-English suggestions. No external AI call needed —
everything here is transparent arithmetic and heuristics.
"""

from collections import defaultdict
from datetime import datetime

import db
from categorizer import is_income_category


def current_month():
    return datetime.now().strftime("%Y-%m")


def monthly_summary(month=None):
    month = month or current_month()
    rows = db.get_transactions(month=month)

    income = sum(r["amount"] for r in rows if r["txn_type"] == "income")
    expense = sum(r["amount"] for r in rows if r["txn_type"] == "expense")
    net = income - expense
    savings_rate = round(100 * net / income, 1) if income > 0 else None

    return {
        "month": month,
        "income": round(income, 2),
        "expense": round(expense, 2),
        "net": round(net, 2),
        "savings_rate": savings_rate,
        "num_transactions": len(rows),
    }


def category_breakdown(month=None):
    """Expense-only breakdown by category, sorted by spend descending."""
    month = month or current_month()
    rows = db.get_transactions(month=month)
    expense_rows = [r for r in rows if r["txn_type"] == "expense"]

    totals = defaultdict(float)
    for r in expense_rows:
        totals[r["category"]] += r["amount"]

    total_expense = sum(totals.values())
    breakdown = [
        {
            "category": cat,
            "total": round(amount, 2),
            "percent": round(100 * amount / total_expense, 1) if total_expense else 0,
        }
        for cat, amount in totals.items()
    ]
    breakdown.sort(key=lambda x: x["total"], reverse=True)
    return breakdown


def month_over_month(month=None):
    """Compare this month's expenses to the previous month's."""
    month = month or current_month()
    months = db.get_all_months()
    if month not in months:
        months = sorted(months + [month], reverse=True)

    idx = months.index(month)
    if idx + 1 >= len(months):
        return None  # no previous month to compare against

    prev_month = months[idx + 1]
    current = monthly_summary(month)["expense"]
    previous = monthly_summary(prev_month)["expense"]

    if previous == 0:
        return None

    change_percent = round(100 * (current - previous) / previous, 1)
    return {
        "current_month": month,
        "previous_month": prev_month,
        "current_expense": current,
        "previous_expense": previous,
        "change_percent": change_percent,
    }


def detect_recurring(min_months=2):
    """
    Detect likely recurring/subscription payments: same description (or a
    close variant) and a similar amount appearing in 2+ different months.
    """
    rows = db.get_transactions()
    expense_rows = [r for r in rows if r["txn_type"] == "expense"]

    groups = defaultdict(list)
    for r in expense_rows:
        key = (r["description"].strip().lower(), round(r["amount"]))
        groups[key].append(r)

    recurring = []
    for (desc, amount), items in groups.items():
        months_seen = {r["date"][:7] for r in items}
        if len(months_seen) >= min_months:
            recurring.append({
                "description": items[0]["description"],
                "amount": amount,
                "months_seen": len(months_seen),
                "category": items[0]["category"],
            })

    recurring.sort(key=lambda x: x["amount"], reverse=True)
    return recurring


def budget_status(month=None):
    """For each budgeted category, compare actual spend to the monthly limit."""
    month = month or current_month()
    budgets = db.get_budgets()
    breakdown = {b["category"]: b["total"] for b in category_breakdown(month)}

    status = []
    for category, limit in budgets.items():
        spent = breakdown.get(category, 0)
        percent = round(100 * spent / limit, 1) if limit > 0 else 0
        status.append({
            "category": category,
            "limit": limit,
            "spent": spent,
            "percent": percent,
            "over_budget": spent > limit,
            "remaining": round(limit - spent, 2),
        })

    status.sort(key=lambda x: x["percent"], reverse=True)
    return status


def generate_insights(month=None):
    """Build a list of plain-English observations for the dashboard."""
    month = month or current_month()
    summary = monthly_summary(month)
    breakdown = category_breakdown(month)
    mom = month_over_month(month)
    recurring = detect_recurring()
    budgets = budget_status(month)

    notes = []

    if summary["num_transactions"] == 0:
        notes.append("No transactions logged for this month yet. Add some to see insights here.")
        return notes

    if summary["savings_rate"] is not None:
        if summary["savings_rate"] < 0:
            notes.append(
                f"You spent more than you earned this month (net {summary['net']:+.2f}). "
                f"Review your largest categories below to find room to cut back."
            )
        elif summary["savings_rate"] < 10:
            notes.append(
                f"Your savings rate is {summary['savings_rate']}% this month — on the low side. "
                f"Financial guidelines often suggest aiming for 15-20%+."
            )
        elif summary["savings_rate"] >= 20:
            notes.append(
                f"Strong month — you saved {summary['savings_rate']}% of your income."
            )

    if breakdown:
        top = breakdown[0]
        notes.append(
            f"{top['category']} was your biggest expense category at ${top['total']:.2f} "
            f"({top['percent']}% of spending)."
        )

    if mom:
        direction = "up" if mom["change_percent"] > 0 else "down"
        if abs(mom["change_percent"]) >= 10:
            notes.append(
                f"Spending is {direction} {abs(mom['change_percent'])}% compared to "
                f"{mom['previous_month']} (${mom['previous_expense']:.2f} → ${mom['current_expense']:.2f})."
            )

    over_budget = [b for b in budgets if b["over_budget"]]
    if over_budget:
        names = ", ".join(f"{b['category']} (${b['spent']:.0f}/${b['limit']:.0f})" for b in over_budget[:3])
        notes.append(f"Over budget in: {names}.")

    if recurring:
        total_recurring = sum(r["amount"] for r in recurring)
        notes.append(
            f"Detected {len(recurring)} likely recurring payment(s) totaling ~${total_recurring:.2f}/month "
            f"({', '.join(r['description'] for r in recurring[:3])}"
            f"{'...' if len(recurring) > 3 else ''}). Worth a quick subscription audit."
        )

    if not notes:
        notes.append("Nothing unusual to flag this month — spending looks steady.")

    return notes
