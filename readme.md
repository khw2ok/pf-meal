# 학교 급식 챗봇
[http://pf.kakao.com/_Mxhxaxdxj](http://pf.kakao.com/_Mxhxaxdxj)

학생들의 편의성을 위해 학교 외의 장소에서도 급식에 대한 정보를 확인 할 수 있도록 하는 Python Flask로 제작된 웹 어플리케이션, 프로젝트입니다.

## 프로젝트 구성
```
├─ .venv
├─ src
│   ├─ data
│   │   │  mdata.*.json
│   │   │  mdata.json
│   │   └─ udata.json
│   │  back.py
│   │  front.py
│   └─ init.py
├─ static
│   └─ index.js
├─ templates
├─ test
│  .env
│  .gitignore
│  readme.md
│  reqiuirements.txt
│  run.py
└─ tailwind.config.js
```

```bash
$ python run.py
```

## 이용된 API
- NEIS API : 급식 정보 및 학교 정보 확인
