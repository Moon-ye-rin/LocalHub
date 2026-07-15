from __future__ import annotations

from datetime import timezone
from math import ceil
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..models import CONTENT_TYPES, Comment, Post, PostLike, PostView, Tag
from ..schemas import CommentCreate, CommentUpdate, PostCreate, PostUpdate

KST = ZoneInfo("Asia/Seoul")
CATEGORY_LABELS = {**CONTENT_TYPES, "자유": "자유"}
CATEGORY_TO_CODE = {label: code for code, label in CONTENT_TYPES.items()}


def normalize_category(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    value = value.strip()
    return CATEGORY_LABELS.get(value, value)


def format_kst(value) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(KST).isoformat(timespec="seconds")


def serialize_summary(post: Post) -> dict:
    return {
        "id": post.id,
        "category": post.category,
        "region": post.region,
        "district": post.district,
        "title": post.title,
        "content": post.content,
        "view_count": post.view_count,
        "like_count": post.like_count,
        "comment_count": len(post.comments),
        "tags": [tag.name for tag in post.tags],
        "created_at": format_kst(post.created_at),
        "updated_at": format_kst(post.updated_at),
    }


def serialize_detail(post: Post, *, liked: bool = False) -> dict:
    data = serialize_summary(post)
    data["images"] = [image.image_url for image in post.images]
    data["liked"] = liked
    return data


def require_post(db: Session, post_id: int, *, options: bool = True) -> Post:
    stmt = select(Post).where(Post.id == post_id)
    if options:
        stmt = stmt.options(selectinload(Post.tags), selectinload(Post.images), selectinload(Post.comments))
    post = db.scalar(stmt)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return post


def list_posts(
    db: Session,
    *,
    page: int,
    size: int,
    category: str | None,
    keyword: str | None,
    tag: str | None,
    sort: str,
) -> dict:
    stmt = select(Post).options(selectinload(Post.tags), selectinload(Post.images), selectinload(Post.comments))
    if category:
        stmt = stmt.where(Post.category == normalize_category(category))
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(Post.title.ilike(pattern), Post.content.ilike(pattern)))
    if tag and tag.strip():
        stmt = stmt.join(Post.tags).where(func.lower(Tag.name) == tag.strip().lower())

    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.scalar(count_stmt) or 0

    if sort == "views":
        stmt = stmt.order_by(Post.view_count.desc(), Post.id.desc())
    elif sort == "likes":
        stmt = stmt.order_by(Post.like_count.desc(), Post.id.desc())
    else:
        stmt = stmt.order_by(Post.created_at.desc(), Post.id.desc())

    posts = db.scalars(stmt.offset((page - 1) * size).limit(size)).unique().all()
    return {
        "posts": [serialize_summary(post) for post in posts],
        "page": page,
        "size": size,
        "total_count": total,
        "total_pages": ceil(total / size) if total else 0,
    }


def record_view(db: Session, post: Post, client_key: str | None) -> None:
    key = (client_key or f"anonymous-{uuid4()}")[:64]
    try:
        db.add(PostView(post_id=post.id, client_key=key))
        db.commit()
    except IntegrityError:
        db.rollback()
    db.refresh(post)


def read_post(db: Session, post_id: int, client_key: str | None) -> dict:
    post = require_post(db, post_id)
    record_view(db, post, client_key)
    key = (client_key or "")[:64]
    liked = bool(key and db.scalar(
        select(func.count()).select_from(PostLike).where(
            PostLike.post_id == post_id, PostLike.client_key == key
        )
    ))
    return serialize_detail(post, liked=liked)


def _tags(db: Session, names: list[str]) -> list[Tag]:
    result: list[Tag] = []
    for name in names:
        tag = db.scalar(select(Tag).where(func.lower(Tag.name) == name.lower()))
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        result.append(tag)
    return result


def create_post(db: Session, payload: PostCreate) -> int:
    post = Post(
        category=normalize_category(payload.category) or payload.category,
        region=payload.region,
        district=payload.district,
        title=payload.title,
        content=payload.content,
        password=payload.password,
        tags=_tags(db, payload.tags),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post.id


def verify_password(db: Session, post_id: int, password: str) -> bool:
    post = require_post(db, post_id, options=False)
    if post.password != password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    return True


def update_post(db: Session, post_id: int, payload: PostUpdate) -> int:
    post = require_post(db, post_id)
    if post.password != payload.password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    post.category = normalize_category(payload.category) or payload.category
    post.region = payload.region
    post.district = payload.district
    post.title = payload.title
    post.content = payload.content
    post.tags = _tags(db, payload.tags)
    db.commit()
    return post.id


def delete_post(db: Session, post_id: int, password: str) -> None:
    post = require_post(db, post_id, options=False)
    if post.password != password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    db.delete(post)
    db.commit()


def like_post(db: Session, post_id: int, client_key: str | None) -> dict:
    post = require_post(db, post_id, options=False)
    key = (client_key or f"anonymous-{uuid4()}")[:64]
    existing = db.scalar(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.client_key == key)
    )
    already = existing is not None
    if not existing:
        db.add(PostLike(post_id=post_id, client_key=key))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            already = True
    db.refresh(post)
    return {"like_count": post.like_count, "liked": True, "already_liked": already}


def unlike_post(db: Session, post_id: int, client_key: str | None) -> dict:
    post = require_post(db, post_id, options=False)
    key = (client_key or "")[:64]
    if key:
        existing = db.scalar(
            select(PostLike).where(PostLike.post_id == post_id, PostLike.client_key == key)
        )
        if existing:
            db.delete(existing)
            db.commit()
    db.refresh(post)
    return {"like_count": post.like_count, "liked": False, "already_liked": False}


def list_tags(db: Session, popular: bool) -> list[dict]:
    stmt = (
        select(Tag.name, func.count(Post.id).label("count"))
        .outerjoin(Tag.posts)
        .group_by(Tag.id)
    )
    if popular:
        stmt = stmt.order_by(func.count(Post.id).desc(), Tag.name.asc()).limit(20)
    else:
        stmt = stmt.order_by(Tag.name.asc())
    return [{"name": name, "count": count} for name, count in db.execute(stmt).all()]


def serialize_comment(comment: Comment) -> dict:
    return {
        "id": comment.id,
        "post_id": comment.post_id,
        "content": comment.content,
        "created_at": format_kst(comment.created_at),
        "updated_at": format_kst(comment.updated_at),
    }


def list_comments(db: Session, post_id: int) -> dict:
    require_post(db, post_id, options=False)
    comments = db.scalars(
        select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.asc(), Comment.id.asc())
    ).all()
    return {"comments": [serialize_comment(item) for item in comments], "total_count": len(comments)}


def create_comment(db: Session, post_id: int, payload: CommentCreate) -> int:
    require_post(db, post_id, options=False)
    comment = Comment(post_id=post_id, content=payload.content, password=payload.password)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment.id


def require_comment(db: Session, post_id: int, comment_id: int) -> Comment:
    comment = db.scalar(
        select(Comment).where(Comment.id == comment_id, Comment.post_id == post_id)
    )
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    return comment


def update_comment(db: Session, post_id: int, comment_id: int, payload: CommentUpdate) -> int:
    comment = require_comment(db, post_id, comment_id)
    if comment.password != payload.password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    comment.content = payload.content
    db.commit()
    return comment.id


def delete_comment(db: Session, post_id: int, comment_id: int, password: str) -> None:
    comment = require_comment(db, post_id, comment_id)
    if comment.password != password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    db.delete(comment)
    db.commit()
