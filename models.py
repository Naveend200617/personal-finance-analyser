from datetime import datetime
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship(
        "Transaction", backref="user", lazy=True,
        cascade="all, delete-orphan"
    )
    budgets = db.relationship(
        "Budget", backref="user", lazy=True,
        cascade="all, delete-orphan"
    )
    categories = db.relationship(
        "Category", backref="user", lazy=True,
        cascade="all, delete-orphan"
    )


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    transaction_type = db.Column(db.Enum("income", "expense", name="txn_type"), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    transaction_date = db.Column(db.Date, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False, default="Overall")
    monthly_limit = db.Column(db.Numeric(12, 2), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "category", "month", "year", name="uq_budget_user_cat_month_year"),
    )


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    name = db.Column(db.String(80), nullable=False)
    category_type = db.Column(db.Enum("income", "expense", name="cat_type"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
