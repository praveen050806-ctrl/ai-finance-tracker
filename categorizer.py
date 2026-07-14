"""
categorizer.py
----------------
Rule-based transaction categorization. Matches a transaction's
description against a keyword database to guess a spending category —
similar in spirit to a bank app's "auto-categorize" feature, without
needing any external AI service.

Categories and keywords are easy to extend for your own spending habits.
"""

import re

CATEGORY_KEYWORDS = {
    "Groceries": [
        "grocery", "supermarket", "walmart", "costco", "trader joe",
        "whole foods", "safeway", "kroger", "aldi", "big bazaar", "reliance fresh",
    ],
    "Food & Dining": [
        "restaurant", "cafe", "coffee", "starbucks", "mcdonald", "burger",
        "pizza", "doordash", "ubereats", "uber eats", "grubhub", "swiggy",
        "zomato", "dining", "diner", "bakery", "bar", "pub",
    ],
    "Transport": [
        "uber", "lyft", "taxi", "cab", "gas station", "fuel", "shell", "chevron",
        "parking", "toll", "metro", "transit", "train ticket", "ola",
    ],
    "Housing & Utilities": [
        "rent", "mortgage", "electricity", "water bill", "gas bill",
        "internet", "broadband", "utility", "utilities", "landlord", "hoa",
    ],
    "Subscriptions": [
        "netflix", "spotify", "hulu", "disney+", "amazon prime", "youtube premium",
        "subscription", "apple music", "icloud", "adobe", "gym membership",
        "membership",
    ],
    "Shopping": [
        "amazon", "ebay", "target", "best buy", "mall", "clothing", "shoes",
        "flipkart", "myntra", "ikea", "online store",
    ],
    "Health": [
        "pharmacy", "doctor", "hospital", "clinic", "dental", "medical",
        "insurance", "cvs", "walgreens", "health",
    ],
    "Entertainment": [
        "movie", "cinema", "concert", "theatre", "theater", "game", "steam",
        "playstation", "xbox", "event ticket",
    ],
    "Travel": [
        "flight", "airline", "airbnb", "hotel", "booking.com", "expedia",
        "vacation", "travel",
    ],
    "Income": [
        "salary", "paycheck", "payroll", "deposit", "refund", "interest earned",
        "dividend", "bonus", "freelance payment", "invoice paid",
    ],
    "Transfers & Fees": [
        "transfer", "atm fee", "bank fee", "service charge", "wire transfer",
        "venmo", "paypal", "zelle",
    ],
}

DEFAULT_CATEGORY = "Other"


def categorize(description):
    """
    Guess a category for a transaction based on its description.
    Returns the first matching category, or DEFAULT_CATEGORY if nothing matches.
    """
    text = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category
    return DEFAULT_CATEGORY


def get_all_categories():
    """All known categories, plus the default, in a stable order."""
    return list(CATEGORY_KEYWORDS.keys()) + [DEFAULT_CATEGORY]


def is_income_category(category):
    return category == "Income"
