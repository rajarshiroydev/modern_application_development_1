from flask import flash, redirect, render_template, request, url_for, session, send_file
from app import app
from models import db, Section, User, Books, Cart, Issued, Feedbacks
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
from weasyprint import HTML


# Decorator for authentication of users
def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "user_id" in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for("login"))

    return inner


# Decorator for authentication of admin
def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        user = User.query.get(session["user_id"])

        if not user.is_admin:
            flash("You are not authorized to access this page")
            return redirect(url_for("index"))
        return func(*args, **kwargs)

    return inner


# ----------------------------Register, Login and Logout------------------------------------#


# register page
@app.route("/register")
def register():
    return render_template("register.html")


# register page post
@app.route("/register", methods=["POST"])
def register_post():
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
    flash("Registered successfully.")
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
        flash("You are not registered. Register first.")
        return redirect(url_for("login"))

    # if the user password do not match then it shows error msg
    if not check_password_hash(user.passhash, password):
        flash("Incorrect password")
        return redirect(url_for("login"))

    # user_id is a varible and the key of the dictionary session
    session["user_id"] = user.id
    session["is_admin"] = user.is_admin
    session["username"] = user.username

    flash("Login successful")

    if user.is_admin:
        return redirect(url_for("admin"))
    else:
        return redirect(url_for("index"))


# logout button
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


@app.route("/book/add/<int:section_id>")
@admin_required
def add_book(section_id):
    sections = Section.query.all()
    section = Section.query.get(section_id)
    if not section:
        flash("Section does not exist")
        return redirect(url_for("admin"))

    now = datetime.now().strftime("%Y-%m-%d")

    return render_template("book/add.html", section=section, sections=sections, now=now)


@app.route("/book/add/", methods=["POST"])
@admin_required
def add_book_post():
    name = request.form.get("name")
    content = request.form.get("content")
    author = request.form.get("author")
    section_id = request.form.get("section_id")

    section = Section.query.get(section_id)

    if not section:
        flash("Cateogory does not exist")
        return redirect(url_for("admin"))

    if not name or not content or not author:
        flash("All fields are mandatory")
        return redirect(url_for("add_book", section_id=section_id))

    book = Books(
        name=name,
        content=content,
        author=author,
        section=section,
    )

    db.session.add(book)
    db.session.commit()
    flash("Book added successfully")
    return redirect(url_for("show_section", id=section_id))


@app.route("/book/<int:id>/edit>")
@admin_required
def edit_book(id):
    sections = Section.query.all()
    book = Books.query.get(id)
    book_date_issued = book.date_issued
    book_return_date = book.return_date
    return render_template(
        "/book/edit.html",
        sections=sections,
        book=book,
        book_date_issued=book_date_issued,
        book_return_date=book_return_date,
    )


@app.route("/book/<int:id>/edit>", methods=["POST"])
@admin_required
def edit_book_post(id):
    name = request.form.get("name")
    content = request.form.get("content")
    author = request.form.get("author")
    section_id = request.form.get("section_id")

    section = Section.query.get(section_id)

    if not section:
        flash("Cateogory does not exist")
        return redirect(url_for("admin"))

    if not name or not content or not author:
        flash("All fields are mandatory")
        return redirect(url_for("add_book", section_id=section_id))

    book = Books.query.get(id)
    book.name = name
    book.content = content
    book.author = author
    book.section = section

    # edits the book and author name in issued books
    # when the source book is edited
    issued_books = Issued.query.get(id)
    issued_books.book_name = name
    issued_books.author = author

    # edits the book and author name in feedbacks
    # when the source book is edited
    feedback = Feedbacks.query.get(id)
    feedback.book_name = name
    feedback.author = author

    db.session.commit()

    flash("Book edited successfully")
    return redirect(url_for("show_section", id=section_id))


@app.route("/book/<int:id>/delete")
@admin_required
def delete_book(id):
    book = Books.query.get(id)

    if not book:
        flash("Book does not exist")
        return redirect(url_for("admin"))

    return render_template("/book/delete.html", book=book)


