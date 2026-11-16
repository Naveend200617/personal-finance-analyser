from datetime import date
from sqlalchemy import func, extract
from flask import Blueprint, render_template
from extensions import db
from models import Transaction, Budget
from .helpers import login_required, current_user_id

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    uid = current_user_id()
    today = date.today()
    month, year = today.month, today.year

    # Overall totals
    total_income = (db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
                    .filter_by(user_id=uid, transaction_type="income").scalar())
    total_expense = (db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
                     .filter_by(user_id=uid, transaction_type="expense").scalar())
    total_balance = total_income - total_expense

    # This-month totals
    def month_sum(ttype, m=month, y=year):
        base = (db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
                .filter(Transaction.user_id == uid,
                        Transaction.transaction_type == ttype,
                        extract("month", Transaction.transaction_date) == m,
                        extract("year", Transaction.transaction_date) == y)
                .scalar())
        return base

    month_income = month_sum("income")
    month_expense = month_sum("expense")
    monthly_savings = month_income - month_expense

    # Budget for this month (Overall)
    overall_budget = (Budget.query
                      .filter_by(user_id=uid, category="Overall", month=month, year=year)
                      .first())
    monthly_budget = overall_budget.monthly_limit if overall_budget else 0
    remaining_budget = monthly_budget - month_expense

    recent = (Transaction.query.filter_by(user_id=uid)
              .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
              .limit(8).all())

    # Category-wise expense data for current month (pie chart)
    cat_rows = (db.session.query(Transaction.category, func.sum(Transaction.amount))
                .filter(Transaction.user_id == uid,
                        Transaction.transaction_type == "expense",
                        extract("month", Transaction.transaction_date) == month,
                        extract("year", Transaction.transaction_date) == year)
                .group_by(Transaction.category).all())

    # Last 6 months income/expense (bar/line chart)
    monthly_labels, monthly_income_data, monthly_expense_data = [], [], []
    m, y = month, year
    months = []
    for _ in range(6):
        months.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    months.reverse()
    for (yy, mm) in months:
        monthly_labels.append(date(yy, mm, 1).strftime("%b %Y"))
        monthly_income_data.append(float(month_sum("income", mm, yy)))
        monthly_expense_data.append(float(month_sum("expense", mm, yy)))

    # Budget utilization
    utilization = round((float(month_expense) / float(monthly_budget) * 100), 1) if monthly_budget else 0

    return render_template(
        "dashboard.html",
        total_income=float(total_income),
        total_expense=float(total_expense),
        total_balance=float(total_balance),
        monthly_savings=float(monthly_savings),
        monthly_budget=float(monthly_budget),
        remaining_budget=float(remaining_budget),
        utilization=utilization,
        recent=recent,
        month_income=float(month_income),
        month_expense=float(month_expense),
        cat_labels=[r[0] for r in cat_rows],
        cat_values=[float(r[1]) for r in cat_rows],
        monthly_labels=monthly_labels,
        monthly_income=monthly_income_data,
        monthly_expense=monthly_expense_data,
    )
