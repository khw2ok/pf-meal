from datetime import datetime, timedelta
import os

from src import front, back
from src.data import *
from flask import Flask
app = Flask(__name__)
app.secret_key = os.environ["APP_SECRET_KEY"]
# app.config["SERVER_NAME"] = "localhost:8000"
# app.config["SERVER_NAME"] = "khw2.kro.kr"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=4)
app.register_blueprint(front.app)
app.register_blueprint(back.app)

if __name__ == "__main__":
  app.run("0.0.0.0", 8000, True)