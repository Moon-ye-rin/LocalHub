from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..models import (
    Location,
    LocationComment,
    LocationLike,
    LocationView,
    Post,
    PostLike,
    PostView,
)
from ..regions import format_region_label
from .location_service import visible_location_conditions

KST = ZoneInfo("Asia/Seoul")
WEEKDAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"]
MONTHLY_CATEGORIES = (
    ("관광지", {"관광지"}),
    ("맛집", {"음식점", "맛집"}),
    ("문화", {"문화시설", "문화"}),
    ("축제", {"축제공연행사", "축제"}),
)
CATEGORY_LABELS = {
    "관광지": "관광지",
    "음식점": "맛집",
    "맛집": "맛집",
    "문화시설": "문화",
    "문화": "문화",
    "축제공연행사": "축제",
    "축제": "축제",
    "여행코스": "여행코스",
    "레포츠": "레포츠",
    "숙박": "숙박",
    "쇼핑": "쇼핑",
    "자유": "자유",
}


def _as_kst(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(KST)


def _as_utc_naive(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _shift_month(year: int, month: int, amount: int) -> tuple[int, int]:
    zero_based = year * 12 + (month - 1) + amount
    return zero_based // 12, zero_based % 12 + 1


def _distribution(posts: list[Post], region: str | None = None) -> list[dict]:
    counts: Counter[str] = Counter()
    for post in posts:
        if region and post.region != region:
            continue
        counts[CATEGORY_LABELS.get(post.category, post.category)] += 1
    return [
        {"label": label, "count": count}
        for label, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _location_rankings(db: Session) -> tuple[list[dict], list[dict]]:
    comment_stats = (
        select(
            LocationComment.contentid.label("contentid"),
            func.count(LocationComment.id).label("comment_count"),
            func.avg(LocationComment.rating).label("average_rating"),
            func.count(LocationComment.id).label("rating_count"),
        )
        .group_by(LocationComment.contentid)
        .subquery()
    )
    like_stats = (
        select(LocationLike.contentid.label("contentid"), func.count(LocationLike.id).label("like_count"))
        .group_by(LocationLike.contentid)
        .subquery()
    )
    view_stats = (
        select(LocationView.contentid.label("contentid"), func.count(LocationView.id).label("view_count"))
        .group_by(LocationView.contentid)
        .subquery()
    )

    comment_count = func.coalesce(comment_stats.c.comment_count, 0)
    like_count = func.coalesce(like_stats.c.like_count, 0)
    view_count = func.coalesce(view_stats.c.view_count, 0)
    rating_count = func.coalesce(comment_stats.c.rating_count, 0)
    average_rating = func.coalesce(comment_stats.c.average_rating, 0.0)
    score = comment_count * 3 + like_count * 2 + view_count

    base = (
        select(
            Location.contentid,
            Location.title,
            Location.region,
            Location.firstimage,
            comment_count.label("comment_count"),
            like_count.label("like_count"),
            view_count.label("view_count"),
            rating_count.label("rating_count"),
            average_rating.label("average_rating"),
            score.label("score"),
        )
        .outerjoin(comment_stats, comment_stats.c.contentid == Location.contentid)
        .outerjoin(like_stats, like_stats.c.contentid == Location.contentid)
        .outerjoin(view_stats, view_stats.c.contentid == Location.contentid)
        .where(*visible_location_conditions())
    )

    popular_rows = db.execute(
        base.where(score > 0).order_by(score.desc(), comment_count.desc(), Location.title.asc()).limit(6)
    ).all()
    popular = [
        {
            "contentid": row.contentid,
            "title": row.title,
            "region": row.region,
            "firstimage": row.firstimage,
            "score": int(row.score or 0),
            "comment_count": int(row.comment_count or 0),
            "like_count": int(row.like_count or 0),
            "view_count": int(row.view_count or 0),
            "average_rating": round(float(row.average_rating or 0), 1),
            "rating_count": int(row.rating_count or 0),
        }
        for row in popular_rows
    ]

    rated_rows = db.execute(
        base.where(rating_count > 0)
        .order_by(average_rating.desc(), rating_count.desc(), comment_count.desc(), Location.title.asc())
        .limit(6)
    ).all()
    top_rated = [
        {
            "contentid": row.contentid,
            "title": row.title,
            "region": row.region,
            "firstimage": row.firstimage,
            "average_rating": round(float(row.average_rating or 0), 1),
            "rating_count": int(row.rating_count or 0),
            "comment_count": int(row.comment_count or 0),
        }
        for row in rated_rows
    ]
    return popular, top_rated


def build_dashboard(db: Session) -> dict:
    now_kst = datetime.now(KST)
    posts = db.scalars(select(Post).options(selectinload(Post.comments))).unique().all()

    month_keys: list[tuple[int, int]] = [
        _shift_month(now_kst.year, now_kst.month, offset) for offset in range(-6, 1)
    ]
    month_index = {key: index for index, key in enumerate(month_keys)}
    monthly_counts = {name: [0] * len(month_keys) for name, _ in MONTHLY_CATEGORIES}
    for post in posts:
        created = _as_kst(post.created_at)
        index = month_index.get((created.year, created.month))
        if index is None:
            continue
        for name, source_categories in MONTHLY_CATEGORIES:
            if post.category in source_categories:
                monthly_counts[name][index] += 1
                break

    popular: dict[tuple[str, str], dict[str, int | str]] = defaultdict(
        lambda: {
            "score": 0,
            "post_count": 0,
            "comment_count": 0,
            "like_count": 0,
            "view_count": 0,
        }
    )
    for post in posts:
        if post.region not in {"서울", "경기"} or not post.district:
            continue
        comments = len(post.comments)
        key = (post.region, post.district)
        bucket = popular[key]
        bucket["post_count"] = int(bucket["post_count"]) + 1
        bucket["comment_count"] = int(bucket["comment_count"]) + comments
        bucket["like_count"] = int(bucket["like_count"]) + post.like_count
        bucket["view_count"] = int(bucket["view_count"]) + post.view_count
        bucket["score"] = int(bucket["score"]) + comments * 3 + post.like_count * 2 + post.view_count

    popular_regions = []
    for (region, district), stats in popular.items():
        popular_regions.append(
            {
                "region": region,
                "district": district,
                "label": format_region_label(region, district),
                **stats,
            }
        )
    popular_regions.sort(
        key=lambda item: (-int(item["score"]), -int(item["post_count"]), str(item["label"]))
    )

    popular_locations, top_rated_locations = _location_rankings(db)

    week_start = (now_kst - timedelta(days=now_kst.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = week_start + timedelta(days=7)
    start_utc = _as_utc_naive(week_start)
    end_utc = _as_utc_naive(week_end)

    view_dates = db.scalars(
        select(PostView.viewed_at).where(PostView.viewed_at >= start_utc, PostView.viewed_at < end_utc)
    ).all()
    like_dates = db.scalars(
        select(PostLike.created_at).where(PostLike.created_at >= start_utc, PostLike.created_at < end_utc)
    ).all()

    views = [0] * 7
    likes = [0] * 7
    for value in view_dates:
        views[_as_kst(value).weekday()] += 1
    for value in like_dates:
        likes[_as_kst(value).weekday()] += 1

    return {
        "monthly_category": {
            "labels": [f"{month}월" for _, month in month_keys],
            "series": [
                {"name": name, "data": monthly_counts[name]} for name, _ in MONTHLY_CATEGORIES
            ],
        },
        "category_distribution": {
            "total": _distribution(posts),
            "seoul": _distribution(posts, "서울"),
            "gyeonggi": _distribution(posts, "경기"),
        },
        "popular_regions": popular_regions[:6],
        "popular_locations": popular_locations,
        "top_rated_locations": top_rated_locations,
        "weekly_trend": {"labels": WEEKDAY_LABELS, "views": views, "likes": likes},
        "score_formula": "(댓글 수 × 3) + (좋아요 수 × 2) + 조회 수",
    }