@app.route("/book/<int:id>/delete", methods=["POST"])
@admin_required
def delete_book_post(id):
    book = Books.query.get(id)

    if not book:
        flash("Book does not exist")
        return redirect(url_for("admin"))

    section_id = book.section_id

    # Before deleting the book, we find all Cart items referencing
    # the book and delete them. This resolves the foreign key constraint violation.
    cart_items = Cart.query.filter_by(book_id=book.id).all()
    for item in cart_items:
        db.session.delete(item)

    # deletes book from library, issued books and user requests
    # when the source book is deleted
    delete_issued_books = Issued.query.filter_by(book_id=book.id).all()
    for issued_book in delete_issued_books:
        db.session.delete(issued_book)

    db.session.delete(book)
    db.session.commit()

    flash("Book deleted successfully")
    return redirect(url_for("show_section", id=section_id))


# ------------------------------User------------------------------------#


@app.route("/")
@auth_required
def index():
    sections = Section.query.filter(Section.books.any()).all()
    parameter = request.args.get("parameter")
    query = request.args.get("query")

    parameters = {
        "section_name": "Section Name",
        "book_name": "Book Name",
        "author_name": "Author Name",
    }

    if parameter == "section_name":
        sections = Section.query.filter(Section.name.ilike(f"%{query}%")).all()
    elif parameter == "book_name":
        sections = [
            section
            for section in sections
            if any(query.lower() in book.name.lower() for book in section.books)
        ]
    elif parameter == "author_name":
        sections = [
            section
            for section in sections
            if any(query.lower() in book.author.lower() for book in section.books)
        ]

    return render_template(
        "index.html",
        sections=sections,
        parameters=parameters,
        query=query,
    )


# ------------------------------User Requests------------------------------------#


@app.route("/cart")
@admin_required
def cart():
    carts = Cart.query.all()
    return render_template("cart.html", carts=carts)


@app.route("/add_to_cart/<int:book_id>", methods=["POST"])
@auth_required
def add_to_cart(book_id):
    book = Books.query.get(book_id)

    if not book:
        flash("Book does not exist")
        return redirect(url_for("index"))

    book.date_issued = datetime.now()

    duration = request.form.get("duration")
    duration = int(duration)
    book.return_date = datetime.now() + timedelta(days=duration)

    # check cart size
    cart_size = Cart.query.filter_by(user_id=session["user_id"]).count()
    if cart_size >= 5:
        flash("You cannot cart for more than 5 books.")
        return redirect(url_for("index"))

    issued_book = Issued.query.filter_by(
        user_id=session["user_id"], book_id=book_id
    ).first()

    if issued_book:
        flash("You already have this book in your library.")
        return redirect(url_for("index"))

    # checks if an item with the same user_id and book_id already exists
    cart = Cart.query.filter_by(user_id=session["user_id"], book_id=book_id).first()

    # if it does, then
    if cart:  # If the book already exists in the cart
        flash("You have already requested for this book.")
    else:  # If the book is new to the cart
        new_cart_item = Cart(
            user_id=session["user_id"],
            book_id=book_id,
            username=session["username"],
        )
        db.session.add(new_cart_item)
        db.session.commit()
        flash("Requested book successfully!")

    return redirect(url_for("index"))


@app.route("/cart/<int:id>/delete", methods=["POST"])
@admin_required
def delete_cart(id):
    cart = Cart.query.get(id)

    if not cart:
        flash("Cart does not exist")
        return redirect(url_for("cart"))

    db.session.delete(cart)
    db.session.commit()
    flash("Request rejected successfully")
    return redirect(url_for("cart"))


# ------------------------------Issued Books------------------------------------#


@app.route("/issued/<int:id>", methods=["POST"])
@admin_required
def issued(id):
    issued = Cart.query.get(id)

    issuance = Issued(
        user_id=issued.user_id,
        book_id=issued.book_id,
        username=issued.username,
        book_name=issued.book.name,
        author=issued.book.author,
        date_issued=issued.book.date_issued,
        return_date=issued.book.return_date,
    )

    db.session.add(issuance)
    db.session.delete(issued)
    db.session.commit()

    flash("Books issued successfully")
    return redirect(url_for("cart"))


