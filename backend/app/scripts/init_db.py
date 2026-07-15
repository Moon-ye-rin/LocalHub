from sqlalchemy import func, select

from ..config import get_settings
from ..database import Base, SessionLocal, engine, migrate_legacy_schema
from ..models import Location
from ..seed import seed_posts
from ..seed_locations import seed_locations


def main() -> None:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    migrate_legacy_schema()
    with SessionLocal() as db:
        posts = seed_posts(db) if settings.seed_data else 0
        count = db.scalar(select(func.count()).select_from(Location)) or 0
        report = {"total": count, "skipped": True}
        if settings.seed_locations and count == 0:
            report = seed_locations(db, settings.data_path)
    print(f"게시글 준비: {posts}건")
    print(f"관광 데이터 준비: {report['total']}건")


if __name__ == "__main__":
    main()
