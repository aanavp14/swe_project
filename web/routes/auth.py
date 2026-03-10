"""
Auth routes: login, signup, logout.
"""

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from persistence.sqlite.user_repository import create_user, get_user_by_email

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login with email and password. Optional name is saved to profile."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    next_url = request.args.get("next") or request.form.get("next") or url_for("index")
    if request.method != "POST":
        return render_template("login.html", error=None, next_url=next_url)
    email = (request.form.get("email") or "").strip()
    password = request.form.get("password") or ""
    if not email or not password:
        return render_template("login.html", error="Email and password required", next_url=next_url), 400
    user = get_user_by_email(email)
    if not user or not check_password_hash(user.password_hash, password):
        return render_template("login.html", error="Invalid email or password", next_url=next_url), 401
    login_user(user, remember=True)
    return redirect(next_url)


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    """Create a new account. Name is required."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    next_url = request.args.get("next") or request.form.get("next") or url_for("index")
    if request.method != "POST":
        return render_template("signup.html", error=None, next_url=next_url)
    email = (request.form.get("email") or "").strip()
    password = request.form.get("password") or ""
    name = (request.form.get("name") or "").strip()
    if not email or not password:
        return render_template("signup.html", error="Email and password required", next_url=next_url), 400
    if not name:
        return render_template("signup.html", error="Name is required", next_url=next_url), 400
    if len(password) < 8:
        return render_template("signup.html", error="Password must be at least 8 characters", next_url=next_url), 400
    if get_user_by_email(email):
        return render_template("signup.html", error="Email already registered", next_url=next_url), 409
    pw_hash = generate_password_hash(password, method="scrypt")
    create_user(email, pw_hash, name=name)
    user = get_user_by_email(email)
    login_user(user, remember=True)
    return redirect(next_url)


@bp.route("/logout")
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    return redirect(url_for("index"))
