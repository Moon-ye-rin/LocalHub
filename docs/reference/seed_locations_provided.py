"""
LocalHub - TourAPI JSON 적재 스크립트
서버 기동 시 1회 실행하거나 (FastAPI lifespan), CLI로 직접 실행한다.

    python seed_locations.py ./data      # 서울_*.json 이 들어있는 폴더

공공누리 3유형(변경 금지):
    원본 필드값을 가공하지 않는다. 빈 문자열("")도 그대로 저장한다.
    명세서 3.5가 허용한 mapx/mapy의 float 변환만 수행한다.
"""
from __future__ import annotations

import glob
import json
import os
import sys

from sqlalchemy import func, select

from models import Base, ContentType, Location, SessionLocal, engine

# 원본 items[] 필드 → locations 컬럼 (SCHEMA.md 기준, 이름 그대로)
RAW_FIELDS = [
    "contentid", "contenttypeid", "title", "addr1", "addr2", "zipcode", "tel",
    "mlevel", "areacode", "sigungucode", "lDongRegnCd", "lDongSignguCd",
    "cat1", "cat2", "cat3", "lclsSystm1", "lclsSystm2", "lclsSystm3",
    "firstimage", "firstimage2", "cpyrhtDivCd", "createdtime", "modifiedtime",
]


def to_float(v):
    """mapx/mapy: 원본은 문자열. 빈 값이면 None."""
    try:
        return float(v) if v not in ("", None) else None
    except (TypeError, ValueError):
        return None


def seed(data_dir: str) -> None:
    Base.metadata.create_all(engine)
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    if not files:
        sys.exit(f"JSON 파일을 찾을 수 없습니다: {data_dir}")

    rows, seen = [], set()
    for path in files:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        if "items" not in doc:          # lclsSystemCode.json 등은 건너뜀
            continue
        region = doc.get("region", "서울")
        for it in doc["items"]:
            cid = it["contentid"]
            if cid in seen:             # 파일 간 중복 방어 (실데이터에는 없음)
                continue
            seen.add(cid)
            row = {k: it.get(k, "") for k in RAW_FIELDS}
            row["region"] = region
            row["mapx"] = to_float(it.get("mapx"))
            row["mapy"] = to_float(it.get("mapy"))
            rows.append(row)
        print(f"  {os.path.basename(path)}: {doc.get('contentType')} {len(doc['items'])}건")

    with SessionLocal() as s:
        # 재실행해도 안전하도록 전체 교체 (원본이 갱신되면 다시 적재)
        s.query(Location).delete()
        s.bulk_insert_mappings(Location, rows)
        s.commit()

        total = s.scalar(select(func.count()).select_from(Location))
        print(f"\n적재 완료: {total}건")
        by_type = s.execute(
            select(Location.contenttypeid, ContentType.name, func.count())
            .join(ContentType, ContentType.contenttypeid == Location.contenttypeid, isouter=True)
            .group_by(Location.contenttypeid)
            .order_by(func.count().desc())
        ).all()
        for code, name, cnt in by_type:
            print(f"  {code} {name or '?'}: {cnt}건")

        missing = [c for c, n in [("39", "음식점")] if not s.scalar(
            select(func.count()).select_from(Location).where(Location.contenttypeid == c))]
        if missing:
            print("\n[경고] contenttypeid 39(음식점) 데이터가 없습니다. "
                  "챗봇의 맛집·음식점 질의에 답할 수 없습니다 — 서울_음식점.json을 확보하세요.")


if __name__ == "__main__":
    seed(sys.argv[1] if len(sys.argv) > 1 else "./data")
