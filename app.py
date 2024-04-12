from flask import Flask

app = Flask(__name__)

import config
import routes
import models
import api


if __name__ == "__main__":
    app.run(debug=True)


# come back to the book show page if the user tries to access a book that does not exist
