from .data import *
from flask import Blueprint, request
app = Blueprint("back", __name__, url_prefix="/m/api")

from datetime import datetime, timedelta
import dotenv
dotenv.load_dotenv()

import json, os, requests

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
    json.dump(udata, open("src/data/udata.json", mode="w", encoding="UTF-8"), indent=2)

@app.errorhandler(CError)
def errorc(e):
  return {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "basicCard": {
            "title": "오류 발생",
            "description": e.msg,
            "thumbnails": {
              "imageUrl": ""
            }
          }
        }
      ],
      "quickReplies": e.qrs
    }
  }

@app.errorhandler(Exception)
def error(e):
  return {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "basicCard": {
            "title": "오류 발생",
            "description": f"아래와 같은 오류가 발생했습니다.\n\"{e}\"",
            "thumbnails": {
              "imageUrl": ""
            }
          }
        }
      ]
    }
  }

@app.post("/gen/fallback")
def gen_fallback():
  return ""

@app.post("/gen/welcome")
def gen_welcome():
  req = request.get_json()
  udata = json.load(open("src/data/udata.json", encoding="UTF-8"))
  res = {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "simpleText": {
            "text": "안녕하세요, \"급식 먹는 시간\" 입니다.\n저와의 대화를 통해서 학교 급식을 빠르게 알아볼 수 있습니다."
          }
        },
        {
          "textCard": {
            "text": "아래 버튼을 통해 급식을 확인 할 수 있습니다.",
            "buttons": [
              {
                "label": "급식 확인하기",
                "action": "block",
                "blockId": "64e1ae328aa99716412905ce"
              }
            ]
          }
        }
      ]
    }
  }
  if not reqOrg(req).uid in udata:
    res["template"]["outputs"][1] = {
      "textCard": {
        "text": "급식을 확인하려면 먼저 학교를 설정해야 합니다.\n아래 버튼을 통해 학교를 설정해주세요.",
        "buttons": [
          {
            "label": "학교 설정하기",
            "action": "block",
            "blockId": "6506881627093e1145e65d80"
          }
        ]
      }
    }
  return res

@app.post("/gen/goweb")
def gen_goweb():
  req = request.get_json()
  return {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "textCard": {
            "text": "아래 버튼을 눌러 웹사이트로 이동하실 수 있습니다.",
            "buttons": [
              {
                "label": "바로가기",
                "action": "webLink",
                "webLinkUrl": f"https://khw2.kr/m/?uid={reqOrg(req).uid}"
              }
            ]
          }
        }
      ]
    }
  }

@app.post("/sch/check")
def sch_check():
  req = request.get_json()
  isUserInData(req)
  udata = json.load(open("src/data/udata.json", encoding="UTF-8"))
  uid = reqOrg(req).uid
  res = {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "simpleText": {
            "text": ""
          }
        }
      ],
      "quickReplies": [
        {
          "label": "확인",
          "action": "block",
          "blockId": "64e0422042d25178766f4ba3"
        },
        {
          "label": "취소",
          "action": "message",
          "messageText": "취소"
        }
      ]
    }
  }
  if udata[uid]["schoolId"][0] == None or udata[uid]["schoolId"][1] == None:
    res["template"]["outputs"][0]["simpleText"]["text"] = "현재 학교가 설정되어 있지 않습니다.\n학교를 설정하시겠습니까?"
  else:
    imData = json.loads(requests.get(f"https://open.neis.go.kr/hub/schoolInfo?KEY={os.environ['NEIS_KEY']}&Type=json&ATPT_OFCDC_SC_CODE={udata[reqOrg(req).uid]['schoolId'][0]}&SD_SCHUL_CODE={udata[reqOrg(req).uid]['schoolId'][1]}").text)
    if not "schoolInfo" in imData:
      res["template"]["outputs"][0]["simpleText"]["text"] = "현재 오류로 인하여 학교가 설정되었지만, 학교를 확인할 수 없습니다.\n학교를 재설정하시겠습니까?"
    else:
      res["template"]["outputs"][0]["simpleText"]["text"] = f"이미 학교가 \"{imData['schoolInfo'][1]['row'][0]['SCHUL_NM']}\"로 설정되어 있습니다.\n학교를 재설정하시겠습니까?"
  return res

@app.post("/sch/setup")
def sch_setup():
  req = request.get_json()
  isUserInData(req)
  schData = json.loads(requests.get(f"https://open.neis.go.kr/hub/schoolInfo?Key={os.environ['NEIS_KEY']}&Type=json&pIndex=1&pSize=10&SCHUL_NM={reqOrg(req).params['sys_text']['origin']}").text)
  if not "schoolInfo" in schData:
    return {
      "version": "2.0",
      "template": {
        "outputs": [
          {
            "simpleText": {
              "text": "해당하는 이름의 학교가 없습니다.\n다시 시도해주세요."
            }
          }
        ],
      "quickReplies": [
        {
          "label": "재시도",
          "action": "block",
          "blockId": "64e0422042d25178766f4ba3?scenarioId=64e0ce1242d25178766f4ddc"
        }
      ]
      }
    }
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
  for i in schData["schoolInfo"][1]["row"]:
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
  return res

