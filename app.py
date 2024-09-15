from datetime import timedelta
import os

from src import front, back
from flask import Flask
app = Flask(__name__)
app.secret_key = os.environ["APP_SECRET_KEY"]
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=4)
app.register_blueprint(front.app)
app.register_blueprint(back.app)

if __name__ == "__main__":
  app.run("0.0.0.0", 8000)
