from flask import Flask, request
app = Flask(__name__)

from datetime import datetime, timedelta
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
import re
import requests

class reqOrg:
  def __init__(self, req:dict):
    self.uid:str = req["userRequest"]["user"]["id"]
    self.utterance:str = req["userRequest"]["utterance"]
    self.params:dict = req["action"]["detailParams"]
    self.clientExtra:dict = req["action"]["clientExtra"]

class regularMealRes:
  def __init__(self, req:dict, dt:datetime):
    mealData = json.loads(requests.get(f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={os.environ['NEIS_KEY']}&Type=json&ATPT_OFCDC_SC_CODE={data[reqOrg(req).uid]['schoolId'][0]}&SD_SCHUL_CODE={data[reqOrg(req).uid]['schoolId'][1]}&MLSV_YMD={changeDateFmt(dt)}").text)
    if "mealServiceDietInfo" in mealData:
      mealDataPrs = re.sub("[0-9#.]+", "", (mealData["mealServiceDietInfo"][1]["row"][0]["DDISH_NM"]).replace("<br/>", "\n")).replace("()", "")
    else:
      mealDataPrs = "급식 데이터가 없습니다."
    self.meal = {
      "version": "2.0",
      "template": {
        "outputs": [
          {
            "basicCard": {
              "title": f"{dt.year}년 {dt.month}월 {dt.day}일 {daysData[datetime(dt.year, dt.month, dt.day).weekday()]}요일",
              "description": f"{mealDataPrs}",
              "thumbnail": {
                "imageUrl": ""
              }
            }
          }
        ],
        "quickReplies": []
      }
    }

class carouselMealRes:
  def __init__(self, req:dict, dt:list):
    self.meal = {
      "version": "2.0",
      "template": {
        "outputs": [
          {
            "carousel": {
              "type": "basicCard",
              "items": []
            }
          }
        ],
        "quickReplies": []
      }
    }

def isUserInData(uid:str):
  data = json.load(open("src/data.json", encoding="UTF-8"))
  if not uid in data:
    data[uid] = defaultData
    json.dump(data, open("src/data.json", "w", encoding="UTF-8"), indent=2)
    data = json.load(open("src/data.json", encoding="UTF-8"))

def addUserUsage(uid:str):
  return ""

def changeDateFmt(dt:datetime):
  return datetime.strftime(dt, "%Y%m%d")

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
  imData = json.loads(requests.get(f"https://open.neis.go.kr/hub/schoolInfo?Key={os.environ['NEIS_KEY']}&Type=json&pIndex=1&pSize=10&SCHUL_NM={reqOrg(req).params['sys_text']['origin']}").text)
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
  data = json.load(open("src/data.json", encoding="UTF-8"))
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
      ],
      "quickReplies": [] # TODO : 급식 확인 바로가기 추가
    }
  }
  return res

