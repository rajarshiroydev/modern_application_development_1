from dotenv import load_dotenv
import os
from app import app  # 1st app is filename, 2nd app is variable name


load_dotenv()
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TEACK_MODIFICATIONS"] = os.getenv(
    "SQLALCHEMY_TEACK_MODIFICATIONS"
)
