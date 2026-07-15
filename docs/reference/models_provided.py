"""
LocalHub - SQLAlchemy 2.0 모델 (SQLite) v3.0
기준: API 명세서 v1.0(개정) + SCHEMA.md(TourAPI 4.0) + 실제 제공 JSON 6,518건

사용:
    from models import Base, engine, SessionLocal
    Base.metadata.create_all(engine)          # 테이블 + 트리거 + 코드표 생성
    python seed_locations.py ./data           # JSON 적재

시간대 주의:
    created_at/updated_at은 UTC 저장. 명세서 6장은 KST(+09:00) 응답을 요구하므로
    Pydantic 직렬화에서 변환할 것:
        dt.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Asia/Seoul"))
"""
from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    func,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./localhub.db")   # .env로 관리
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def _enable_fk(dbapi_conn, _):
    # SQLite는 외래키가 기본 OFF → ON DELETE CASCADE가 동작하려면 필수
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


class Base(DeclarativeBase):
    pass


# =====================================================================
# 1. 커뮤니티
# =====================================================================
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Index("idx_post_tags_tag", "tag_id"),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NOCASE: 'Cafe'와 'cafe'를 같은 태그로. 앞뒤 공백은 앱에서 strip() 후 저장.
    name: Mapped[str] = mapped_column(String(30, collation="NOCASE"), nullable=False, unique=True)

    posts: Mapped[list["Post"]] = relationship(secondary=post_tags, back_populates="tags")


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        CheckConstraint("length(title) BETWEEN 1 AND 200", name="ck_posts_title_len"),
        CheckConstraint("length(password) >= 4", name="ck_posts_password_len"),
        Index("idx_posts_created_at", "created_at"),
        Index("idx_posts_view_count", "view_count"),
        Index("idx_posts_like_count", "like_count"),
        Index("idx_posts_category", "category", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)  # 평문(의도된 설계)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # onupdate를 쓰면 조회수 증가에도 갱신된다 → 트리거가 내용 변경 시에만 채운다
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    tags: Mapped[list[Tag]] = relationship(secondary=post_tags, back_populates="posts")
    images: Mapped[list["PostImage"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    likes: Mapped[list["PostLike"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class PostImage(Base):
    __tablename__ = "post_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    image_url: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    post: Mapped[Post] = relationship(back_populates="images")


# client_key = 프론트가 crypto.randomUUID()로 만들어 localStorage에 보관하고
#              헤더 X-Client-Key로 보내는 값. UNIQUE가 중복의 최종 방어선.
class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("post_id", "client_key", name="uq_like_post_client"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    client_key: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    post: Mapped[Post] = relationship(back_populates="likes")


class PostView(Base):
    __tablename__ = "post_views"
    __table_args__ = (UniqueConstraint("post_id", "client_key", name="uq_view_post_client"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    client_key: Mapped[str] = mapped_column(String(64), nullable=False)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# =====================================================================
# 2. TourAPI 4.0 원본 캐시
#    공공누리 3유형(변경 금지) → 필드명·값을 원본 그대로 유지.
#    빈 문자열("")도 NULL로 바꾸지 않고 그대로 저장한다.
# =====================================================================
class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        Index("idx_loc_type", "contenttypeid"),
        Index("idx_loc_title", "title"),
        Index("idx_loc_signgu", "lDongSignguCd", "contenttypeid"),
        Index("idx_loc_lcls", "lclsSystm1"),
    )

    contentid: Mapped[str] = mapped_column(String(20), primary_key=True)
    contenttypeid: Mapped[str] = mapped_column(String(2), nullable=False)
    region: Mapped[str] = mapped_column(String(20), nullable=False, default="서울")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    addr1: Mapped[str | None] = mapped_column(String(200))     # "" = 주소 미제공
    addr2: Mapped[str | None] = mapped_column(String(200))
    zipcode: Mapped[str | None] = mapped_column(String(10))
    tel: Mapped[str | None] = mapped_column(String(50))        # 실데이터 97%가 ""
    mapx: Mapped[float | None] = mapped_column(Float)          # 경도 (원본 string → float)
    mapy: Mapped[float | None] = mapped_column(Float)          # 위도
    mlevel: Mapped[str | None] = mapped_column(String(2))
    areacode: Mapped[str | None] = mapped_column(String(5))    # 79%가 "" → 필터로 쓰지 말 것
    sigungucode: Mapped[str | None] = mapped_column(String(5))
    lDongRegnCd: Mapped[str | None] = mapped_column(String(2))     # '11' = 서울
    lDongSignguCd: Mapped[str | None] = mapped_column(String(3))   # 구 코드 → 지역 필터는 이걸로
    cat1: Mapped[str | None] = mapped_column(String(10))       # 78%가 ""
    cat2: Mapped[str | None] = mapped_column(String(10))
    cat3: Mapped[str | None] = mapped_column(String(10))
    lclsSystm1: Mapped[str | None] = mapped_column(String(3))  # 신 분류 (100% 존재)
    lclsSystm2: Mapped[str | None] = mapped_column(String(5))
    lclsSystm3: Mapped[str | None] = mapped_column(String(9))
    firstimage: Mapped[str | None] = mapped_column(String(255))   # "" = 이미지 없음
    firstimage2: Mapped[str | None] = mapped_column(String(255))
    cpyrhtDivCd: Mapped[str | None] = mapped_column(String(5))
    createdtime: Mapped[str | None] = mapped_column(String(14))   # 원본 문자열 유지
    modifiedtime: Mapped[str | None] = mapped_column(String(14))
    loaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ContentType(Base):
    """contenttypeid → 한글명 (화면 필터 / 챗봇 의도 매핑)"""

    __tablename__ = "content_types"

    contenttypeid: Mapped[str] = mapped_column(String(2), primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)


CONTENT_TYPES = {
    "12": "관광지", "14": "문화시설", "15": "축제공연행사", "25": "여행코스",
    "28": "레포츠", "32": "숙박", "38": "쇼핑", "39": "음식점",
}

# =====================================================================
# 3. 트리거 + 코드표 초기 데이터 (create_all 시 함께 생성)
# =====================================================================
_TRIGGERS = [
    """CREATE TRIGGER IF NOT EXISTS trg_posts_updated_at
       AFTER UPDATE ON posts FOR EACH ROW
       WHEN OLD.title IS NOT NEW.title OR OLD.content IS NOT NEW.content
         OR OLD.category IS NOT NEW.category
       BEGIN UPDATE posts SET updated_at = datetime('now') WHERE id = OLD.id; END;""",
    """CREATE TRIGGER IF NOT EXISTS trg_like_insert
       AFTER INSERT ON post_likes FOR EACH ROW
       BEGIN UPDATE posts SET like_count = like_count + 1 WHERE id = NEW.post_id; END;""",
    """CREATE TRIGGER IF NOT EXISTS trg_like_delete
       AFTER DELETE ON post_likes FOR EACH ROW
       BEGIN UPDATE posts SET like_count = MAX(like_count - 1, 0) WHERE id = OLD.post_id; END;""",
    """CREATE TRIGGER IF NOT EXISTS trg_view_insert
       AFTER INSERT ON post_views FOR EACH ROW
       BEGIN UPDATE posts SET view_count = view_count + 1 WHERE id = NEW.post_id; END;""",
]


@event.listens_for(Base.metadata, "after_create")
def _after_create(target, connection, **kw):
    for ddl in _TRIGGERS:
        connection.exec_driver_sql(ddl)
    for code, name in CONTENT_TYPES.items():
        connection.exec_driver_sql(
            "INSERT OR IGNORE INTO content_types (contenttypeid, name) VALUES (?, ?)", (code, name)
        )
