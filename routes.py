from crypt import methods
from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
    redirect,
    flash,
    session,
)

from app import app
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps


# decorator for auth required
def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "user_id" in session:
            return func(*args, **kwargs)
        else:
            flash("Please login to continue")
            return redirect(url_for("login"))

    return inner


@app.route("/")
@auth_required
def index():
    # user_id in session
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        flash("Please fill out all the fields")
        return redirect(url_for("login"))

    # returns a boolean value on whether the user exists of not
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("Username does not exist")
        return redirect(url_for("login"))

    if not check_password_hash(user.passhash, password):
        flash("Incorrect password")
        return redirect(url_for("login"))

    session["user_id"] = (
        user.id
    )  # user_id is a varible and the key of the dictionary session
    flash("Login successful")
    return redirect(url_for("index"))


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register_post():
    name = request.form.get("name")
    # name of the input in the form should match the name inside get
    username = request.form.get("username")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if not name or not username or not password or not confirm_password:
        flash("Please fill out all the fields")
        return redirect(url_for("register"))

    if password != confirm_password:
        flash("Passwords do not match")
        return redirect(url_for("register"))

    user = User.query.filter_by(username=username).first()

    if user:
        flash("User already exists")
        return redirect(url_for("register"))

    password_hash = generate_password_hash(password)

    new_user = User(username=username, passhash=password_hash, name=name)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for("login"))


@app.route("/profile")
@auth_required
def profile():
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)


@app.route("/profile", methods=["POST"])
@auth_required
def profile_post():
    name = request.form.get("name")
    username = request.form.get("username")
    cpassword = request.form.get("cpassword")
    password = request.form.get("password")

    user = User.query.get(session["user_id"])
    new_username = User.query.filter_by(username=username).first()
    if new_username:
        flash("Username already exists")
        return redirect(url_for("profile"))

    if not check_password_hash(user.passhash, cpassword):
        flash("Current passwords do not match")
        return redirect(url_for("profile"))

    if check_password_hash(user.passhash, password):
        flash("New password cannot be same as the old password")
        return redirect(url_for("profile"))

    new_password_hash = generate_password_hash(password)
    user.username = username
    user.passhash = new_password_hash
    user.name = name
    db.session.commit()
    flash("Profile updated successfully")
    return redirect(url_for("profile"))


@app.route("/logout")
@auth_required
def logout():
    session.pop("user_id")
    return redirect(url_for("login"))
