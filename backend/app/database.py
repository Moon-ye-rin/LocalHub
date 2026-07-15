from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _):
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_legacy_schema() -> None:
    """기존 배포 DB에 새 게시글 지역 컬럼과 갱신 트리거를 안전하게 추가한다."""
    if not settings.database_url.startswith("sqlite"):
        return

    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(posts)").fetchall()
        }
        if "region" not in columns:
            connection.exec_driver_sql("ALTER TABLE posts ADD COLUMN region VARCHAR(10)")
        if "district" not in columns:
            connection.exec_driver_sql("ALTER TABLE posts ADD COLUMN district VARCHAR(30)")

        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_posts_region_district ON posts(region, district)"
        )

        location_comment_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(location_comments)").fetchall()
        }
        if location_comment_columns:
            if "password" not in location_comment_columns:
                # 기존 v1.5 댓글은 비밀번호가 없으므로 빈 값으로 보존한다. 신규 댓글부터 4자 이상 검증.
                connection.exec_driver_sql(
                    "ALTER TABLE location_comments ADD COLUMN password VARCHAR(100) NOT NULL DEFAULT ''"
                )
            if "updated_at" not in location_comment_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE location_comments ADD COLUMN updated_at DATETIME"
                )
            connection.exec_driver_sql("DROP TRIGGER IF EXISTS trg_location_comments_updated_at")
            connection.exec_driver_sql(
                """CREATE TRIGGER trg_location_comments_updated_at
                   AFTER UPDATE ON location_comments FOR EACH ROW
                   WHEN OLD.nickname IS NOT NEW.nickname OR OLD.content IS NOT NEW.content
                     OR OLD.rating IS NOT NEW.rating
                   BEGIN UPDATE location_comments SET updated_at = datetime('now') WHERE id = OLD.id; END;"""
            )
        # 기존 DB의 동일 이름 트리거는 컬럼 추가 내용을 모르므로 재생성한다.
        connection.exec_driver_sql("DROP TRIGGER IF EXISTS trg_posts_updated_at")
        connection.exec_driver_sql(
            """CREATE TRIGGER trg_posts_updated_at
               AFTER UPDATE ON posts FOR EACH ROW
               WHEN OLD.title IS NOT NEW.title OR OLD.content IS NOT NEW.content
                 OR OLD.category IS NOT NEW.category OR OLD.region IS NOT NEW.region
                 OR OLD.district IS NOT NEW.district
               BEGIN UPDATE posts SET updated_at = datetime('now') WHERE id = OLD.id; END;"""
        )
