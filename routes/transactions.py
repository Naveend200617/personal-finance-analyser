from datetime import datetime
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Transaction
from .helpers import login_required, current_user_id, INCOME_CATEGORIES, EXPENSE_CATEGORIES

transactions_bp = Blueprint("transactions", __name__, url_prefix="/transactions")


@transactions_bp.route("/")
@login_required
def index():
    uid = current_user_id()
    q = request.args.get("q", "").strip()
    ttype = request.args.get("type", "").strip()
    category = request.args.get("category", "").strip()
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()
    sort = request.args.get("sort", "date").strip()
    order = request.args.get("order", "desc").strip()

    query = Transaction.query.filter_by(user_id=uid)
    if q:
        query = query.filter(Transaction.title.ilike(f"%{q}%"))
    if ttype in ("income", "expense"):
        query = query.filter_by(transaction_type=ttype)
    if category:
        query = query.filter_by(category=category)
    if start:
        try:
            query = query.filter(Transaction.transaction_date >= datetime.strptime(start, "%Y-%m-%d").date())
        except ValueError:
            pass
    if end:
        try:
            query = query.filter(Transaction.transaction_date <= datetime.strptime(end, "%Y-%m-%d").date())
        except ValueError:
            pass

    sort_col = Transaction.amount if sort == "amount" else Transaction.transaction_date
    query = query.order_by(sort_col.asc() if order == "asc" else sort_col.desc(), Transaction.id.desc())
    rows = query.all()

    return render_template("transactions.html", rows=rows,
                           income_categories=INCOME_CATEGORIES,
                           expense_categories=EXPENSE_CATEGORIES,
                           q=q, ttype=ttype, category=category,
                           start=start, end=end, sort=sort, order=order)


@transactions_bp.route("/edit/<int:txn_id>", methods=["POST"])
@login_required
def edit(txn_id):
    txn = Transaction.query.get_or_404(txn_id)
    if txn.user_id != current_user_id():
        flash("You are not allowed to edit this transaction.", "danger")
        return redirect(url_for("transactions.index"))

    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    amount_raw = request.form.get("amount", "").strip()
    date_raw = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()
    new_type = request.form.get("transaction_type", "").strip()

    valid_cats = INCOME_CATEGORIES if new_type == "income" else EXPENSE_CATEGORIES
    errors = []
    if new_type not in ("income", "expense"):
        new_type = txn.transaction_type
        valid_cats = INCOME_CATEGORIES if new_type == "income" else EXPENSE_CATEGORIES
    if not title:
        errors.append("Title is required.")
    if category not in valid_cats:
        errors.append("Invalid category for this transaction type.")
    try:
        amount = Decimal(amount_raw)
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        amount = None
        errors.append("Invalid amount.")
    try:
        txn_date = datetime.strptime(date_raw, "%Y-%m-%d").date()
    except ValueError:
        txn_date = None
        errors.append("Invalid date.")

    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("transactions.index"))

    txn.title, txn.transaction_type, txn.category = title, new_type, category
    txn.amount, txn.transaction_date, txn.description = amount, txn_date, description
    try:
        db.session.commit()
        flash("Transaction updated.", "success")
    except Exception:
        db.session.rollback()
        flash("Update failed. Database error.", "danger")
    return redirect(url_for("transactions.index"))


@transactions_bp.route("/delete/<int:txn_id>", methods=["POST"])
@login_required
def delete(txn_id):
    txn = Transaction.query.get_or_404(txn_id)
    if txn.user_id != current_user_id():
        flash("You are not allowed to delete this transaction.", "danger")
        return redirect(url_for("transactions.index"))
    try:
        db.session.delete(txn)
        db.session.commit()
        flash("Transaction deleted.", "info")
    except Exception:
        db.session.rollback()
        flash("Delete failed. Database error.", "danger")
    return redirect(url_for("transactions.index"))
