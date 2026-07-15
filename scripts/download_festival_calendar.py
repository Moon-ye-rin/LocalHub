import json
from pathlib import Path

import requests

####################################################
# 공공데이터포털 일반(Decoding) 서비스키 입력
####################################################
SERVICE_KEY = "bJD/KNyNug/+KunrXE3Conzyp5zb2cqrIhAw8MSdyc1z3GdfTnKc6jLPDyQW6pi1gMo1wETozU+0XvuBQ2hg8w=="
####################################################

URL = "https://apis.data.go.kr/B551011/KorService2/searchFestival2"

COMMON_PARAMS = {
    "serviceKey": SERVICE_KEY,
    "MobileOS": "ETC",
    "MobileApp": "LocalHub",
    "_type": "json",
    "numOfRows": 100,
    "eventStartDate": "20260101",   # 2026-07-01 이후 시작 행사
}

AREAS = {
    "서울": 1,
    "경기": 31,
}


def download_festival(region_name, area_code):

    page = 1
    results = []

    while True:

        params = COMMON_PARAMS.copy()
        params["areaCode"] = area_code
        params["pageNo"] = page

        response = requests.get(URL, params=params)

        if response.status_code != 200:
            print(f"{region_name} API 호출 실패")
            print(response.text)
            return

        data = response.json()

        header = data["response"]["header"]

        if header["resultCode"] != "0000":
            print(header["resultMsg"])
            return

        body = data["response"]["body"]

        total = body["totalCount"]

        if body["items"] == "":
            break

        items = body["items"]["item"]

        if isinstance(items, dict):
            items = [items]

        results.extend(items)

        print(f"{region_name} : {page}페이지 ({len(results)}/{total})")

        if len(results) >= total:
            break

        page += 1

    ####################################################
    # 기존 응답 그대로 저장
    ####################################################

    output = {
        "region": region_name,
        "contentType": "축제공연행사",
        "contentTypeId": 15,
        "eventStartDate": COMMON_PARAMS["eventStartDate"],
        "items": results
    }

    ####################################################
    # 저장 위치
    ####################################################

    BASE_DIR = Path(__file__).resolve().parent.parent

    save_dir = (
        BASE_DIR
        / "backend"
        / "app"
        / "data"
        / "calendar"
    )

    save_dir.mkdir(parents=True, exist_ok=True)

    save_path = save_dir / f"{region_name}_행사일정.json"

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print(f"\n{save_path.name} 저장 완료 ({len(results)}건)\n")


if __name__ == "__main__":

    for region_name, area_code in AREAS.items():
        download_festival(region_name, area_code)

    print("=" * 60)
    print("서울 · 경기 행사 데이터 저장 완료")
    print("=" * 60)