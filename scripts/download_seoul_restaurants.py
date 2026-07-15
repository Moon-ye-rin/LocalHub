import json
from pathlib import Path

import requests

#######################################################
# 공공데이터포털에서 발급받은 일반(Decoding) 서비스키 입력
#######################################################

SERVICE_KEY = "bJD/KNyNug/+KunrXE3Conzyp5zb2cqrIhAw8MSdyc1z3GdfTnKc6jLPDyQW6pi1gMo1wETozU+0XvuBQ2hg8w=="

#######################################################

URL = "https://apis.data.go.kr/B551011/KorService2/areaBasedList2"

PARAMS = {
    "serviceKey": SERVICE_KEY,
    "MobileOS": "ETC",
    "MobileApp": "LocalHub",
    "_type": "json",
    "numOfRows": 100,
    "contentTypeId": 39,      # 음식점
    "areaCode": 1             # 서울
}


def download():
    page = 1
    result = []

    while True:

        PARAMS["pageNo"] = page

        response = requests.get(URL, params=PARAMS)

        data = response.json()

        body = data["response"]["body"]

        total = body["totalCount"]

        if body["items"] == "":
            break

        items = body["items"]["item"]

        if isinstance(items, dict):
            items = [items]

        result.extend(items)

        print(f"{page}페이지 ({len(result)}/{total})")

        if len(result) >= total:
            break

        page += 1

    BASE_DIR = Path(__file__).resolve().parent.parent

    save_path = BASE_DIR / "backend" / "app" / "data" / "seoul" / "서울_음식점.json"
    save_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
    "region": "서울",
    "contentType": "음식점",
    "contentTypeId": 39,
    "items": result,
    }

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print("서울 음식점 저장 완료")


if __name__ == "__main__":
    download()