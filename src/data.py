from datetime import datetime, timedelta
import dotenv

import json, os, re, requests

daysData = ["월", "화", "수", "목", "금", "토", "일"]
mQRRes = {
  "오늘": [
    {
      "label": "내일 급식",
      "action": "block",
      "blockId": "64e1ae328aa99716412905ce",
      "extra": {
        "date": "내일"
      }
    },
    {
      "label": "이번주 급식",
      "action": "block",
      "blockId": "64e1ae328aa99716412905ce",
      "extra": {
        "date": "이번주"
      }
    },
    {
      "label": "특정 날짜의 급식",
      "action": "block",
      "blockId": "64e1afb7a6b5503755568189"
    }
  ],
  "이번주": [
    {
      "label": "오늘 급식",
      "action": "block",
      "blockId": "64e1ae328aa99716412905ce",
      "extra": {
        "date": "오늘"
      }
    },
    {
      "label": "다음주 급식",
      "action": "block",
      "blockId": "64e1ae328aa99716412905ce",
      "extra": {
        "date": "다음주"
      }
    },
    {
      "label": "특정 날짜의 급식",
      "action": "block",
      "blockId": "64e1afb7a6b5503755568189"
    }
  ],
  "기타": [
    {
      "label": "오늘 급식",
      "action": "block",
      "blockId": "64e1ae328aa99716412905ce",
      "extra": {
        "date": "오늘"
      }
    },
    {
      "label": "이번주 급식",
      "action": "block",
      "blockId": "64e1ae328aa99716412905ce",
      "extra": {
        "date": "이번주"
      }
    },
    {
      "label": "특정 날짜의 급식",
      "action": "block",
      "blockId": "64e1afb7a6b5503755568189"
    }
  ],
}

class CError(Exception):
  def __init__(self, msg:str, qrs:list=[]):
    self.msg = msg
    self.qrs = qrs
    super().__init__(self.msg)

class reqOrg:
  def __init__(self, req:dict):
    self.uid:str = req["userRequest"]["user"]["id"]
    self.utterance:str = req["userRequest"]["utterance"]
    self.params:dict = req["action"]["detailParams"]
    self.clientExtra:dict = req["action"]["clientExtra"]

def regularMealRes(req:dict, dt:datetime, opt:str|None=None):
  mealData = getMealData(req, dt)
  meal = {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "basicCard": {
            "title": f"{dt.year}년 {dt.month}월 {dt.day}일 {daysData[datetime(dt.year, dt.month, dt.day).weekday()]}요일",
            "description": mealData,
            "thumbnail": {
              "imageUrl": ""
            },
            "forwardable": True
          }
        }
      ],
      "quickReplies": mQRRes["기타"]
    }
  }
  if opt != None:
    meal["template"]["outputs"][0]["basicCard"]["title"] = f"{dt.year}년 {dt.month}월 {dt.day}일 {daysData[datetime(dt.year, dt.month, dt.day).weekday()]}요일 ({opt})"
    if opt in mQRRes:
      meal["template"]["quickReplies"] = mQRRes[opt]
    if opt in ["오늘", "어제"] and mealData != "급식 정보가 없습니다.":
      (meal["template"]["outputs"]).append({
        "textCard": {
          "text": f"{opt}의 베스트 메뉴를 선택해주세요.",
          "buttons": [
            {
              "label": "바로가기",
              "action": "block",
              "blockId": "65223a604f3e9c3d821a38f4", # ! 여기 제대로 만들어야 함
              "extra": {
                "dt": opt,
                "meal": re.sub(r"\((.*?)\)", "", mealData)
              }
            }
          ]
        }
      })
  return meal

def carouselMealRes(req:dict, dt:list, opt:str|None=None):
  meal = {
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
      "quickReplies": mQRRes["기타"]
    }
  }
  for i in dt:
    mealData = getMealData(req, i)
    meal["template"]["outputs"][0]["carousel"]["items"].append({
      "title": f"{i.year}년 {i.month}월 {i.day}일 {daysData[datetime(i.year, i.month, i.day).weekday()]}요일",
      "description": mealData,
      "thumbnail": {
        "imageUrl": ""
      }
    })
  if opt in mQRRes:
    meal["template"]["quickReplies"] = mQRRes[opt]
  return meal

def isUserInData(req:dict):
  udata = json.load(open("src/data/udata.json", encoding="UTF-8"))
  if not reqOrg(req).uid in udata:
    udata[reqOrg(req).uid] = {
      "schoolId": [None, None],
      "schoolFav": [],
      "mealFav": [],
      "settings": {
        "allergicMeal": False,
        "notifMeal": False
      },
      "usage": 0
    }
    json.dump(udata, open("src/data/udata.json", "w", encoding="UTF-8"), indent=2)

def changeDateFmt(dt:datetime):
  return datetime.strftime(dt, "%Y%m%d")

def getMealData(req:dict, dt:datetime):
  udata = json.load(open("src/data/udata.json", encoding="UTF-8"))
  mealData = json.loads(requests.get(f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={os.environ['NEIS_KEY']}&Type=json&ATPT_OFCDC_SC_CODE={udata[reqOrg(req).uid]['schoolId'][0]}&SD_SCHUL_CODE={udata[reqOrg(req).uid]['schoolId'][1]}&MLSV_YMD={changeDateFmt(dt)}").text)
  if "mealServiceDietInfo" in mealData:
    mealDataPrs = re.sub("[0-9#.]+", "", (mealData["mealServiceDietInfo"][1]["row"][0]["DDISH_NM"]).replace("<br/>", "\n")).replace("()", "")
    mealDataPrs = updateMealData(req, mealDataPrs)
  else:
    mealDataPrs = "급식 정보가 없습니다."
  return mealDataPrs

def updateMealData(req:dict, meal:str):
  udata = json.load(open("src/data/udata.json", encoding="UTF-8"))
  mealData = meal.split("\n")
  for i in udata[reqOrg(req).uid]["mealFav"]:
    for n, j in enumerate(mealData):
      if i in j: mealData[n] = "❤️ " + j
  return "\n".join(mealData)

def korED(t:str):
  if (ord(t[-1]) - ord('가')) % 28 != 0:
    return f"\"{t}\"을"
  else:
    return f"\"{t}\"를"