@app.route("/issued_books")
@admin_required
def issued_books():
    all_issued = Issued.query.all()
    now = datetime.now().strftime("%Y-%m-%d")
    return render_template("issued.html", all_issued=all_issued, now=now)


@app.route("/revoke_book/<int:book_id>/<int:user_id>", methods=["POST"])
@admin_required
def revoke_book(book_id, user_id):
    revoke_book = Issued.query.filter_by(user_id=user_id, book_id=book_id).first()

    db.session.delete(revoke_book)
    db.session.commit()

    flash("Book revoked successfully.")
    return redirect(url_for("issued_books"))


@app.route("/issued_books_user")
@auth_required
def issued_books_user():
    all_issued = Issued.query.filter_by(user_id=session["user_id"]).all()
    return render_template("library.html", all_issued=all_issued)


@app.route("/return_book/<int:id>", methods=["POST"])
@auth_required
def return_book(id):
    user_id = session.get("user_id")
    return_book = Issued.query.filter_by(user_id=user_id, book_id=id).first()

    db.session.delete(return_book)
    db.session.commit()

    flash("Book returned successfully.")
    return redirect(url_for("issued_books_user"))


# ----------------------------------Feedbacks------------------------------------------- #


@app.route("/give_feedbacks/<int:id>")
@auth_required
def give_feedbacks(id):
    return render_template("give_feedbacks.html", book_id=id)


@app.route("/give_feedbacks_post/<int:id>", methods=["POST"])
@auth_required
def give_feedbacks_post(id):
    feedback = request.form.get("feedback")

    info = Books.query.get(id)

    book_feedback = Feedbacks(
        user_id=session["user_id"],
        book_id=id,
        username=session["username"],
        book_name=info.name,
        author=info.author,
        feedback=feedback,
        date_of_feedback=datetime.now(),
    )
    db.session.add(book_feedback)
    db.session.commit()
    flash("Feedback given successfully")
    return redirect(url_for("issued_books_user"))


@app.route("/show_feedbacks")
@admin_required
def show_feedbacks():
    feedbacks = Feedbacks.query.all()
    return render_template("show_feedbacks.html", feedbacks=feedbacks)


@app.route("/show_feedbacks/<int:book_id>")
@auth_required
def show_feedbacks_user(book_id):
    feedbacks = Feedbacks.query.filter_by(book_id=book_id).all()
    return render_template("show_feedbacks.html", feedbacks=feedbacks)


# ----------------------------------Set Date------------------------------------------- #


# revoke access if book not returned within the return date
@app.route("/set_date", methods=["POST"])
@admin_required
def set_date():
    new_date = request.form.get("new_date")
    new_date = datetime.strptime(new_date, "%Y-%m-%d").date()

    issued_books = Issued.query.all()

    # if set_date > request date then revoke access
    for issued in issued_books:
        if new_date > issued.return_date:
            db.session.delete(issued)

    db.session.commit()
    flash("Successfully revoked books passed the return date.")
    return redirect(url_for("issued_books"))


# ----------------------------------Read Book------------------------------------------- #


@app.route("/readbook/<int:id>", methods=["POST"])
@auth_required
def read_book(id):
    book = Books.query.get(id)
    if not book:
        flash("No such book exists")
        return redirect(url_for("issued_books_user"))
    return render_template("read_book.html", book=book)


# -------------------------------------Download Book------------------------------------------------- #


@app.route("/download_pdf/<int:id>", methods=["POST"])
@auth_required
def download_book(id):
    book = Books.query.get(id)

    name = book.name
    author = book.author
    content = book.content

    # Generate HTML content with book details and content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{name} by {author}</title>
    </head>
    <body>
        <h1>{name}</h1>
        <h2>by {author}</h2>
        <br> 
        <div>{content}</div>
    </body>
    </html>
    """

    filename = f"{name}.pdf"
    HTML(string=html_content).write_pdf(filename)
    return send_file(filename, as_attachment=True)
