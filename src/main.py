from flask import Blueprint, request
app = Blueprint("meal", __name__, url_prefix="/meal")

from datetime import datetime, timedelta
import dotenv
dotenv.load_dotenv()

import json
data = json.load(open("src/data.json", encoding="UTF-8"))
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
  def __init__(self, req:dict, dt:datetime, days:str|None=None):
    mealData = json.loads(requests.get(f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={os.environ['NEIS_KEY']}&Type=json&ATPT_OFCDC_SC_CODE={data[reqOrg(req).uid]['schoolId'][0]}&SD_SCHUL_CODE={data[reqOrg(req).uid]['schoolId'][1]}&MLSV_YMD={changeDateFmt(dt)}").text)
    if "mealServiceDietInfo" in mealData:
      mealDataPrs = re.sub("[0-9#.]+", "", (mealData["mealServiceDietInfo"][1]["row"][0]["DDISH_NM"]).replace("<br/>", "\n")).replace("()", "")
    else:
      mealDataPrs = "급식 데이터가 없습니다."
    if days == None:
      self.meal = {
        "version": "2.0",
        "template": {
          "outputs": [
            {
              "basicCard": {
                "title": f"{dt.year}년 {dt.month}월 {dt.day}일 {daysData[datetime(dt.year, dt.month, dt.day).weekday()]}요일",
                "description": mealDataPrs,
                "thumbnail": {
                  "imageUrl": ""
                }
              }
            }
          ],
          "quickReplies": []
        }
      }
    else:
      self.meal = {
        "version": "2.0",
        "template": {
          "outputs": [
            {
              "basicCard": {
                "title": f"{dt.year}년 {dt.month}월 {dt.day}일 {daysData[datetime(dt.year, dt.month, dt.day).weekday()]}요일 ({days})",
                "description": mealDataPrs,
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
    for i in dt:
      mealData = json.loads(requests.get(f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={os.environ['NEIS_KEY']}&Type=json&ATPT_OFCDC_SC_CODE={data[reqOrg(req).uid]['schoolId'][0]}&SD_SCHUL_CODE={data[reqOrg(req).uid]['schoolId'][1]}&MLSV_YMD={changeDateFmt(i)}").text)
      # ! print((f'{mealData}').replace("'", "\""))
      if "mealServiceDietInfo" in mealData:
        mealDataPrs = re.sub("[0-9#.]+", "", (mealData["mealServiceDietInfo"][1]["row"][0]["DDISH_NM"]).replace("<br/>", "\n")).replace("()", "")
      else:
        mealDataPrs = "급식 데이터가 없습니다."
      (self.meal["template"]["outputs"][0]["carousel"]["items"]).append({
        "title": f"{i.year}년 {i.month}월 {i.day}일 {daysData[datetime(i.year, i.month, i.day).weekday()]}요일",
        "description": mealDataPrs,
        "thumbnail": {
          "imageUrl": ""
        }
      })

def isUserInData(req:dict):
  # ! print(f"A : {type(reqOrg(req).uid)} {reqOrg(req).uid}")
  if not reqOrg(req).uid in data:
    # ! print("B")
    data[reqOrg(req).uid] = {
      "schoolId": [None, None],
      "schoolFav": [],
      "mealFav": [],
      "settings": {
        "allergicMeal": False,
        "notifMeal": False
      },
      "usage": 0
    }
    json.dump(data, open("src/data.json", "w", encoding="UTF-8"), indent=2)

def addUserUsage(uid:str):
  return ""

def bool8Time()->bool:
  """현재 시간이 18시를 지났다면 True 리턴"""
  if datetime.now().hour >= 18:
    return True
  else:
    return False

def changeDateFmt(dt:datetime):
  return datetime.strftime(dt, "%Y%m%d")

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
  isUserInData(req)
  # ! print((f'{req}').replace("'", "\""))
  imData = json.loads(requests.get(f"https://open.neis.go.kr/hub/schoolInfo?Key={os.environ['NEIS_KEY']}&Type=json&pIndex=1&pSize=10&SCHUL_NM={reqOrg(req).params['sys_text']['origin']}").text)
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
  isUserInData(req)
  uid = reqOrg(req).uid
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
  isUserInData(req)
  uid = reqOrg(req).uid
  if data[uid]["schoolId"][0] == None or data[uid]["schoolId"][1] == None:
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
    "이번주": [datetime.now() + timedelta(-int(datetime.now().weekday())+i) for i in range(6)],
    "다음주": [datetime.now() + timedelta(-int(datetime.now().weekday())+7+i) for i in range(6)],
    "저번주": [datetime.now() + timedelta(-(int(datetime.now().weekday())+7)+i) for i in range(6)]
  }
  if "date" in reqOrg(req).clientExtra:
    mealData = json.loads(requests.get(f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={os.environ['NEIS_KEY']}&Type=json&ATPT_OFCDC_SC_CODE={data[reqOrg(req).uid]['schoolId'][0]}&SD_SCHUL_CODE={data[reqOrg(req).uid]['schoolId'][1]}&MLSV_YMD={changeDateFmt(reqOrg(req).clientExtra['date'])}").text)
    if "mealServiceDietInfo" in mealData:
      mealDataPrs = re.sub("[0-9#.]+", "", (mealData["mealServiceDietInfo"][1]["row"][0]["DDISH_NM"]).replace("<br/>", "\n")).replace("()", "")
    else:
      mealDataPrs = "급식 데이터가 없습니다."
    return regularMealRes(req, reqOrg(req).clientExtra["date"]).meal
    # {
    #   "version": "2.0",
    #   "template": {
    #     "outputs": [
    #       {
    #         "basicCard": {
    #           "title": f"{val2Date['내일'].year}년 {val2Date['내일'].month}월 {val2Date['내일'].day}일 {daysData[datetime(val2Date['내일'].year, val2Date['내일'].month, val2Date['내일'].day).weekday()]}요일",
    #           "description": mealDataPrs,
    #           "thumbnail": {
    #             "imageUrl": ""
    #           }
    #         }
    #       }
    #     ],
    #     "quickReplies": [
    #       {
    #         "label": "오늘 급식 확인하기",
    #         "action": "block",
    #         "blockId": "64e1ae328aa99716412905ce",
    #         "extra": {
    #           "date": val2Date["오늘"]
    #         }
    #       },
    #       {
    #         "label": "이번주 급식 확인하기",
    #         "action": "block",
    #         "blockId": "64e1ae328aa99716412905ce",
    #         "extra": {
    #           "date": val2Week["이번주"]
    #         }
    #       },
    #       {
    #         "label": "특정 날짜의 급식 확인하기",
    #         "action": "block",
    #         "blockId": "64e1afb7a6b5503755568189"
    #       }
    #     ]
    #   }
    # }
  if not "bot_date" in reqOrg(req).params:
    if bool8Time():
      mealData = json.loads(requests.get(f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={os.environ['NEIS_KEY']}&Type=json&ATPT_OFCDC_SC_CODE={data[reqOrg(req).uid]['schoolId'][0]}&SD_SCHUL_CODE={data[reqOrg(req).uid]['schoolId'][1]}&MLSV_YMD={changeDateFmt(val2Date['내일'])}").text)
      if "mealServiceDietInfo" in mealData:
        mealDataPrs = re.sub("[0-9#.]+", "", (mealData["mealServiceDietInfo"][1]["row"][0]["DDISH_NM"]).replace("<br/>", "\n")).replace("()", "")
      else:
        # ! print("Y")
        mealDataPrs = "급식 데이터가 없습니다."
      return {
        "version": "2.0",
        "template": {
          "outputs": [
            {
              "basicCard": {
                "title": f"{val2Date['내일'].year}년 {val2Date['내일'].month}월 {val2Date['내일'].day}일 {daysData[datetime(val2Date['내일'].year, val2Date['내일'].month, val2Date['내일'].day).weekday()]}요일 (내일)",
                "description": mealDataPrs,
                "thumbnail": {
                  "imageUrl": ""
                }
              }
            }
          ],
          "quickReplies": [
            {
              "label": "오늘 급식 확인하기",
              "action": "block",
              "blockId": "64e1ae328aa99716412905ce",
              "extra": {
                "date": val2Date["오늘"]
              }
            },
            {
              "label": "이번주 급식 확인하기",
              "action": "block",
              "blockId": "64e1ae328aa99716412905ce",
              "extra": {
                "date": val2Week["이번주"]
              }
            },
            {
              "label": "특정 날짜의 급식 확인하기",
              "action": "block",
              "blockId": "64e1afb7a6b5503755568189"
            }
          ]
        }
      }
    else:
      mealData = json.loads(requests.get(f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={os.environ['NEIS_KEY']}&Type=json&ATPT_OFCDC_SC_CODE={data[reqOrg(req).uid]['schoolId'][0]}&SD_SCHUL_CODE={data[reqOrg(req).uid]['schoolId'][1]}&MLSV_YMD={changeDateFmt(val2Date['오늘'])}").text)
      if "mealServiceDietInfo" in mealData:
        mealDataPrs = re.sub("[0-9#.]+", "", (mealData["mealServiceDietInfo"][1]["row"][0]["DDISH_NM"]).replace("<br/>", "\n")).replace("()", "")
      else:
        # ! print("Y")
        mealDataPrs = "급식 데이터가 없습니다."
      return {
        "version": "2.0",
        "template": {
          "outputs": [
            {
              "basicCard": {
                "title": f"{val2Date['오늘'].year}년 {val2Date['오늘'].month}월 {val2Date['오늘'].day}일 {daysData[datetime(val2Date['오늘'].year, val2Date['오늘'].month, val2Date['오늘'].day).weekday()]}요일 (오늘)",
                "description": mealDataPrs,
                "thumbnail": {
                  "imageUrl": ""
                }
              }
            }
          ],
          "quickReplies": [
            {
              "label": "내일 급식 확인하기",
              "action": "block",
              "blockId": "",
              "extra": {
                "date": val2Date["내일"]
              }
            },
            {
              "label": "이번주 급식 확인하기",
              "action": "block",
              "blockId": "",
              "extra": {
                "date": val2Week["이번주"]
              }
            },
            {
              "label": "특정 날짜의 급식 확인하기",
              "action": "block",
              "blockId": "64e1afb7a6b5503755568189"
            }
          ]
        }
      }
  elif reqOrg(req).params["bot_date"]["value"] in val2Date:
    # mealDtVal = val2Date[reqOrg(req).params["bot_date"]["value"]]
    return regularMealRes(req, val2Date[reqOrg(req).params["bot_date"]["value"]], reqOrg(req).params["bot_date"]["value"]).meal
  elif reqOrg(req).params["bot_date"]["value"] in val2Week: # TODO : 특정 주 급식 출력
    return carouselMealRes(req, val2Week[reqOrg(req).params["bot_date"]["value"]]).meal
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

@app.post("/api/mplugin") # 급식 확인 플러그인
def api_mplugin():
  req = request.get_json()
  return regularMealRes(req, datetime.strptime(reqOrg(req).params["sys_plugin_date"]["origin"], "%Y-%m-%d")).meal

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