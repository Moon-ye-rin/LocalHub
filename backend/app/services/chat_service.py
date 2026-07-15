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
    "attraction": "12", "attractions": "12", "sightseeing": "12", "landmark": "12",
    "문화": "14", "박물관": "14", "미술관": "14",
    "culture": "14", "cultural": "14", "museum": "14", "gallery": "14",
    "축제": "15", "공연": "15", "행사": "15",
    "festival": "15", "festivals": "15", "event": "15", "events": "15", "performance": "15",
    "코스": "25", "여행코스": "25", "course": "25", "itinerary": "25", "route": "25",
    "레포츠": "28", "운동": "28", "자전거": "28", "sports": "28", "leisure": "28", "cycling": "28",
    "숙박": "32", "호텔": "32", "펜션": "32", "hotel": "32", "accommodation": "32", "stay": "32",
    "쇼핑": "38", "시장": "38", "shopping": "38", "market": "38",
    "맛집": "39", "음식점": "39", "먹을": "39", "restaurant": "39", "restaurants": "39", "food": "39", "dining": "39",
}


def detect_code(message: str) -> str | None:
    lowered = message.lower()
    for keyword, code in INTENT_CODES.items():
        if keyword in lowered:
            return code
    return None


def detect_region(message: str) -> str | None:
    lowered = message.lower()
    if "경기" in message or "경기도" in message or "gyeonggi" in lowered:
        return "경기"
    if "서울" in message or "seoul" in lowered:
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
        "근처", "주변", "찾아줘", "보여줘", "seoul", "gyeonggi", "recommend", "show", "find", "near",
        "nearby", "information", "place", "places", "attraction", "attractions", "culture", "cultural",
        "festival", "festivals", "event", "events", "hotel", "accommodation", "shopping", "restaurant",
        "restaurants", "food", "community", "post", "posts", "about", "the", "and", "for", "in",
    }
    location_filters = []
    post_filters = []
    for word in words[:6]:
        if word.lower() in stopwords:
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


def local_reply(message: str, locations: list[Location], posts: list[Post], language: str) -> str:
    lines: list[str] = []
    if language == "en":
        if locations:
            lines.append("I found these related places. Names and addresses are shown in the original Korean source data.")
            for item in locations:
                address = item.addr1 or "Address unavailable"
                region = "Seoul" if item.region == "서울" else "Gyeonggi"
                lines.append(f"• [{region}] {item.title} — {address}")
        if posts:
            lines.append("\nRelated community posts:")
            for post in posts:
                lines.append(f"• {post.title}")
        if not lines:
            lines.append(
                "I could not find an exact match. Try including Seoul or Gyeonggi, a Korean place/district name, "
                "or a type such as attractions, festivals, accommodation, shopping, or restaurants."
            )
        lines.append("\nSource: Korea Tourism Organization TourAPI 4.0 · KOGL Type 3")
        return "\n".join(lines)

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


def build_references(locations: list[Location], posts: list[Post], language: str) -> list[dict]:
    def region_label(value: str) -> str:
        if language == "en":
            return "Seoul" if value == "서울" else "Gyeonggi"
        return value

    refs = [
        {"type": "location", "id": item.contentid, "name": f"[{region_label(item.region)}] {item.title}"}
        for item in locations
    ]
    refs.extend({"type": "post", "id": str(post.id), "name": post.title} for post in posts)
    return refs[:8]


def answer_chat(db: Session, payload: ChatRequest) -> dict:
    locations, posts = search_context(db, payload.message)
    references = build_references(locations, posts, payload.language)
    fallback = local_reply(payload.message, locations, posts, payload.language)
    source_notice = (
        "Source: Korea Tourism Organization TourAPI 4.0 · KOGL Type 3"
        if payload.language == "en"
        else "출처: 한국관광공사 TourAPI 4.0 · 공공누리 제3유형"
    )

    if not settings.use_openai or not settings.openai_api_key:
        return {"reply": fallback, "references": references, "mode": "local", "source_notice": source_notice}

    context_lines = [
        f"[Tourism/{item.region}] {item.title} | {item.addr1 or '주소 미제공'} | contentid={item.contentid}"
        for item in locations
    ]
    context_lines += [f"[Community post] {post.title} | {post.content[:300]}" for post in posts]
    if payload.language == "en":
        prompt = (
            "You are the LocalHub guide for Seoul and Gyeonggi. Answer in English using only the search results below. "
            "Do not translate or alter TourAPI place names and addresses; preserve the original Korean source strings. "
            "If the information is unavailable, say so. End answers using TourAPI data with "
            "'Source: Korea Tourism Organization TourAPI 4.0 · KOGL Type 3'.\n\n"
            f"Search results:\n{chr(10).join(context_lines) if context_lines else '(none)'}\n\n"
            f"Question: {payload.message}"
        )
    else:
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
        return {"reply": reply, "references": references, "mode": "openai", "source_notice": source_notice}
    except Exception as exc:
        message = (
            "An error occurred while generating the chatbot response. Please try again shortly."
            if payload.language == "en"
            else "챗봇 응답 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )
        raise RuntimeError(message) from exc
