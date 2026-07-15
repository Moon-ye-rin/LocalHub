"""서울·경기 TourAPI JSON 파일을 SQLite에 적재한다.

DATA_DIR 아래의 모든 하위 폴더를 재귀 탐색한다.
공공누리 제3유형 조건에 따라 mapx/mapy만 float로 변환하고,
나머지 원본 필드와 빈 문자열은 그대로 저장한다.
"""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Location

RAW_FIELDS = [
    "contentid", "contenttypeid", "title", "addr1", "addr2", "zipcode", "tel",
    "mlevel", "areacode", "sigungucode", "lDongRegnCd", "lDongSignguCd",
    "cat1", "cat2", "cat3", "lclsSystm1", "lclsSystm2", "lclsSystm3",
    "firstimage", "firstimage2", "cpyrhtDivCd", "createdtime", "modifiedtime",
]


def to_float(value):
    try:
        return float(value) if value not in ("", None) else None
    except (TypeError, ValueError):
        return None


def load_rows(data_dir: str | Path) -> tuple[list[dict], list[dict]]:
    data_path = Path(data_dir)
    files = sorted(data_path.rglob("*.json"))
    rows: list[dict] = []
    report: list[dict] = []
    seen: set[str] = set()

    for filename in files:
        with filename.open(encoding="utf-8") as file:
            doc = json.load(file)

        items = doc.get("items") if isinstance(doc, dict) else None
        if not isinstance(items, list):
            continue

        region = str(doc.get("region") or "서울")
        inserted = 0
        visible = 0

        for item in items:
            contentid = str(item.get("contentid", "")).strip()
            if not contentid or contentid in seen:
                continue

            seen.add(contentid)
            row = {key: item.get(key, "") for key in RAW_FIELDS}
            row["contentid"] = contentid
            row["contenttypeid"] = str(row.get("contenttypeid", ""))
            row["region"] = region
            row["mapx"] = to_float(item.get("mapx"))
            row["mapy"] = to_float(item.get("mapy"))
            rows.append(row)
            inserted += 1
            if str(item.get("firstimage", "")).strip():
                visible += 1

        report.append({
            "file": str(filename.relative_to(data_path)),
            "region": region,
            "content_type": doc.get("contentType"),
            "content_type_id": str(doc.get("contentTypeId", "")),
            "count": inserted,
            "visible_count": visible,
        })

    return rows, report


def seed_locations(db: Session, data_dir: str | Path, replace: bool = False) -> dict:
    existing = db.scalar(select(func.count()).select_from(Location)) or 0
    if existing and not replace:
        return {"skipped": True, "total": existing, "files": []}

    rows, report = load_rows(data_dir)
    if not rows:
        raise RuntimeError(f"관광 JSON 파일을 찾지 못했습니다: {data_dir}")

    if replace:
        db.query(Location).delete()

    db.bulk_insert_mappings(Location, rows)
    db.commit()
    total = db.scalar(select(func.count()).select_from(Location)) or 0
    return {"skipped": False, "total": total, "files": report}
