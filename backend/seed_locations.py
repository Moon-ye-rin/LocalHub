"""서울·경기 TourAPI JSON 적재 CLI.

예:
    python seed_locations.py app/data
    python seed_locations.py app/data --replace
"""
from __future__ import annotations

import sys

from app.database import Base, SessionLocal, engine
from app.seed_locations import seed_locations


def main() -> None:
    data_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "app/data"
    replace = "--replace" in sys.argv[1:]
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        report = seed_locations(db, data_dir, replace=replace)
    print(
        f"적재 완료: {report['total']}건"
        if not report["skipped"]
        else f"기존 데이터 유지: {report['total']}건"
    )
    for item in report.get("files", []):
        print(
            f"  {item['file']}: {item['count']}건 "
            f"(대표 이미지 {item.get('visible_count', 0)}건)"
        )


if __name__ == "__main__":
    main()
