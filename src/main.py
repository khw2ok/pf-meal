from flask import Flask, request
app = Flask(__name__)

import datetime
import dotenv
dotenv.load_dotenv()

import json
data = json.load(open("src/data.json", encoding="UTF-8"))
defaultData = {
  "schoolId": [None, None],
  "schoolFav": [],
  "mealFav": [],
  "settings": {
    "allergicMeal": False,
    "notifMeal": False
  },
  "usage": 12
}
daysData = ["월", "화", "수", "목", "금", "토", "일"]

import os
import requests

class reqOrg:
  def __init__(self, req:dict):
    self.uid = req["userRequest"]["user"]["id"]
    self.utterance = req["userRequest"]["utterance"]
    self.params = req["action"]["params"]
    self.clientExtra = req["action"]["clientExtra"]

def isUserInData(uid:str):
  data = json.load(open("src/data.json", encoding="UTF-8"))
  if not uid in data:
    data[uid] = defaultData
    json.dump(data, open("src/data.json", "w", encoding="UTF-8"), indent=2)

def addUserUsage(uid:str):
  return ""

def changeDateFmt(dt:datetime):
  return datetime.datetime.strftime(dt, "%Y%m%d")

@app.route("/") # api 서버 접속 시
def index():
  return "Hello, world!"

@app.post("/api/welcome") # 환영 메시지
def api_welcome():
  req = request.get_json()
  res = {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "simpleText": {
            "text": "<환영 메시지>" # TODO : 환영 메시지 입력
          }
        },
        {
          "textCard": {
            "text": "<급식 확인 메시지>", # TODO : 급식 확인 메시지 입력
            "buttons": [
              {
                "label": "급식 확인하기",
                "action": "block",
                "blockId": "<급식 확인 블록>" # TODO : 급식 확인 블록 연결
              }
            ]
          }
        }
      ]
    }
  }
  if not reqOrg(req).uid in data: # TODO : 만약 학교 설정이 되어 있지 않다면
    res["template"]["outputs"][1] = {
      "textCard": {
        "text": "<학교 선택 메시지>", # TODO : 학교 설정 메시지 입력
        "buttons": [
          {
            "label": "학교 설정하기",
            "action": "block",
            "blockId": "64e0422042d25178766f4ba3" # TODO : 학교 설정 블록 연결
          }
        ]
      }
    }
  return res

@app.post("/api/setup") # 학교 설정
def api_setup():
  req = request.get_json()
  isUserInData(reqOrg(req).uid)
  # ! print((f'{req}').replace("'", "\""))
  imData = json.loads(requests.get(f"https://open.neis.go.kr/hub/schoolInfo?Key={os.environ['NEIS_KEY']}&Type=json&pIndex=1&pSize=10&SCHUL_NM={reqOrg(req).params['sys_text']}").text)
  # ! print(imData)
  if not "schoolInfo" in imData:
    res = {
      "version": "2.0",
      "template": {
        "outputs": [
          {
            "simpleText": {
              "text": "해당하는 이름의 학교가 없습니다.\n다시 시도해주세요."
            }
          }
        ]
      }
    }
    return res
  res = {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "listCard": {
            "header": {
              "title": "해당하는 학교를 선택해주세요."
            },
            "items": []
          }
        }
      ],
      "quickReplies": []
    }
  }
  for i in imData["schoolInfo"][1]["row"]:
    (res["template"]["outputs"][0]["listCard"]["items"]).append({
      "title": i["SCHUL_NM"],
      "description": i["ORG_RDNMA"]
    })
    (res["template"]["quickReplies"]).append({
      "label": i["SCHUL_NM"],
      "action": "block",
      "blockId": "64e0ce2d42d25178766f4dde",
      "extra": {
        "sname": i["SCHUL_NM"],
        "sid": [i["ATPT_OFCDC_SC_CODE"], i["SD_SCHUL_CODE"]]
      }
    })
  # ! print(res)
  return res

@app.post("/api/sredir")
def api_sredir():
  req = request.get_json()
  uid = reqOrg(req).uid
  isUserInData(uid)
  data[uid]["schoolId"] = reqOrg(req).clientExtra["sid"]
  json.dump(data, open("src/data.json", "w", encoding="UTF-8"), indent=2)
  (data[uid]["schoolFav"]).append(reqOrg(req).clientExtra["sid"])
  json.dump(data, open("src/data.json", "w", encoding="UTF-8"), indent=2)
  res = {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "simpleText": {
            "text": f"\"{reqOrg(req).clientExtra['sname']}\"로 설정되었습니다."
          }
        }
      ]
    }
  }
  return res

@app.route("/api/meal") # 급식 확인
def api_meal():
  req = request.get_json()
  # req_plugin_date = datetime.strptime(params_sys_plugin_date, "%Y-%m-%d")
  # if reqOrg(req).params['sys_date'] in
  data = json.loads(requests.get(f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={os.environ['NEIS_APIKEY']}&Type=json&ATPT_OFCDC_SC_CODE={data[reqOrg(req).uid]['schoolId'][0]}&SD_SCHUL_CODE={data[reqOrg(req).uid]['schoolId'][1]}&MLSV_YMD={reqOrg(req).params['']}", timeout=2).text)
  return ""

@app.route("/api/preferred_meal")
def api_preferred_meal():
  return ""

if __name__ == "__main__":
  app.run("0.0.0.0", 8000, debug=True)