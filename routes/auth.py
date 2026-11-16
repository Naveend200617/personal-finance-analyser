from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User
from .helpers import login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Server-side validation
        errors = []
        if not name or len(name) < 2:
            errors.append("Name must be at least 2 characters.")
        if not email or "@" not in email or "." not in email.split("@")[-1]:
            errors.append("Please enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("This email is already registered. Please log in.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", name=name, email=email)

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
        )
        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Registration failed due to a database error. Try again.", "danger")
            return render_template("register.html", name=name, email=email)

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            session["user_name"] = user.name
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("dashboard.index"))

        flash("Invalid email or password.", "danger")
        return render_template("login.html", email=email)

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
