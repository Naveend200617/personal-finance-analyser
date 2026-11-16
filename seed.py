"""Seed the database with a demo user and ~2 months of sample transactions.

Usage:
    python seed.py
Demo login:  demo@pocketwise.com  /  demo123
"""
import random
from datetime import date, timedelta
from decimal import Decimal
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import User, Transaction, Budget

app = create_app()

random.seed(7)

DEMO_EXPENSES = [
    ("Groceries", "Food", 400, 1400), ("Dinner out", "Food", 300, 900),
    ("Bus / cab fares", "Transport", 60, 400), ("Online shopping", "Shopping", 500, 2500),
    ("Online course", "Education", 500, 1500), ("Pharmacy", "Healthcare", 150, 800),
    ("Movie night", "Entertainment", 250, 700), ("Electricity bill", "Electricity", 900, 1600),
    ("House rent", "Rent", 8500, 8500), ("Mobile recharge", "Bills", 239, 399),
]


def make_month(uid, year, month):
    # salary
    db.session.add(Transaction(
        user_id=uid, title=f"Salary", transaction_type="income", category="Salary",
        amount=Decimal("45000.00"), transaction_date=date(year, month, 1),
        description="Monthly salary credit"))
    db.session.add(Transaction(
        user_id=uid, title="Freelance project", transaction_type="income", category="Freelancing",
        amount=Decimal(random.choice([3000, 5000, 8000])),
        transaction_date=date(year, month, random.randint(8, 20)),
        description="Side project payment"))
    # expenses spread across the month
    d = date(year, month, 1)
    days = min(28, (date(year, month + 1, 1) - timedelta(days=1)).day) if month < 12 else 28
    for title, cat, lo, hi in DEMO_EXPENSES:
        repeat = 1 if cat in ("Rent", "Electricity", "Bills") else random.randint(1, 2)
        for _ in range(repeat):
            amt = Decimal(random.randint(lo, hi))
            day = random.randint(1, min(days, date.today().day if (year, month) == (date.today().year, date.today().month) else days))
            day = max(1, min(day, days))
            db.session.add(Transaction(
                user_id=uid, title=title, transaction_type="expense", category=cat,
                amount=amt, transaction_date=date(year, month, day)))


with app.app_context():
    db.create_all()
    user = User.query.filter_by(email="demo@pocketwise.com").first()
    if user:
        print("Demo user already exists — clearing their data and reseeding.")
        Transaction.query.filter_by(user_id=user.id).delete()
        Budget.query.filter_by(user_id=user.id).delete()
        db.session.commit()
    else:
        user = User(name="Demo User", email="demo@pocketwise.com",
                    password_hash=generate_password_hash("demo123"))
        db.session.add(user)
        db.session.commit()

    today = date.today()
    this_month, this_year = today.month, today.year
    pm, py = (this_month - 1, this_year) if this_month > 1 else (12, this_year - 1)

    make_month(user.id, py, pm)
    make_month(user.id, this_year, this_month)

    db.session.add(Budget(user_id=user.id, category="Overall", monthly_limit=Decimal("30000"),
                          month=this_month, year=this_year))
    db.session.add(Budget(user_id=user.id, category="Food", monthly_limit=Decimal("6000"),
                          month=this_month, year=this_year))
    db.session.add(Budget(user_id=user.id, category="Shopping", monthly_limit=Decimal("4000"),
                          month=this_month, year=this_year))

    db.session.commit()
    print("Seeded:")
    print(f"  user_id  = {user.id}")
    print(f"  txns     = {Transaction.query.filter_by(user_id=user.id).count()}")
    print(f"  budgets  = {Budget.query.filter_by(user_id=user.id).count()}")
    print("Login with: demo@pocketwise.com / demo123")
