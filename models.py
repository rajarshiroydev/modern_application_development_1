from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash


db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    username = db.Column(db.String(32), unique=True)
    passhash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    books = db.relationship(
        "Books", backref="section", lazy=True, cascade="all, delete-orphan"
    )


class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    content = db.Column(db.Text)
    author = db.Column(db.String(64))
    date_issued = db.Column(db.Date)
    return_date = db.Column(db.Date)
    section_id = db.Column(db.Integer, db.ForeignKey("section.id"))

    carts = db.relationship("Cart", backref="book", lazy=True)


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    username = db.Column(db.Integer, db.ForeignKey("user.username"))
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"))


class Issued(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"))
    username = db.Column(db.String(32))
    author = db.Column(db.String(64))
    date_issued = db.Column(db.Date)
    return_date = db.Column(db.Date)


with app.app_context():
    db.create_all()
    # if an admin does not exist
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        password_hash = generate_password_hash("admin")
        admin = User(
            name="admin", username="admin", passhash=password_hash, is_admin=True
        )
    db.session.add(admin)
    db.session.commit()