@app.post("/api/meal") # 급식 확인
def api_meal():
  req = request.get_json()
  uid = reqOrg(req).uid
  isUserInData(uid)
  data = json.load(open("src/data.json", encoding="UTF-8"))
  if data[reqOrg(req).uid]["schoolId"][0] == None or data[reqOrg(req).uid]["schoolId"][1] == None:
    return {
      "version": "2.0",
      "template": {
        "outputs": [
          {
            "basicCard": {
              "title": "오류 발생",
              "description": "학교 설정이 되어 있지 않습니다.\n학교 설정 후에 급식 확인을 할 수 있습니다.",
              "thumbnail": {
                "imageUrl": ""
              }
            }
          }
        ],
        "quickReplies": [
          {
            "label": "학교 설정하기",
            "action": "block",
            "blockId": "64e0422042d25178766f4ba3"
          }
        ]
      }
    }
  val2Date = {
    "오늘": datetime.now(),
    "내일": datetime.now()+timedelta(1),
    "어제": datetime.now()-timedelta(1),
    "모레": datetime.now()+timedelta(2)
  }
  val2Week = {
    "이번주": [datetime.now() + timedelta(-int(datetime.now().weekday())+i) for i in range(7)],
    "다음주": [datetime.now() + timedelta(-int(datetime.now().weekday())+7+i) for i in range(7)],
    "저번주": [datetime.now() + timedelta(-(int(datetime.now().weekday())+7)+i) for i in range(7)]
  }
  # ! print((f'{req}').replace("'", "\""))
  if "date" in reqOrg(req).clientExtra:
    pass
  if not "bot_date" in reqOrg(req).params: # TODO : 어떤 방식으로 급식을 확인하시겠습니까?
    return {} # TODO : 리턴 값 넣기
  elif reqOrg(req).params["bot_date"]["value"] in val2Date:
    # mealDtVal = val2Date[reqOrg(req).params["bot_date"]["value"]]
    return regularMealRes(req, val2Date[reqOrg(req).params["bot_date"]["value"]]).meal
  elif reqOrg(req).params["bot_date"]["value"] in val2Week: # TODO : 특정 주 급식 출력
    return {} # TODO : 리턴 값 넣기
  else:
    try:
      # mealDtVal = datetime.strptime(f"{datetime.now().year}년 {reqOrg(req).params['bot_date']['origin']}", "%Y년 %m월 %d일")
      return regularMealRes(req, datetime.strptime(f"{datetime.now().year}년 {reqOrg(req).params['bot_date']['origin']}", "%Y년 %m월 %d일")).meal
    except ValueError:
      return {
        "version": "2.0",
        "template": {
          "outputs": [
            {
              "basicCard": {
                "title": "오류 발생",
                "description": "올바르지 않은 값이 전달되었습니다.",
                "thumbnail": {
                  "imageUrl": ""
                }
              }
            }
          ],
          "quickReplies": [
            {
              "label": "재시도",
              "action": "block",
              "blockId": "64e1ae328aa99716412905ce"
            }
          ]
        }
      }
  # mealData = json.loads(requests.get(f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={os.environ['NEIS_KEY']}&Type=json&ATPT_OFCDC_SC_CODE={data[reqOrg(req).uid]['schoolId'][0]}&SD_SCHUL_CODE={data[reqOrg(req).uid]['schoolId'][1]}&MLSV_YMD={changeDateFmt(mealDtVal)}").text)
  # if "mealServiceDietInfo" in mealData:
  #   mealDataPrs = re.sub("[0-9#.]+", "", (mealData["mealServiceDietInfo"][1]["row"][0]["DDISH_NM"]).replace("<br/>", "\n")).replace("()", "")
  # else:
  #   mealDataPrs = "급식 데이터가 없습니다."
  # res = {
  #   "version": "2.0",
  #   "template": {
  #     "outputs": [
  #       {
  #         "basicCard": {
  #           "title": f"{mealDtVal.year}년 {mealDtVal.month}월 {mealDtVal.day}일 {daysData[datetime(mealDtVal.year, mealDtVal.month, mealDtVal.day).weekday()]}요일",
  #           "description": f"{mealDataPrs}",
  #           "thumbnail": {
  #             "imageUrl": ""
  #           }
  #         }
  #       }
  #     ],
  #     "quickReplies": []
  #   }
  # }
  # return res

@app.post("/api/config")
def api_config():
  return {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "carousel": {
            "type": "listCard",
            "items": [
              {
                "header": {
                  "title": "학교 관련"
                },
                "items": [
                  {
                    "title": "학교 설정하기",
                    "description": "설정된 학교 변경하기"
                  }
                ],
                "buttons": [
                  {
                    "label": "학교 설정하기"
                  }
                ]
              }
            ]
          }
        }
      ]
    }
  }

@app.post("/api/credir")
def api_credir():
  return ""

if __name__ == "__main__":
  app.run("0.0.0.0", 8000, debug=True)