@app.post("/sch/result")
def sch_result():
  req = request.get_json()
  isUserInData(req)
  udata = json.load(open("src/data/udata.json", encoding="UTF-8"))
  udata[reqOrg(req).uid]["schoolId"] = reqOrg(req).clientExtra["sid"]
  json.dump(udata, open("src/data/udata.json", "w", encoding="UTF-8"), indent=2)
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
      "quickReplies": [
        {
          "label": "급식 확인하기",
          "action": "block",
          "blockId": "64e1ae328aa99716412905ce"
        }
      ]
    }
  }
  return res

@app.post("/meal/get")
def meal_get():
  req = request.get_json()
  isUserInData(req)
  udata = json.load(open("src/data/udata.json", encoding="UTF-8"))
  uid = reqOrg(req).uid
  if udata[uid]["schoolId"][0] == None or udata[uid]["schoolId"][1] == None:
    raise CError("학교 설정이 되어 있지 않습니다.\n학교 설정 후에 기능을 이용 할 수 있습니다.", [{"label": "학교 설정하기", "action": "block", "blockId": "6506881627093e1145e65d80"}])
  val2Date = { # TODO : 이 부분 최적화 필요
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
  val2Days = {
    "월요일": val2Week["이번주"][0],
    "화요일": val2Week["이번주"][1],
    "수요일": val2Week["이번주"][2],
    "목요일": val2Week["이번주"][3],
    "금요일": val2Week["이번주"][4],
    "토요일": val2Week["이번주"][5],
    "일요일": val2Week["이번주"][6],
    "다음주 월요일": val2Week["다음주"][0],
    "다음주 화요일": val2Week["다음주"][1],
    "다음주 수요일": val2Week["다음주"][2],
    "다음주 목요일": val2Week["다음주"][3],
    "다음주 금요일": val2Week["다음주"][4],
    "다음주 토요일": val2Week["다음주"][5],
    "다음주 일요일": val2Week["다음주"][6],
    "저번주 월요일": val2Week["저번주"][0],
    "저번주 화요일": val2Week["저번주"][1],
    "저번주 수요일": val2Week["저번주"][2],
    "저번주 목요일": val2Week["저번주"][3],
    "저번주 금요일": val2Week["저번주"][4],
    "저번주 토요일": val2Week["저번주"][5],
    "저번주 일요일": val2Week["저번주"][6]
  }
  if "date" in reqOrg(req).clientExtra:
    if reqOrg(req).clientExtra["date"] in val2Date:
      return regularMealRes(req, val2Date[reqOrg(req).clientExtra["date"]], reqOrg(req).clientExtra["date"])
    if reqOrg(req).clientExtra["date"] in val2Week:
      return carouselMealRes(req, val2Week[reqOrg(req).clientExtra["date"]], reqOrg(req).clientExtra["date"])
  if not "bot_date" in reqOrg(req).params:
    if datetime.now().hour >= 20:
      return regularMealRes(req, val2Date["내일"], "내일")
    else:
      return regularMealRes(req, val2Date["오늘"], "오늘")
  elif reqOrg(req).params["bot_date"]["value"] in val2Date:
    return regularMealRes(req, val2Date[reqOrg(req).params["bot_date"]["value"]], reqOrg(req).params["bot_date"]["value"])
  elif reqOrg(req).params["bot_date"]["value"] in val2Week:
    return carouselMealRes(req, val2Week[reqOrg(req).params["bot_date"]["value"]], reqOrg(req).params["bot_date"]["value"])
  elif reqOrg(req).params["bot_date"]["value"] in val2Days:
    return regularMealRes(req, val2Days[reqOrg(req).params["bot_date"]["value"]])
  else:
    try:
      return regularMealRes(req, datetime.strptime(f"{datetime.now().year}년 {reqOrg(req).params['bot_date']['origin']}", "%Y년 %m월 %d일"))
    except ValueError:
      raise CError("올바르지 않은 값이 전달되었습니다.", [{"label": "재시도", "action": "block", "": "64e1ae328aa99716412905ce"}])

@app.post("/meal/plugin")
def meal_plugin():
  req = request.get_json()
  return regularMealRes(req, datetime.strptime(reqOrg(req).params["sys_plugin_date"]["origin"], "%Y-%m-%d"))

@app.post("/meal/fav")
def meal_fav():
  req = request.get_json()
  isUserInData(req)
  res = {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "textCard": {
            "text": "아래 버튼의 페이지에서 선호 급식 메뉴 키워드를 설정하실 수 있습니다.",
            "buttons": [
              {
                "action": "webLink",
                "label": "바로가기",
                "webLinkUrl": f"https://khw2.kr/m/config/{reqOrg(req).uid}"
              }
            ]
          }
        }
      ]
    }
  }
  return res

@app.post("/meal/allergy") # TODO : make meal_allergy
def meal_allergy():
  return ""

