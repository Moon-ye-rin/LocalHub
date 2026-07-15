from __future__ import annotations

from datetime import timezone
from math import ceil
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Location,
    LocationBookmark,
    LocationComment,
    LocationLike,
    LocationView,
)
from ..schemas import LocationCommentCreate, LocationCommentUpdate

KST = ZoneInfo("Asia/Seoul")


def visible_location_conditions():
    """대표 이미지가 없는 TourAPI 원본 데이터는 모든 사용자 화면에서 제외한다."""
    return (
        Location.firstimage.is_not(None),
        func.trim(Location.firstimage) != "",
    )


def format_kst(value) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(KST).isoformat(timespec="seconds")


def serialize_item(location: Location, *, bookmarked: bool = False) -> dict:
    return {
        "contentid": location.contentid,
        "contenttypeid": location.contenttypeid,
        "region": location.region,
        "title": location.title,
        "addr1": location.addr1,
        "addr2": location.addr2,
        "tel": location.tel,
        "mapx": location.mapx,
        "mapy": location.mapy,
        "lDongRegnCd": location.lDongRegnCd,
        "lDongSignguCd": location.lDongSignguCd,
        "lclsSystm1": location.lclsSystm1,
        "lclsSystm2": location.lclsSystm2,
        "lclsSystm3": location.lclsSystm3,
        "firstimage": location.firstimage,
        "firstimage2": location.firstimage2,
        "cpyrhtDivCd": location.cpyrhtDivCd,
        "bookmarked": bookmarked,
    }


def _client_key(value: str | None) -> str:
    return (value or f"anonymous-{uuid4()}")[:64]


def require_location(db: Session, contentid: str) -> Location:
    location = db.scalar(
        select(Location)
        .where(Location.contentid == contentid)
        .where(*visible_location_conditions())
    )
    if not location:
        raise HTTPException(status_code=404, detail="해당 관광 정보를 찾을 수 없습니다.")
    return location


def record_location_view(db: Session, contentid: str, client_key: str | None) -> None:
    key = _client_key(client_key)
    try:
        db.add(LocationView(contentid=contentid, client_key=key))
        db.commit()
    except IntegrityError:
        db.rollback()


def _count(db: Session, model, contentid: str) -> int:
    return int(
        db.scalar(select(func.count()).select_from(model).where(model.contentid == contentid)) or 0
    )


def location_stats(db: Session, contentid: str, client_key: str | None = None) -> dict:
    comment_count = _count(db, LocationComment, contentid)
    like_count = _count(db, LocationLike, contentid)
    bookmark_count = _count(db, LocationBookmark, contentid)
    view_count = _count(db, LocationView, contentid)
    rating_row = db.execute(
        select(func.avg(LocationComment.rating), func.count(LocationComment.id)).where(
            LocationComment.contentid == contentid
        )
    ).one()
    average_rating = round(float(rating_row[0] or 0), 1)
    rating_count = int(rating_row[1] or 0)
    key = (client_key or "")[:64]
    liked = bool(
        key
        and db.scalar(
            select(func.count()).select_from(LocationLike).where(
                LocationLike.contentid == contentid,
                LocationLike.client_key == key,
            )
        )
    )
    bookmarked = bool(
        key
        and db.scalar(
            select(func.count()).select_from(LocationBookmark).where(
                LocationBookmark.contentid == contentid,
                LocationBookmark.client_key == key,
            )
        )
    )
    return {
        "view_count": view_count,
        "like_count": like_count,
        "bookmark_count": bookmark_count,
        "comment_count": comment_count,
        "average_rating": average_rating,
        "rating_count": rating_count,
        "liked": liked,
        "bookmarked": bookmarked,
    }


