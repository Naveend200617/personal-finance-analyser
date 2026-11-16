from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Transaction
from .helpers import login_required, current_user_id, INCOME_CATEGORIES

income_bp = Blueprint("income", __name__, url_prefix="/income")


def parse_txn_form(form):
    title = form.get("title", "").strip()
    category = form.get("category", "").strip()
    amount_raw = form.get("amount", "").strip()
    date_raw = form.get("date", "").strip()
    description = form.get("description", "").strip()

    errors = []
    if not title:
        errors.append("Title is required.")
    if category not in INCOME_CATEGORIES:
        errors.append("Please choose a valid income category.")
    try:
        amount = Decimal(amount_raw)
        if amount <= 0:
            errors.append("Amount must be greater than zero.")
    except (InvalidOperation, ValueError):
        amount = None
        errors.append("Amount must be a valid number.")
    try:
        txn_date = datetime.strptime(date_raw, "%Y-%m-%d").date()
        if txn_date > date.today():
            errors.append("Transaction date cannot be in the future.")
    except ValueError:
        txn_date = None
        errors.append("Please provide a valid date.")
    return title, category, amount, txn_date, description, errors


@income_bp.route("/")
@login_required
def index():
    uid = current_user_id()
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    query = Transaction.query.filter_by(user_id=uid, transaction_type="income")
    if q:
        query = query.filter(Transaction.title.ilike(f"%{q}%"))
    if category in INCOME_CATEGORIES:
        query = query.filter_by(category=category)
    rows = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).all()
    total = sum(float(r.amount) for r in rows)

    return render_template("income.html", rows=rows, total=total,
                           categories=INCOME_CATEGORIES, q=q, category=category,
                           now_date=date.today().isoformat())


@income_bp.route("/add", methods=["POST"])
@login_required
def add():
    title, category, amount, txn_date, description, errors = parse_txn_form(request.form)
    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("income.index"))

    txn = Transaction(user_id=current_user_id(), title=title, transaction_type="income",
                      category=category, amount=amount, transaction_date=txn_date,
                      description=description)
    try:
        db.session.add(txn)
        db.session.commit()
        flash("Income added successfully.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not save income. Database error.", "danger")
    return redirect(url_for("income.index"))


@income_bp.route("/edit/<int:txn_id>", methods=["POST"])
@login_required
def edit(txn_id):
    txn = Transaction.query.get_or_404(txn_id)
    if txn.user_id != current_user_id() or txn.transaction_type != "income":
        flash("You are not allowed to edit this record.", "danger")
        return redirect(url_for("income.index"))

    title, category, amount, txn_date, description, errors = parse_txn_form(request.form)
    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("income.index"))

    txn.title, txn.category, txn.amount = title, category, amount
    txn.transaction_date, txn.description = txn_date, description
    try:
        db.session.commit()
        flash("Income updated.", "success")
    except Exception:
        db.session.rollback()
        flash("Update failed. Database error.", "danger")
    return redirect(url_for("income.index"))


@income_bp.route("/delete/<int:txn_id>", methods=["POST"])
@login_required
def delete(txn_id):
    txn = Transaction.query.get_or_404(txn_id)
    if txn.user_id != current_user_id() or txn.transaction_type != "income":
        flash("You are not allowed to delete this record.", "danger")
        return redirect(url_for("income.index"))
    try:
        db.session.delete(txn)
        db.session.commit()
        flash("Income record deleted.", "info")
    except Exception:
        db.session.rollback()
        flash("Delete failed. Database error.", "danger")
    return redirect(url_for("income.index"))
