import csv
import io
from datetime import date, datetime
from sqlalchemy import func, extract
from flask import Blueprint, render_template, request, Response
from extensions import db
from models import Transaction
from .helpers import login_required, current_user_id

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _month_data(uid, month, year):
    income = (db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
              .filter(Transaction.user_id == uid, Transaction.transaction_type == "income",
                      extract("month", Transaction.transaction_date) == month,
                      extract("year", Transaction.transaction_date) == year).scalar())
    expense = (db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
               .filter(Transaction.user_id == uid, Transaction.transaction_type == "expense",
                       extract("month", Transaction.transaction_date) == month,
                       extract("year", Transaction.transaction_date) == year).scalar())
    cat_rows = (db.session.query(Transaction.category, func.sum(Transaction.amount))
                .filter(Transaction.user_id == uid, Transaction.transaction_type == "expense",
                        extract("month", Transaction.transaction_date) == month,
                        extract("year", Transaction.transaction_date) == year)
                .group_by(Transaction.category)
                .order_by(func.sum(Transaction.amount).desc()).all())
    income_cat_rows = (db.session.query(Transaction.category, func.sum(Transaction.amount))
                       .filter(Transaction.user_id == uid, Transaction.transaction_type == "income",
                               extract("month", Transaction.transaction_date) == month,
                               extract("year", Transaction.transaction_date) == year)
                       .group_by(Transaction.category).all())
    txns = (Transaction.query.filter(Transaction.user_id == uid,
                                     extract("month", Transaction.transaction_date) == month,
                                     extract("year", Transaction.transaction_date) == year)
            .order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).all())
    return float(income), float(expense), cat_rows, income_cat_rows, txns


@reports_bp.route("/")
@login_required
def index():
    uid = current_user_id()
    today = date.today()
    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)
    if not (1 <= month <= 12):
        month = today.month

    income, expense, cat_rows, income_cat_rows, txns = _month_data(uid, month, year)
    savings = income - expense
    # Convert Decimal amounts to float so Jinja math/formatting is safe
    cat_rows = [(name, float(amt)) for name, amt in cat_rows]
    income_cat_rows = [(name, float(amt)) for name, amt in income_cat_rows]

    # 12-month trend for the selected year
    trend_income, trend_expense = [], []
    for m in range(1, 13):
        i, e, _, _, _ = _month_data(uid, m, year)
        trend_income.append(i)
        trend_expense.append(e)

    return render_template(
        "reports.html",
        month=month, year=year,
        month_name=date(year, month, 1).strftime("%B %Y"),
        income=income, expense=expense, savings=savings,
        cat_rows=cat_rows, income_cat_rows=income_cat_rows, txns=txns,
        trend_labels=[date(2000, m, 1).strftime("%b") for m in range(1, 13)],
        trend_income=trend_income, trend_expense=trend_expense,
        chart_labels=[r[0] for r in cat_rows],
        chart_values=[float(r[1]) for r in cat_rows],
    )


@reports_bp.route("/export/csv")
@login_required
def export_csv():
    uid = current_user_id()
    today = date.today()
    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)

    _, _, _, _, txns = _month_data(uid, month, year)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Category", "Title", "Description", "Amount (INR)"])
    for t in txns:
        writer.writerow([t.transaction_date.isoformat(), t.transaction_type, t.category,
                         t.title, t.description or "", f"{float(t.amount):.2f}"])
    filename = f"pocketwise_{year}_{month:02d}.csv"
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})


@reports_bp.route("/export/pdf")
@login_required
def export_pdf():
    uid = current_user_id()
    today = date.today()
    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)

    from flask import session as flask_session
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle)
    from reportlab.lib.styles import getSampleStyleSheet

    income, expense, cat_rows, income_cat_rows, txns = _month_data(uid, month, year)
    savings = income - expense
    month_name = date(year, month, 1).strftime("%B %Y")
    user_name = flask_session.get("user_name", "User")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                            topMargin=1.8 * cm, bottomMargin=1.8 * cm)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("PocketWise — Monthly Financial Report", styles["Title"]))
    story.append(Paragraph(f"{user_name} · {month_name} · Generated {datetime.now():%d %b %Y}",
                           styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    summary = Table([
        ["Total Income (INR)", f"{income:,.2f}"],
        ["Total Expense (INR)", f"{expense:,.2f}"],
        ["Monthly Savings (INR)", f"{savings:,.2f}"],
    ])
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c7d2fe")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(summary)
    story.append(Spacer(1, 0.6 * cm))

    if cat_rows:
        story.append(Paragraph("Category-wise Expenses", styles["Heading2"]))
        data = [["Category", "Amount (INR)", "Share %"]]
        for name, amt in cat_rows:
            data.append([name, f"{float(amt):,.2f}",
                         f"{(float(amt) / expense * 100) if expense else 0:.1f}"])
        t = Table(data)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c7d2fe")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.6 * cm))

    if txns:
        story.append(Paragraph("Transactions", styles["Heading2"]))
        data = [["Date", "Type", "Category", "Title", "Amount (INR)"]]
        for trow in txns[:200]:
            data.append([trow.transaction_date.strftime("%d %b %Y"),
                         trow.transaction_type.capitalize(), trow.category,
                         trow.title[:30], f"{float(trow.amount):,.2f}"])
        t = Table(data, repeatRows=1)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0ea5e9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#bae6fd")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f9ff")]),
        ]
        t.setStyle(TableStyle(style))
        story.append(t)

    doc.build(story)
    buffer.seek(0)
    return Response(buffer.getvalue(), mimetype="application/pdf",
                    headers={"Content-Disposition":
                             f"attachment; filename=pocketwise_report_{year}_{month:02d}.pdf"})