def nearest_locations(
    db: Session, location: Location, client_key: str | None, limit: int = 5
) -> list[dict]:
    if location.mapx is None or location.mapy is None:
        return []
    distance = (
        (Location.mapx - location.mapx) * (Location.mapx - location.mapx)
        + (Location.mapy - location.mapy) * (Location.mapy - location.mapy)
    )
    items = db.scalars(
        select(Location)
        .where(*visible_location_conditions())
        .where(Location.contentid != location.contentid)
        .where(Location.mapx.is_not(None), Location.mapy.is_not(None))
        .order_by(distance.asc(), Location.title.asc())
        .limit(limit)
    ).all()
    key = (client_key or "")[:64]
    bookmarked_ids: set[str] = set()
    if key and items:
        bookmarked_ids = set(
            db.scalars(
                select(LocationBookmark.contentid).where(
                    LocationBookmark.client_key == key,
                    LocationBookmark.contentid.in_([item.contentid for item in items]),
                )
            ).all()
        )
    return [
        serialize_item(item, bookmarked=item.contentid in bookmarked_ids)
        for item in items
    ]


def serialize_detail(db: Session, location: Location, client_key: str | None) -> dict:
    data = serialize_item(location)
    data.update(
        {
            "zipcode": location.zipcode,
            "mlevel": location.mlevel,
            "areacode": location.areacode,
            "sigungucode": location.sigungucode,
            "cat1": location.cat1,
            "cat2": location.cat2,
            "cat3": location.cat3,
            "createdtime": location.createdtime,
            "modifiedtime": location.modifiedtime,
            "nearby": nearest_locations(db, location, client_key, 5),
            **location_stats(db, location.contentid, client_key),
        }
    )
    return data


def list_locations(
    db: Session,
    *,
    region: str | None,
    bookmarked_only: bool,
    client_key: str | None,
    contenttypeid: str | None,
    keyword: str | None,
    lDongSignguCd: str | None,
    lclsSystm1: str | None,
    lclsSystm2: str | None,
    lclsSystm3: str | None,
    page: int,
    size: int,
) -> dict:
    stmt = select(Location).where(*visible_location_conditions())
    key = (client_key or "")[:64]

    if bookmarked_only:
        if not key:
            stmt = stmt.where(Location.contentid == "__no_client_bookmarks__")
        else:
            stmt = stmt.join(
                LocationBookmark,
                LocationBookmark.contentid == Location.contentid,
            ).where(LocationBookmark.client_key == key)

    if region in {"서울", "경기"}:
        stmt = stmt.where(Location.region == region)
    if contenttypeid:
        stmt = stmt.where(Location.contenttypeid == contenttypeid)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(Location.title.ilike(pattern), Location.addr1.ilike(pattern)))
    if lDongSignguCd:
        stmt = stmt.where(Location.lDongSignguCd == lDongSignguCd)
    if lclsSystm1:
        stmt = stmt.where(Location.lclsSystm1 == lclsSystm1)
    if lclsSystm2:
        stmt = stmt.where(Location.lclsSystm2 == lclsSystm2)
    if lclsSystm3:
        stmt = stmt.where(Location.lclsSystm3 == lclsSystm3)

    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(
        stmt.order_by(Location.title.asc()).offset((page - 1) * size).limit(size)
    ).all()

    bookmarked_ids: set[str] = set()
    if key and items:
        bookmarked_ids = set(
            db.scalars(
                select(LocationBookmark.contentid).where(
                    LocationBookmark.client_key == key,
                    LocationBookmark.contentid.in_([item.contentid for item in items]),
                )
            ).all()
        )

    return {
        "region": region or "전체",
        "items": [
            serialize_item(item, bookmarked=item.contentid in bookmarked_ids)
            for item in items
        ],
        "page": page,
        "size": size,
        "total_count": total,
        "total_pages": ceil(total / size) if total else 0,
    }


def get_location(db: Session, contentid: str, client_key: str | None) -> dict:
    location = require_location(db, contentid)
    record_location_view(db, contentid, client_key)
    return serialize_detail(db, location, client_key)


