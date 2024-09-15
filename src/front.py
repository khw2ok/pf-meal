from .data import *
from flask import Blueprint, render_template, request, session
app = Blueprint("front", __name__, url_prefix="/m")

from urllib import parse
import json

@app.route("/")
def index():
  return render_template("index.html")

@app.route("/config")
def config():
  return render_template("config.html")

@app.route("/config/<uid>", methods=["GET", "POST"])
def config_uid(uid:str):
  udata = json.load(open("src/data/udata.json", encoding="UTF-8"))
  if request.method == "POST":
    if int(request.form["type"]) == 0 and request.form["target[]"] not in udata[uid]["mealFav"]:
      (udata[uid]["mealFav"]).append(request.form["target[]"])
      json.dump(udata, open("src/data/udata.json", "w", encoding="UTF-8"), indent=2)
    elif int(request.form["type"]) == 1:
      for i in request.form.getlist("target[]"):
        if i in udata[uid]["mealFav"]:
          udata[uid]["mealFav"].remove(i)
          json.dump(udata, open("src/data/udata.json", "w", encoding="UTF-8"), indent=2)
    return {"done": True}
  else:
    prms = request.args.to_dict()
    if not "s" in prms: prms["s"] = ""
    if not uid in udata:
      return render_template("error.html", msg="유효하지 않은 uid 입니다.")
    return render_template("config_uid.html", udata=udata, prms=prms, uid=uid, enumerate=enumerate, parse=parse)

@app.route("/rank")
def rank():
  mdata = json.load(open("src/data/mdata.json", encoding="UTF-8"))
  prms = request.args.to_dict()
  if not "m" in prms: prms["m"] = datetime.strftime(datetime.now(), "%Y-%m")
  try: mdata_month = json.load(open(f"src/data/mdata.{prms['m']}.json", encoding="UTF-8"))
  except FileNotFoundError or json.decoder.JSONDecodeError:
    with open(f"src/data/mdata.{datetime.strftime(datetime.now(), '%Y-%m')}.json", "w", encoding="UTF-8") as file:
      file.write("{}")
      file.close()
    mdata_month = json.load(open(f"src/data/mdata.{datetime.strftime(datetime.now(), '%Y-%m')}.json", encoding="UTF-8"))
  return render_template("rank.html", mdata=dict(reversed(sorted(mdata.items(), key=lambda i: len(i[1]["score"])))), mdata_month=mdata_month, prms=prms, list=list, mdkeys=list(mdata.keys()), enumerate=enumerate, len=len, parse=parse)
