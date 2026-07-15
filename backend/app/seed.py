from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Post, Tag

INITIAL_POSTS = [
    {
        "category": "관광지",
        "region": "서울",
        "district": "종로구",
        "title": "경복궁 근처 서촌 산책 코스 추천해요",
        "content": "경복궁 관람 후 서촌 골목과 통인시장까지 걸으면 반나절 코스로 좋습니다. 공공데이터 장소 정보도 함께 확인해 보세요.",
        "password": "1234",
        "tags": ["경복궁", "서촌", "산책"],
    },
    {
        "category": "축제공연행사",
        "region": "서울",
        "district": "중구",
        "title": "서울 축제 정보는 날짜를 꼭 확인하세요",
        "content": "축제 데이터의 modifiedtime과 공식 홈페이지를 함께 확인하면 일정 변경에 대응하기 좋습니다.",
        "password": "5678",
        "tags": ["서울", "축제", "일정"],
    },
    {
        "category": "쇼핑",
        "region": "경기",
        "district": "수원시",
        "title": "전통시장 방문 후기 공유합니다",
        "content": "주소와 영업시간은 방문 직전에 다시 확인하는 것을 추천합니다. 지역별 후기도 댓글 대신 새 글로 자유롭게 공유해 주세요.",
        "password": "1111",
        "tags": ["전통시장", "쇼핑", "후기"],
    },
    {
        "category": "레포츠",
        "region": "서울",
        "district": "영등포구",
        "title": "한강공원 자전거 이용 팁",
        "content": "주말에는 이용자가 많아 이른 시간 방문이 편했습니다. 안전장비를 챙기고 현장 운영 정보를 확인하세요.",
        "password": "2222",
        "tags": ["한강", "자전거", "레포츠"],
    },
]


def get_or_create_tag(db: Session, name: str) -> Tag:
    tag = db.scalar(select(Tag).where(func.lower(Tag.name) == name.lower()))
    if tag:
        return tag
    tag = Tag(name=name)
    db.add(tag)
    db.flush()
    return tag


def seed_posts(db: Session) -> int:
    existing = db.scalar(select(func.count()).select_from(Post)) or 0
    if existing:
        return existing
    for item in INITIAL_POSTS:
        tags = [get_or_create_tag(db, name) for name in item["tags"]]
        post = Post(
            category=item["category"],
            region=item["region"],
            district=item["district"],
            title=item["title"],
            content=item["content"],
            password=item["password"],
            tags=tags,
        )
        db.add(post)
    db.commit()
    return len(INITIAL_POSTS)