def serialize_location_comment(comment: LocationComment) -> dict:
    return {
        "id": comment.id,
        "contentid": comment.contentid,
        "nickname": comment.nickname or "익명",
        "content": comment.content,
        "rating": comment.rating,
        "created_at": format_kst(comment.created_at),
        "updated_at": format_kst(comment.updated_at),
    }


def list_location_comments(db: Session, contentid: str) -> dict:
    require_location(db, contentid)
    comments = db.scalars(
        select(LocationComment)
        .where(LocationComment.contentid == contentid)
        .order_by(LocationComment.created_at.desc(), LocationComment.id.desc())
    ).all()
    ratings = [item.rating for item in comments]
    return {
        "comments": [serialize_location_comment(item) for item in comments],
        "total_count": len(comments),
        "average_rating": round(sum(ratings) / len(ratings), 1) if ratings else 0,
        "rating_count": len(ratings),
    }


def create_location_comment(
    db: Session, contentid: str, payload: LocationCommentCreate
) -> int:
    require_location(db, contentid)
    comment = LocationComment(
        contentid=contentid,
        nickname=payload.nickname or "익명",
        content=payload.content,
        rating=payload.rating,
        password=payload.password,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment.id


def require_location_comment(db: Session, contentid: str, comment_id: int) -> LocationComment:
    require_location(db, contentid)
    comment = db.scalar(
        select(LocationComment).where(
            LocationComment.id == comment_id,
            LocationComment.contentid == contentid,
        )
    )
    if not comment:
        raise HTTPException(status_code=404, detail="지역정보 댓글을 찾을 수 없습니다.")
    return comment


def update_location_comment(
    db: Session,
    contentid: str,
    comment_id: int,
    payload: LocationCommentUpdate,
) -> int:
    comment = require_location_comment(db, contentid, comment_id)
    if comment.password != payload.password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    comment.nickname = payload.nickname or "익명"
    comment.content = payload.content
    comment.rating = payload.rating
    db.commit()
    return comment.id


def delete_location_comment(
    db: Session,
    contentid: str,
    comment_id: int,
    password: str,
) -> None:
    comment = require_location_comment(db, contentid, comment_id)
    if comment.password != password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    db.delete(comment)
    db.commit()


def like_location(db: Session, contentid: str, client_key: str | None) -> dict:
    require_location(db, contentid)
    key = _client_key(client_key)
    existing = db.scalar(
        select(LocationLike).where(
            LocationLike.contentid == contentid, LocationLike.client_key == key
        )
    )
    if not existing:
        db.add(LocationLike(contentid=contentid, client_key=key))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    return {"count": _count(db, LocationLike, contentid), "active": True}


def unlike_location(db: Session, contentid: str, client_key: str | None) -> dict:
    require_location(db, contentid)
    key = (client_key or "")[:64]
    if key:
        existing = db.scalar(
            select(LocationLike).where(
                LocationLike.contentid == contentid, LocationLike.client_key == key
            )
        )
        if existing:
            db.delete(existing)
            db.commit()
    return {"count": _count(db, LocationLike, contentid), "active": False}


def bookmark_location(db: Session, contentid: str, client_key: str | None) -> dict:
    require_location(db, contentid)
    key = _client_key(client_key)
    existing = db.scalar(
        select(LocationBookmark).where(
            LocationBookmark.contentid == contentid,
            LocationBookmark.client_key == key,
        )
    )
    if not existing:
        db.add(LocationBookmark(contentid=contentid, client_key=key))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    return {"count": _count(db, LocationBookmark, contentid), "active": True}


def unbookmark_location(db: Session, contentid: str, client_key: str | None) -> dict:
    require_location(db, contentid)
    key = (client_key or "")[:64]
    if key:
        existing = db.scalar(
            select(LocationBookmark).where(
                LocationBookmark.contentid == contentid,
                LocationBookmark.client_key == key,
            )
        )
        if existing:
            db.delete(existing)
            db.commit()
    return {"count": _count(db, LocationBookmark, contentid), "active": False}
