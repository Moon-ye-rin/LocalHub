from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Location, Post
from ..schemas import ChatRequest
from .location_service import visible_location_conditions

settings = get_settings()

INTENT_CODES = {
    "관광지": "12", "관광": "12", "가볼": "12", "명소": "12",
    "문화": "14", "박물관": "14", "미술관": "14",
    "축제": "15", "공연": "15", "행사": "15",
    "코스": "25", "여행코스": "25",
    "레포츠": "28", "운동": "28", "자전거": "28",
    "숙박": "32", "호텔": "32", "펜션": "32",
    "쇼핑": "38", "시장": "38",
    "맛집": "39", "음식점": "39", "먹을": "39",
}


def detect_code(message: str) -> str | None:
    lowered = message.lower()
    for keyword, code in INTENT_CODES.items():
        if keyword in lowered:
            return code
    return None


def detect_region(message: str) -> str | None:
    if "경기" in message or "경기도" in message:
        return "경기"
    if "서울" in message:
        return "서울"
    return None


def search_context(db: Session, message: str) -> tuple[list[Location], list[Post]]:
    code = detect_code(message)
    region = detect_region(message)
    loc_stmt = select(Location).where(*visible_location_conditions())

    if code:
        loc_stmt = loc_stmt.where(Location.contenttypeid == code)
    if region:
        loc_stmt = loc_stmt.where(Location.region == region)

    words = [word.strip(".,!?()[]") for word in message.split() if len(word.strip(".,!?()[]")) >= 2]
    stopwords = {
        "서울", "경기", "경기도", "관광지", "관광", "가볼", "명소", "문화", "박물관", "미술관",
        "축제", "공연", "행사", "코스", "여행코스", "레포츠", "운동", "자전거", "숙박", "호텔",
        "펜션", "쇼핑", "시장", "맛집", "음식점", "먹을", "추천", "추천해줘", "알려줘", "정보",
        "근처", "주변", "찾아줘", "보여줘",
    }
    location_filters = []
    post_filters = []
    for word in words[:6]:
        if word in stopwords:
            continue
        location_filters += [Location.title.ilike(f"%{word}%"), Location.addr1.ilike(f"%{word}%")]
        post_filters += [Post.title.ilike(f"%{word}%"), Post.content.ilike(f"%{word}%")]

    if location_filters:
        loc_stmt = loc_stmt.where(or_(*location_filters))
    locations = db.scalars(loc_stmt.order_by(Location.region, Location.title).limit(5)).all()

    post_stmt = select(Post)
    if post_filters:
        post_stmt = post_stmt.where(or_(*post_filters))
    posts = db.scalars(post_stmt.order_by(Post.created_at.desc()).limit(3)).all()
    return locations, posts


def local_reply(message: str, locations: list[Location], posts: list[Post]) -> str:
    lines: list[str] = []
    if locations:
        lines.append("관련 지역정보를 찾았습니다.")
        for item in locations:
            address = item.addr1 or "주소 미제공"
            lines.append(f"• [{item.region}] {item.title} — {address}")
    if posts:
        lines.append("\n커뮤니티에서 함께 확인할 글입니다.")
        for post in posts:
            lines.append(f"• {post.title}")
    if not lines:
        lines.append(
            "질문과 정확히 일치하는 데이터를 찾지 못했습니다. "
            "서울 또는 경기와 함께 장소명, 시·군·구 이름, 관광지·축제·숙박·음식점 같은 유형을 입력해 주세요."
        )
    lines.append("\n출처: 한국관광공사 TourAPI 4.0 · 공공누리 제3유형")
    return "\n".join(lines)


def build_references(locations: list[Location], posts: list[Post]) -> list[dict]:
    refs = [
        {"type": "location", "id": item.contentid, "name": f"[{item.region}] {item.title}"}
        for item in locations
    ]
    refs.extend({"type": "post", "id": str(post.id), "name": post.title} for post in posts)
    return refs[:8]


def answer_chat(db: Session, payload: ChatRequest) -> dict:
    locations, posts = search_context(db, payload.message)
    references = build_references(locations, posts)
    fallback = local_reply(payload.message, locations, posts)

    if not settings.use_openai or not settings.openai_api_key:
        return {"reply": fallback, "references": references, "mode": "local"}

    context_lines = [
        f"[관광정보/{item.region}] {item.title} | {item.addr1 or '주소 미제공'} | contentid={item.contentid}"
        for item in locations
    ]
    context_lines += [f"[게시글] {post.title} | {post.content[:300]}" for post in posts]
    prompt = (
        "너는 LocalHub 서울·경기 지역정보 도우미다. 아래 검색 결과 안에서만 답하고, "
        "모르는 정보는 모른다고 말한다. TourAPI 데이터 사용 시 답변 끝에 "
        "'출처: 한국관광공사 TourAPI 4.0 · 공공누리 제3유형'을 붙인다.\n\n"
        f"검색 결과:\n{chr(10).join(context_lines) if context_lines else '(없음)'}\n\n"
        f"질문: {payload.message}"
    )
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.create(model=settings.openai_model, input=prompt)
        reply = response.output_text.strip() or fallback
        return {"reply": reply, "references": references, "mode": "openai"}
    except Exception as exc:
        raise RuntimeError("챗봇 응답 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.") from exc
