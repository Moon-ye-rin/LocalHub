"""LocalHub SQLAlchemy 2.0 models.

Applied from the provided DB schema v3.0 and real TourAPI JSON dataset.
Community dates are stored in UTC and serialized to Asia/Seoul by services.
"""
from __future__ import annotations

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
    event,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


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
        Index("idx_posts_region_district", "region", "district"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    region: Mapped[str | None] = mapped_column(String(10), nullable=True)
    district: Mapped[str | None] = mapped_column(String(30), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)  # RFP 교육용 평문 저장
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    tags: Mapped[list[Tag]] = relationship(secondary=post_tags, back_populates="posts")
    images: Mapped[list["PostImage"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    likes: Mapped[list["PostLike"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    views: Mapped[list["PostView"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", order_by="Comment.created_at"
    )


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint("length(content) BETWEEN 1 AND 1000", name="ck_comments_content_len"),
        CheckConstraint("length(password) >= 4", name="ck_comments_password_len"),
        Index("idx_comments_post_created", "post_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)  # 교육 목적 평문 저장
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    post: Mapped[Post] = relationship(back_populates="comments")


class PostImage(Base):
    __tablename__ = "post_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    image_url: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    post: Mapped[Post] = relationship(back_populates="images")


class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (
        UniqueConstraint("post_id", "client_key", name="uq_like_post_client"),
        Index("idx_post_likes_post", "post_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    client_key: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    post: Mapped[Post] = relationship(back_populates="likes")


class PostView(Base):
    __tablename__ = "post_views"
    __table_args__ = (
        UniqueConstraint("post_id", "client_key", name="uq_view_post_client"),
        Index("idx_post_views_post", "post_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    client_key: Mapped[str] = mapped_column(String(64), nullable=False)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    post: Mapped[Post] = relationship(back_populates="views")


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        Index("idx_loc_type", "contenttypeid"),
        Index("idx_loc_region_type", "region", "contenttypeid"),
        Index("idx_loc_title", "title"),
        Index("idx_loc_signgu", "lDongSignguCd", "contenttypeid"),
        Index("idx_loc_lcls", "lclsSystm1"),
    )

    contentid: Mapped[str] = mapped_column(String(20), primary_key=True)
    contenttypeid: Mapped[str] = mapped_column(String(2), nullable=False)
    region: Mapped[str] = mapped_column(String(20), nullable=False, default="서울")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    addr1: Mapped[str | None] = mapped_column(String(200))
    addr2: Mapped[str | None] = mapped_column(String(200))
    zipcode: Mapped[str | None] = mapped_column(String(10))
    tel: Mapped[str | None] = mapped_column(String(50))
    mapx: Mapped[float | None] = mapped_column(Float)
    mapy: Mapped[float | None] = mapped_column(Float)
    mlevel: Mapped[str | None] = mapped_column(String(2))
    areacode: Mapped[str | None] = mapped_column(String(5))
    sigungucode: Mapped[str | None] = mapped_column(String(5))
    lDongRegnCd: Mapped[str | None] = mapped_column(String(5))
    lDongSignguCd: Mapped[str | None] = mapped_column(String(5))
    cat1: Mapped[str | None] = mapped_column(String(10))
    cat2: Mapped[str | None] = mapped_column(String(10))
    cat3: Mapped[str | None] = mapped_column(String(10))
    lclsSystm1: Mapped[str | None] = mapped_column(String(10))
    lclsSystm2: Mapped[str | None] = mapped_column(String(10))
    lclsSystm3: Mapped[str | None] = mapped_column(String(10))
    firstimage: Mapped[str | None] = mapped_column(String(255))
    firstimage2: Mapped[str | None] = mapped_column(String(255))
    cpyrhtDivCd: Mapped[str | None] = mapped_column(String(5))
    createdtime: Mapped[str | None] = mapped_column(String(14))
    modifiedtime: Mapped[str | None] = mapped_column(String(14))
    loaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    comments: Mapped[list["LocationComment"]] = relationship(
        back_populates="location", cascade="all, delete-orphan", order_by="LocationComment.created_at"
    )
    likes: Mapped[list["LocationLike"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )
    bookmarks: Mapped[list["LocationBookmark"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )
    views: Mapped[list["LocationView"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )


class LocationComment(Base):
    __tablename__ = "location_comments"
    __table_args__ = (
        CheckConstraint("length(content) BETWEEN 1 AND 1000", name="ck_location_comments_content_len"),
        CheckConstraint("rating BETWEEN 0 AND 5", name="ck_location_comments_rating"),
        CheckConstraint("length(password) >= 4", name="ck_location_comments_password_len"),
        Index("idx_location_comments_content_created", "contentid", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    contentid: Mapped[str] = mapped_column(
        ForeignKey("locations.contentid", ondelete="CASCADE"), nullable=False
    )
    nickname: Mapped[str] = mapped_column(String(30), nullable=False, default="익명", server_default="익명")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    location: Mapped[Location] = relationship(back_populates="comments")


class LocationLike(Base):
    __tablename__ = "location_likes"
    __table_args__ = (
        UniqueConstraint("contentid", "client_key", name="uq_location_like_client"),
        Index("idx_location_likes_content", "contentid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    contentid: Mapped[str] = mapped_column(
        ForeignKey("locations.contentid", ondelete="CASCADE"), nullable=False
    )
    client_key: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    location: Mapped[Location] = relationship(back_populates="likes")


class LocationBookmark(Base):
    __tablename__ = "location_bookmarks"
    __table_args__ = (
        UniqueConstraint("contentid", "client_key", name="uq_location_bookmark_client"),
        Index("idx_location_bookmarks_content", "contentid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    contentid: Mapped[str] = mapped_column(
        ForeignKey("locations.contentid", ondelete="CASCADE"), nullable=False
    )
    client_key: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    location: Mapped[Location] = relationship(back_populates="bookmarks")


class LocationView(Base):
    __tablename__ = "location_views"
    __table_args__ = (
        UniqueConstraint("contentid", "client_key", name="uq_location_view_client"),
        Index("idx_location_views_content", "contentid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    contentid: Mapped[str] = mapped_column(
        ForeignKey("locations.contentid", ondelete="CASCADE"), nullable=False
    )
    client_key: Mapped[str] = mapped_column(String(64), nullable=False)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    location: Mapped[Location] = relationship(back_populates="views")


class ContentType(Base):
    __tablename__ = "content_types"

    contenttypeid: Mapped[str] = mapped_column(String(2), primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)


CONTENT_TYPES = {
    "12": "관광지",
    "14": "문화시설",
    "15": "축제공연행사",
    "25": "여행코스",
    "28": "레포츠",
    "32": "숙박",
    "38": "쇼핑",
    "39": "음식점",
}

_TRIGGERS = [
    """CREATE TRIGGER IF NOT EXISTS trg_posts_updated_at
       AFTER UPDATE ON posts FOR EACH ROW
       WHEN OLD.title IS NOT NEW.title OR OLD.content IS NOT NEW.content
         OR OLD.category IS NOT NEW.category OR OLD.region IS NOT NEW.region
         OR OLD.district IS NOT NEW.district
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
    """CREATE TRIGGER IF NOT EXISTS trg_comments_updated_at
       AFTER UPDATE ON comments FOR EACH ROW
       WHEN OLD.content IS NOT NEW.content
       BEGIN UPDATE comments SET updated_at = datetime('now') WHERE id = OLD.id; END;""",
    """CREATE TRIGGER IF NOT EXISTS trg_location_comments_updated_at
       AFTER UPDATE ON location_comments FOR EACH ROW
       WHEN OLD.nickname IS NOT NEW.nickname OR OLD.content IS NOT NEW.content
         OR OLD.rating IS NOT NEW.rating
       BEGIN UPDATE location_comments SET updated_at = datetime('now') WHERE id = OLD.id; END;""",
]


@event.listens_for(Base.metadata, "after_create")
def after_create(_, connection, **__):
    for ddl in _TRIGGERS:
        connection.exec_driver_sql(ddl)
    for code, name in CONTENT_TYPES.items():
        connection.exec_driver_sql(
            "INSERT OR IGNORE INTO content_types (contenttypeid, name) VALUES (?, ?)",
            (code, name),
        )
