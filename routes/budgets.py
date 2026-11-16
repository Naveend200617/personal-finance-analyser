from datetime import date
from decimal import Decimal, InvalidOperation
from sqlalchemy import func, extract
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Budget, Transaction
from .helpers import login_required, current_user_id, EXPENSE_CATEGORIES

budgets_bp = Blueprint("budgets", __name__, url_prefix="/budgets")
BUDGET_CATEGORIES = ["Overall"] + EXPENSE_CATEGORIES


@budgets_bp.route("/")
@login_required
def index():
    uid = current_user_id()
    today = date.today()
    month = int(request.args.get("month", today.month))
    year = int(request.args.get("year", today.year))
    if not (1 <= month <= 12):
        month = today.month

    budgets = (Budget.query.filter_by(user_id=uid, month=month, year=year)
               .order_by(Budget.category).all())

    # amount spent per category for the period
    spent_rows = (db.session.query(Transaction.category, func.sum(Transaction.amount))
                  .filter(Transaction.user_id == uid,
                          Transaction.transaction_type == "expense",
                          extract("month", Transaction.transaction_date) == month,
                          extract("year", Transaction.transaction_date) == year)
                  .group_by(Transaction.category).all())
    spent_by_cat = {r[0]: float(r[1]) for r in spent_rows}
    overall_spent = sum(spent_by_cat.values())

    budget_rows = []
    for b in budgets:
        spent = overall_spent if b.category == "Overall" else spent_by_cat.get(b.category, 0.0)
        limit = float(b.monthly_limit)
        pct = round(spent / limit * 100, 1) if limit > 0 else 0
        budget_rows.append({
            "id": b.id,
            "category": b.category,
            "limit": limit,
            "spent": spent,
            "remaining": limit - spent,
            "pct": min(pct, 999),
            "exceeded": spent > limit,
        })

    # month selector data: months that have budgets, plus current month
    periods = (db.session.query(Budget.month, Budget.year)
               .filter_by(user_id=uid).distinct()
               .order_by(Budget.year.desc(), Budget.month.desc()).all())

    return render_template("budgets.html",
                           budgets=budget_rows, month=month, year=year,
                           month_name=date(year, month, 1).strftime("%B %Y"),
                           categories=BUDGET_CATEGORIES, periods=periods)


@budgets_bp.route("/add", methods=["POST"])
@login_required
def add():
    uid = current_user_id()
    category = request.form.get("category", "").strip()
    limit_raw = request.form.get("monthly_limit", "").strip()
    month = request.form.get("month", "").strip()
    year = request.form.get("year", "").strip()

    errors = []
    if category not in BUDGET_CATEGORIES:
        errors.append("Please choose a valid budget category.")
    try:
        limit = Decimal(limit_raw)
        if limit <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        limit = None
        errors.append("Limit must be a positive number.")
    try:
        month, year = int(month), int(year)
        if not (1 <= month <= 12):
            raise ValueError
        if not (2000 <= year <= 2100):
            raise ValueError
    except ValueError:
        errors.append("Invalid month or year.")

    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("budgets.index", month=request.form.get("month", date.today().month),
                                year=request.form.get("year", date.today().year)))

    existing = Budget.query.filter_by(user_id=uid, category=category, month=month, year=year).first()
    if existing:
        existing.monthly_limit = limit
        flash(f"Budget for {category} already existed — limit updated.", "info")
    else:
        db.session.add(Budget(user_id=uid, category=category, monthly_limit=limit,
                              month=month, year=year))
        flash("Budget saved.", "success")
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Could not save budget. Database error.", "danger")
    return redirect(url_for("budgets.index", month=month, year=year))


@budgets_bp.route("/edit/<int:budget_id>", methods=["POST"])
@login_required
def edit(budget_id):
    b = Budget.query.get_or_404(budget_id)
    if b.user_id != current_user_id():
        flash("You are not allowed to edit this budget.", "danger")
        return redirect(url_for("budgets.index"))
    limit_raw = request.form.get("monthly_limit", "").strip()
    try:
        limit = Decimal(limit_raw)
        if limit <= 0:
            raise ValueError
        b.monthly_limit = limit
        db.session.commit()
        flash("Budget updated.", "success")
    except (InvalidOperation, ValueError):
        flash("Limit must be a positive number.", "danger")
    except Exception:
        db.session.rollback()
        flash("Update failed. Database error.", "danger")
    return redirect(url_for("budgets.index", month=b.month, year=b.year))


@budgets_bp.route("/delete/<int:budget_id>", methods=["POST"])
@login_required
def delete(budget_id):
    b = Budget.query.get_or_404(budget_id)
    if b.user_id != current_user_id():
        flash("You are not allowed to delete this budget.", "danger")
        return redirect(url_for("budgets.index"))
    m, y = b.month, b.year
    try:
        db.session.delete(b)
        db.session.commit()
        flash("Budget deleted.", "info")
    except Exception:
        db.session.rollback()
        flash("Delete failed. Database error.", "danger")
    return redirect(url_for("budgets.index", month=m, year=y))
