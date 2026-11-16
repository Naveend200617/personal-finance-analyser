from functools import wraps
from flask import session, redirect, url_for, flash, request


INCOME_CATEGORIES = ["Salary", "Business", "Freelancing", "Investment", "Gift", "Other"]
EXPENSE_CATEGORIES = ["Food", "Shopping", "Transport", "Education", "Healthcare",
                      "Entertainment", "Electricity", "Rent", "Bills", "Other"]


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated


def current_user_id():
    return session.get("user_id")
