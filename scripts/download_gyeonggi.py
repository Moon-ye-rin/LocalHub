import json
from pathlib import Path

import requests

#######################################################
# 공공데이터포털에서 발급받은 일반(Decoding) 서비스키 입력
#######################################################

SERVICE_KEY = "bJD/KNyNug/+KunrXE3Conzyp5zb2cqrIhAw8MSdyc1z3GdfTnKc6jLPDyQW6pi1gMo1wETozU+0XvuBQ2hg8w=="

#######################################################

URL = "https://apis.data.go.kr/B551011/KorService2/areaBasedList2"

CONTENT_TYPES = {
    "관광지": 12,
    "문화시설": 14,
    "축제공연행사": 15,
    "여행코스": 25,
    "레포츠": 28,
    "숙박": 32,
    "쇼핑": 38,
    "음식점": 39
}


def download(content_name, content_id):

    params = {
        "serviceKey": SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "LocalHub",
        "_type": "json",
        "areaCode": 31,          # 경기
        "contentTypeId": content_id,
        "numOfRows": 100
    }

    page = 1
    result = []

    while True:

        params["pageNo"] = page

        response = requests.get(URL, params=params)

        data = response.json()

        body = data["response"]["body"]

        total = body["totalCount"]

        if body["items"] == "":
            break

        items = body["items"]["item"]

        if isinstance(items, dict):
            items = [items]

        result.extend(items)

        print(f"{content_name} : {page}페이지 ({len(result)}/{total})")

        if len(result) >= total:
            break

        page += 1

    BASE_DIR = Path(__file__).resolve().parent.parent

    save_path = (
        BASE_DIR
        / "backend"
        / "app"
        / "data"
        / "gyeonggi"
        / f"경기_{content_name}.json"
    )

    save_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
    "region": "경기",
    "contentType": content_name,
    "contentTypeId": content_id,
    "items": result,
    }  

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print(f"경기_{content_name}.json 저장 완료\n")


if __name__ == "__main__":

    for name, cid in CONTENT_TYPES.items():
        download(name, cid)

    print("모든 경기 데이터 저장 완료")