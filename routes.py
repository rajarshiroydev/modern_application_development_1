from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
    session,
)
from app import app
from models import db, Section, User, Books
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime


# Decorator for authentication of users
def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "user_id" in session:
            return func(*args, **kwargs)
        else:
            flash("Please login to continue")
            return redirect(url_for("login"))

    return inner


# Decorator for authentication of admin
def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue")
            return redirect(url_for("login"))

        user = User.query.get(session["user_id"])

        if not user.is_admin:
            flash("You are not authorized to access this page")
            return redirect(url_for("index"))
        return func(*args, **kwargs)

    return inner


# ----------------------------Register, Login and Logout------------------------------------#


# index page
@app.route("/")
@auth_required
def index():
    # user_id in session
    return render_template("index.html")


# register page
@app.route("/register")
def register():
    return render_template("register.html")


# register page post
@app.route("/register", methods=["POST"])
def register_post():
    # name of the input in the form should match the name inside get
    name = request.form.get("name")
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


# login page
@app.route("/login")
def login():
    return render_template("login.html")


# login page post
@app.route("/login", methods=["POST"])
def login_post():
    # fetches the username and password from the html login form
    username = request.form.get("username")
    password = request.form.get("password")

    # checks if all the fields are filled
    if not username or not password:
        flash("Please fill out all the fields")
        return redirect(url_for("login"))

    # returns a boolean value on whether the user exists of not
    # the first username is the username field in the model User
    # the second username is the varible username which is fetched from the html form
    user = User.query.filter_by(username=username).first()

    # if the user doesn't exist, then it shows error msg
    if not user:
        flash("Username does not exist")
        return redirect(url_for("login"))

    # if the user password do not match then it shows error msg
    if not check_password_hash(user.passhash, password):
        flash("Incorrect password")
        return redirect(url_for("login"))

    # user_id is a varible and the key of the dictionary session
    session["user_id"] = user.id
    session["is_admin"] = user.is_admin

    flash("Login successful")

    if user.is_admin:
        return redirect(url_for(""))
    else:
        return redirect(url_for("index"))


@app.route("/logout")
@auth_required
def logout():
    session.pop("user_id")
    return redirect(url_for("login"))


# ------------------------------Profile Page------------------------------------#


# profile page
@app.route("/profile")
@auth_required
def profile():
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)


@app.route("/profile", methods=["POST"])
@auth_required
def profile_post():
    name = request.form.get("name")
    username = request.form.get("username")  # rajarshiroy
    cpassword = request.form.get("cpassword")
    password = request.form.get("password")

    if not name or not username or not cpassword or not password:
        flash("Please fill out all the fields")
        return redirect(url_for("profile"))

    user = User.query.get(session["user_id"])
    if username != user.username:  # rajarshiroy != rajarshiroy2
        new_username = User.query.filter_by(username=username).first()
        if new_username:
            flash("Username already exists")
            return redirect(url_for("profile"))

    if not check_password_hash(user.passhash, cpassword):
        flash("Current passwords do not match")
        return redirect(url_for("profile"))

    if check_password_hash(cpassword, password):
        flash("New password cannot be same as the old password")
        return redirect(url_for("profile"))

    new_password_hash = generate_password_hash(password)
    user.username = username
    user.passhash = new_password_hash
    user.name = name
    db.session.commit()
    flash("Profile updated successfully")
    return redirect(url_for("profile"))


# ------------------------------Admin & Sections------------------------------------#


# admin page
@app.route("/admin")
@admin_required
def admin():
    sections = Section.query.all()
    return render_template("admin.html", sections=sections)


@app.route("/section/add")
@admin_required
def add_section():
    return render_template("/section/add.html")


@app.route("/section/add", methods=["POST"])
@admin_required
def add_section_post():
    name = request.form.get("name")

    if not name:
        flash("Please fill out all the fields")
        return redirect(url_for("add_section"))

    section = Section(name=name)
    db.session.add(section)
    db.session.commit()

    flash("Section created successfully")
    return redirect(url_for("admin"))


@app.route("/section/<int:id>/")
@admin_required
def show_section(id):
    section = Section.query.get(id)
    if not section:
        flash("Section does not exist")
        return redirect(url_for("admin"))
    return render_template("/section/show.html", section=section)


# @app.route("/section/<int:id>/", methods=['POST'])
# @admin_required
# def show_section_post(id):
#     section = Section.query.get(id)
#     if not section:
#         flash("Section does not exist")
#         return redirect(url_for("admin"))
#     return render_template("/section/show.html", section=section)


@app.route("/section/<int:id>/edit")
@admin_required
def edit_section(id):
    section = Section.query.get(id)
    if not section:
        flash("Section does not exist")
        return redirect(url_for("admin"))
    return render_template("/section/edit.html", section=section)


@app.route("/section/<int:id>/edit", methods=["POST"])
@admin_required
def edit_section_post(id):
    # fetches the section object(instance) of the given id
    section = Section.query.get(id)

    # checks if the section exists or not
    if not section:
        flash("Section does not exist")
        return redirect(url_for("admin"))
    # fetches the name from the html form for editing the section name
    name = request.form.get("name")

    # if the user leaves the form empty, then the below error message is given
    if not name:
        flash("Please fill out all the fields")
        return redirect(url_for("edit_section", id=id))

    # updated with the new section name, committed to the db, success message shown, redirected to admin dashboard
    section.name = name
    db.session.commit()
    flash("Section updated successfully")
    return redirect(url_for("admin"))


@app.route("/section/<int:id>/delete")
@admin_required
def delete_section(id):
    section = Section.query.get(id)
    if not section:
        flash("Section does not exist")
        return redirect(url_for("admin"))
    return render_template("/section/delete.html", section=section)


@app.route("/section/<int:id>/delete", methods=["POST"])
@admin_required
def delete_section_post(id):
    section = Section.query.get(id)
    if not section:
        flash("Section does not exist")
        return redirect(url_for("admin"))

    db.session.delete(section)
    db.session.commit()
    flash("Section deleted successfully")
    return redirect(url_for("admin"))


# ------------------------------Admin & Books------------------------------------#


# Book
@app.route("/book/add/<int:section_id>")
@admin_required
def add_book(section_id):
    sections = Section.query.all()
    section = Section.query.get(section_id)
    if not section:
        flash("Section does not exist")
        return redirect(url_for("admin"))
    # now = datetime.now().strftime('%Y-%m-%d')
    return render_template("book/add.html", section=section, sections=sections)


@app.route("/section/add", methods=["POST"])
@admin_required
def add_book_post():
    name = request.form.get("name")

    if not name:
        flash("Please fill out all the fields")
        return redirect(url_for("add_section"))

    section = Section(name=name)
    db.session.add(section)
    db.session.commit()

    flash("Section created successfully")
    return redirect(url_for("admin"))