@app.post("/meal/bestsel")
def meal_bestsel():
  req = request.get_json()
  if (not "dt" in reqOrg(req).clientExtra) or (not "opt" in reqOrg(req).clientExtra) or (not "meal" in reqOrg(req).clientExtra):
    raise CError("올바르지 않은 값이 전달되었습니다.")
  if (reqOrg(req).clientExtra["dt"] != changeDateFmt(datetime.now())) and (reqOrg(req).clientExtra["dt"] != changeDateFmt(datetime.now()-timedelta(1))):
    raise CError("올바르지 않은 날짜가 전달되었습니다.")
  mealArr = (reqOrg(req).clientExtra["meal"]).split("\n")
  res = {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "simpleText": {
            "text": f"{reqOrg(req).clientExtra['opt']}의 베스트 메뉴를 아래 메뉴를 통해 하나를 선택해주세요.\n\n※ \"취소\" 를 보내 선택을 취소할 수 있습니다."
          }
        }
      ],
      "quickReplies": []
    }
  }
  for i in mealArr:
    (res["template"]["quickReplies"]).append({
      "label": i.rstrip(" "),
      "action": "block",
      "blockId": "6522424988c60e498232e41e",
      "extra": {
        "meal": i.rstrip(" ")
      }
    })
  return res

@app.post("/meal/bestres")
def api_bmres():
  req = request.get_json()
  mdata = json.load(open("src/data/mdata.json", encoding="UTF-8"))
  tMonth = datetime.strftime(datetime.now(), "%Y-%m")
  try:
    mdata_month = json.load(open(f"src/data/mdata.{tMonth}.json", encoding="UTF-8"))
  except FileNotFoundError or json.decoder.JSONDecodeError:
    with open(f"src/data/mdata.{datetime.strftime(datetime.now(), '%Y-%m')}.json", "w", encoding="UTF-8") as file:
      file.write("{}")
      file.close()
    mdata_month = json.load(open(f"src/data/mdata.{datetime.strftime(datetime.now(), '%Y-%m')}.json", encoding="UTF-8"))
  if not "meal" in reqOrg(req).clientExtra:
    raise CError("올바르지 않은 값이 전달되었습니다.\n")
  if not reqOrg(req).clientExtra["meal"].rstrip(" ") in mdata:
    mdata[reqOrg(req).clientExtra["meal"].rstrip(" ")] = {"score": []}
  if not reqOrg(req).clientExtra["meal"].rstrip(" ") in mdata_month:
      mdata_month[reqOrg(req).clientExtra["meal"].rstrip(" ")] = {"score": []}
  for key, val in mdata.items():
    for i in val["score"]:
      if reqOrg(req).uid in i and i[reqOrg(req).uid] == changeDateFmt(datetime.now()):
        return {
          "version": "2.0",
          "template": {
            "outputs": [
              {
                "textCard": {
                  "text": "오늘은 이미 베스트 메뉴를 선택하셨습니다. 내일 다시 시도해 주시기 바랍니다.\n아래 버튼을 통해 베스트 메뉴 순위를 확인해보세요.",
                  "buttons": [
                    {
                      "action": "webLink",
                      "label": "바로가기",
                      "webLinkUrl": f"https://khw2.kr/m/rank?uid={reqOrg(req).uid}"
                    }
                  ]
                }
              }
            ]
          }
        }
  mdata[reqOrg(req).clientExtra["meal"].rstrip(" ")]["score"].append({reqOrg(req).uid: changeDateFmt(datetime.now())})
  json.dump(mdata, open("src/data/mdata.json", "w", encoding="UTF-8"), indent=2)
  mdata_month[reqOrg(req).clientExtra["meal"].rstrip(" ")]["score"].append({reqOrg(req).uid: changeDateFmt(datetime.now())})
  json.dump(mdata_month, open(f"src/data/mdata.{tMonth}.json", "w", encoding="UTF-8"), indent=2)
  return {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "textCard": {
            "text": f"{korED(reqOrg(req).clientExtra['meal'].rstrip(' '))} 베스트 메뉴로 선택하셨습니다.\n아래 버튼을 통해 베스트 메뉴 순위를 확인해보세요.",
            "buttons": [
              {
                "action": "webLink",
                "label": "바로가기",
                "webLinkUrl": f"https://khw2.kr/m/rank?uid={reqOrg(req).uid}"
              }
            ]
          }
        }
      ]
    }
  }

@app.post("/meal/rank")
def meal_rank():
  req = request.get_json()
  isUserInData(req)
  res = {
    "version": "2.0",
    "template": {
      "outputs": [
        {
          "textCard": {
            "text": "아래 버튼의 페이지에서 급식 순위를 확인 할 수 있습니다.",
            "buttons": [
              {
                "action": "webLink",
                "label": "바로가기",
                "webLinkUrl": f"https://khw2.kr/m/rank?uid={reqOrg(req).uid}"
              }
            ]
          }
        }
      ]
    }
  }
  return res
