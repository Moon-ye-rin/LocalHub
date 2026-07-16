"""LocalHub 챗봇 서비스.

v1.11.0 개선 사항
- 멀티턴 컨텍스트: 직전 대화(history)에서 지역·시군구·유형을 승계해
  "거기 근처는?" 같은 후속 질문을 이해한다.
- 시·군·구 단위 검색: regions.py의 자치구/시군 목록을 재활용해
  "종로구 문화시설" 같은 질의를 주소 기준으로 정확히 좁힌다.
- 관련도 랭킹: 제목 정확일치 > 제목 부분일치 > 주소 일치 순으로 정렬한다.
- 경로 안내 연동: "A에서 B 가는 길" 의도를 감지하면 무거운 A* 계산은
  하지 않고 경로 참조(reference)만 돌려준다. 실제 경로 계산은 사용자가
  버튼을 누를 때 프론트가 기존 /api/routes/astar 로 별도 호출하므로
  챗봇 응답 자체는 항상 빠르게 반환된다(외부 API 타임아웃 격리).
- OpenAI 폴백: 외부 LLM 호출이 실패해도 502로 끊지 않고 로컬 검색
  결과로 우아하게 대체한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import CONTENT_TYPES, Location, Post
from ..regions import GYEONGGI_MUNICIPALITIES, SEOUL_DISTRICTS
from ..schemas import ChatRequest
from .location_service import visible_location_conditions

settings = get_settings()

SOURCE_NOTICE = "출처: 한국관광공사 TourAPI 4.0 · 공공누리 제3유형"

INTENT_CODES = {
    "관광지": "12", "관광": "12", "가볼": "12", "명소": "12", "명소들": "12",
    "문화": "14", "박물관": "14", "미술관": "14", "전시": "14",
    "축제": "15", "공연": "15", "행사": "15", "이벤트": "15",
    "코스": "25", "여행코스": "25",
    "레포츠": "28", "운동": "28", "자전거": "28", "등산": "28",
    "숙박": "32", "호텔": "32", "펜션": "32", "게스트하우스": "32", "숙소": "32",
    "쇼핑": "38", "시장": "38", "아울렛": "38",
    "맛집": "39", "음식점": "39", "먹을": "39", "밥집": "39", "카페": "39", "식당": "39",
}

# 시·군·구 → 소속 지역(서울/경기) 역참조 테이블
DISTRICT_TO_REGION: dict[str, str] = {name: "서울" for name in SEOUL_DISTRICTS}
DISTRICT_TO_REGION.update({name: "경기" for name in GYEONGGI_MUNICIPALITIES})

# 경로 안내 의도를 나타내는 표현
ROUTE_HINT_WORDS = ("가는 길", "가는길", "경로", "길찾기", "길 안내", "route", "어떻게 가", "가려면")
ROUTE_CONNECTORS = ("에서", "부터", "->", "→", "~")

STOPWORDS = {
    "서울", "경기", "경기도", "추천", "추천해줘", "추천해", "알려줘", "정보", "좀",
    "근처", "주변", "찾아줘", "보여줘", "어디", "있어", "있나요", "해줘", "관련",
    "그리고", "그럼", "그러면", "거기", "여기", "그곳", "저곳",
    *INTENT_CODES.keys(),
    *SEOUL_DISTRICTS,
    *GYEONGGI_MUNICIPALITIES,
}


@dataclass(slots=True)
class QueryContext:
    """한 번의 질문에서 해석한 검색 조건."""

    region: str | None = None
    district: str | None = None
    code: str | None = None
    keywords: list[str] = field(default_factory=list)
    route_from: str | None = None
    route_to: str | None = None

    @property
    def wants_route(self) -> bool:
        return bool(self.route_from and self.route_to)


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


def detect_district(message: str) -> str | None:
    """메시지에서 서울 자치구 또는 경기 시·군 이름을 찾는다."""
    for name in DISTRICT_TO_REGION:
        if name in message:
            return name
    return None


def detect_route_intent(message: str) -> tuple[str | None, str | None]:
    """'A에서 B 가는 길' 형태에서 출발지·도착지 후보를 뽑는다.

    실제 장소 매칭은 이후 DB 조회로 수행하고, 여기서는 문자열만 분리한다.
    """
    if not any(hint in message.lower() for hint in ROUTE_HINT_WORDS):
        return None, None

    text = message
    # 경로 힌트 표현은 도착지 뒤에 붙으므로 제거해 도착지 이름을 깔끔히 만든다.
    for hint in ROUTE_HINT_WORDS:
        text = re.sub(re.escape(hint), " ", text, flags=re.IGNORECASE)

    # "A에서 B", "A부터 B", "A -> B" 등을 분리
    for connector in ROUTE_CONNECTORS:
        if connector in text:
            left, _, right = text.partition(connector)
            start = _clean_place(left)
            end = _clean_place(right)
            if start and end:
                return start, end
    return None, None


def _clean_place(value: str) -> str:
    cleaned = value.strip(" .,!?()[]~-")
    # 유형/장식어를 제거해 순수 장소명에 가깝게 만든다.
    for token in ("까지", "으로", "로", "에", "좀", "여기", "거기"):
        if cleaned.endswith(token):
            cleaned = cleaned[: -len(token)].strip()
    return cleaned.strip()


def inherit_from_history(context: QueryContext, history: list) -> QueryContext:
    """이번 질문에서 빠진 지역·시군구·유형을 직전 대화에서 물려받는다."""
    if context.region and context.district and context.code:
        return context

    # history는 최신이 뒤에 오므로 역순으로 사용자 발화를 살핀다.
    for item in reversed(history):
        role = getattr(item, "role", None)
        content = getattr(item, "content", "") or ""
        if role != "user":
            continue
        if context.region is None:
            context.region = detect_region(content)
        if context.district is None:
            context.district = detect_district(content)
        if context.code is None:
            context.code = detect_code(content)
        if context.region and context.district and context.code:
            break

    # 시군구를 알면 지역은 자동으로 확정된다.
    if context.district and not context.region:
        context.region = DISTRICT_TO_REGION.get(context.district)
    return context


def parse_query(message: str, history: list) -> QueryContext:
    route_from, route_to = detect_route_intent(message)
    district = detect_district(message)
    region = detect_region(message)
    if district and not region:
        region = DISTRICT_TO_REGION.get(district)

    words = [w.strip(".,!?()[]~") for w in message.split()]
    keywords = [w for w in words if len(w) >= 2 and w not in STOPWORDS][:6]

    context = QueryContext(
        region=region,
        district=district,
        code=detect_code(message),
        keywords=keywords,
        route_from=route_from,
        route_to=route_to,
    )
    return inherit_from_history(context, history)


def _match_location_by_name(db: Session, name: str, region: str | None) -> Location | None:
    """장소명 문자열로 가장 그럴듯한 Location 한 건을 찾는다(경로 출발/도착 매칭용).

    '강남구'·'수원시' 같은 순수 지역명은 특정 장소가 아니므로 경로 지점으로
    받아들이지 않는다. 또한 제목(title)에 이름이 들어간 경우만 인정해
    주소만 우연히 겹치는 엉뚱한 장소가 매칭되는 것을 막는다.
    """
    if not name:
        return None
    # 자치구·시군 이름 자체는 장소가 아니라 지역이므로 경로 지점에서 제외한다.
    if name in DISTRICT_TO_REGION:
        return None

    stmt = select(Location).where(*visible_location_conditions())
    if region:
        stmt = stmt.where(Location.region == region)
    # 제목 정확일치를 최우선, 다음으로 접두 일치, 부분 일치 순.
    score = case(
        (func.lower(Location.title) == name.lower(), 3),
        (Location.title.ilike(f"{name}%"), 2),
        (Location.title.ilike(f"%{name}%"), 1),
        else_=0,
    )
    # 주소만 겹치는 항목은 배제하고, 제목에 이름이 포함된 장소만 대상으로 한다.
    stmt = stmt.where(Location.title.ilike(f"%{name}%"))
    stmt = stmt.order_by(score.desc(), Location.title).limit(1)
    return db.scalar(stmt)


def _base_location_stmt(context: QueryContext):
    stmt = select(Location).where(*visible_location_conditions())
    if context.code:
        stmt = stmt.where(Location.contenttypeid == context.code)
    if context.region:
        stmt = stmt.where(Location.region == context.region)
    if context.district:
        # 주소에 자치구/시군 이름이 포함된 항목으로 좁힌다.
        stmt = stmt.where(Location.addr1.ilike(f"%{context.district}%"))
    return stmt


def _apply_ranking(stmt, keywords: list[str]):
    """제목 정확일치 > 제목 부분일치 > 주소 일치 순으로 정렬한다."""
    if keywords:
        first = keywords[0]
        relevance = case(
            (func.lower(Location.title) == first.lower(), 3),
            (Location.title.ilike(f"%{first}%"), 2),
            (Location.addr1.ilike(f"%{first}%"), 1),
            else_=0,
        )
        return stmt.order_by(relevance.desc(), Location.region, Location.title)
    return stmt.order_by(Location.region, Location.title)


def search_locations(db: Session, context: QueryContext) -> list[Location]:
    stmt = _base_location_stmt(context)

    filters = []
    for word in context.keywords:
        filters += [Location.title.ilike(f"%{word}%"), Location.addr1.ilike(f"%{word}%")]

    keyword_stmt = stmt.where(or_(*filters)) if filters else stmt
    results = db.scalars(_apply_ranking(keyword_stmt, context.keywords).limit(5)).all()

    # 멀티턴 후속 질문 대응: 지역·시군구·유형이 이미 잡혀 있는데
    # 키워드가 데이터와 안 맞아 결과가 비면, 키워드를 완화하고
    # 승계된 지역/유형 조건만으로 다시 찾는다.
    has_scope = bool(context.code or context.region or context.district)
    if not results and filters and has_scope:
        results = db.scalars(_apply_ranking(stmt, []).limit(5)).all()

    return results


def search_posts(db: Session, context: QueryContext) -> list[Post]:
    stmt = select(Post)
    filters = []
    for word in context.keywords:
        filters += [Post.title.ilike(f"%{word}%"), Post.content.ilike(f"%{word}%")]
    if context.district:
        filters.append(Post.district == context.district)
    if filters:
        stmt = stmt.where(or_(*filters))
    return db.scalars(stmt.order_by(Post.created_at.desc()).limit(3)).all()


@dataclass(slots=True)
class RouteResolution:
    """경로 매칭 결과. 두 장소를 모두 찾으면 pair가 채워진다."""

    pair: tuple[Location, Location] | None = None
    start_name: str = ""
    end_name: str = ""
    start_found: bool = False
    end_found: bool = False

    @property
    def matched(self) -> bool:
        return self.pair is not None


def resolve_route(db: Session, context: QueryContext) -> RouteResolution | None:
    """경로 의도가 있으면 출발지·도착지 Location을 매칭한다.

    한쪽만 찾은 경우에도 사용자에게 안내할 수 있도록 부분 결과를 담아 돌려준다.
    """
    if not context.wants_route:
        return None
    start = _match_location_by_name(db, context.route_from, context.region)
    end = _match_location_by_name(db, context.route_to, context.region)
    resolution = RouteResolution(
        start_name=context.route_from or "",
        end_name=context.route_to or "",
        start_found=start is not None,
        end_found=end is not None,
    )
    if start and end and start.contentid != end.contentid:
        resolution.pair = (start, end)
    return resolution


def type_label(code: str | None) -> str:
    return CONTENT_TYPES.get(code, "") if code else ""


def local_reply(
    context: QueryContext,
    locations: list[Location],
    posts: list[Post],
    route: RouteResolution | None,
) -> str:
    lines: list[str] = []

    if route and route.matched:
        start, end = route.pair
        lines.append(
            f"🗺️ '{start.title}'에서 '{end.title}'까지의 경로를 준비했어요.\n"
            "아래 '경로 보기'를 누르면 지도에서 실제 도로 기반 길안내(도보/자동차)를 확인할 수 있습니다."
        )
        if locations:
            lines.append("")
    elif route:
        # 한쪽 이상을 못 찾은 경우 사용자에게 검색을 유도한다.
        missing = []
        if not route.start_found:
            missing.append(f"출발지 '{route.start_name}'")
        if not route.end_found:
            missing.append(f"도착지 '{route.end_name}'")
        target = " · ".join(missing) if missing else "두 장소"
        lines.append(
            f"경로를 그리려 했지만 {target}에 정확히 맞는 장소를 찾지 못했어요.\n"
            "정식 명칭으로 다시 알려주시면 경로를 안내해 드릴게요. "
            "(예: '남산타워' 대신 'N서울타워')"
        )
        if locations:
            lines.append("")

    if locations:
        label = type_label(context.code)
        scope = context.district or context.region
        header = "관련 장소를 찾았어요"
        if scope and label:
            header = f"{scope} {label} 정보예요"
        elif scope:
            header = f"{scope} 관련 장소예요"
        lines.append(f"{header}:")
        for item in locations:
            address = item.addr1 or "주소 미제공"
            lines.append(f"• [{item.region}] {item.title} — {address}")

    if posts:
        lines.append("\n커뮤니티에서 함께 확인할 글이에요:")
        for post in posts:
            lines.append(f"• {post.title}")

    if not lines:
        lines.append(
            "질문과 딱 맞는 데이터를 찾지 못했어요. "
            "'서울'·'경기' 또는 '강남구'·'수원시' 같은 지역명과 함께 "
            "관광지·축제·숙박·맛집 같은 유형을 넣어주시면 더 잘 찾아드려요."
        )

    lines.append(f"\n{SOURCE_NOTICE}")
    return "\n".join(lines)


def build_references(
    locations: list[Location],
    posts: list[Post],
    route: RouteResolution | None,
) -> list[dict]:
    refs: list[dict] = []
    if route and route.matched:
        start, end = route.pair
        # 프론트가 이 참조로 /locations/{start}?to={end} 경로 화면을 연다.
        refs.append(
            {
                "type": "route",
                "id": f"{start.contentid}:{end.contentid}",
                "name": f"🗺️ {start.title} → {end.title} 경로 보기",
            }
        )
    refs += [
        {"type": "location", "id": item.contentid, "name": f"[{item.region}] {item.title}"}
        for item in locations
    ]
    refs += [{"type": "post", "id": str(post.id), "name": post.title} for post in posts]
    return refs[:8]


def build_openai_context(
    locations: list[Location],
    posts: list[Post],
    route: RouteResolution | None,
) -> str:
    lines: list[str] = []
    if route and route.matched:
        start, end = route.pair
        lines.append(
            f"[경로요청] 출발={start.title}({start.addr1 or '주소미상'}) / "
            f"도착={end.title}({end.addr1 or '주소미상'}) — 사용자가 지도 버튼으로 확인 가능"
        )
    lines += [
        f"[관광정보/{item.region}] {item.title} | {item.addr1 or '주소 미제공'} | contentid={item.contentid}"
        for item in locations
    ]
    lines += [f"[게시글] {post.title} | {post.content[:300]}" for post in posts]
    return "\n".join(lines) if lines else "(없음)"


def try_openai_reply(message: str, context_block: str) -> str | None:
    """OpenAI 응답을 시도한다. 실패하면 None을 돌려 로컬 답변으로 폴백한다."""
    prompt = (
        "너는 LocalHub 서울·경기 지역정보 도우미다. 아래 검색 결과 안에서만 답하고, "
        "모르는 정보는 모른다고 말한다. [경로요청]이 있으면 출발지와 도착지 이름을 언급하며 "
        "'아래 경로 보기 버튼을 누르면 지도에서 길안내를 확인할 수 있어요'라고 안내한다. "
        f"답변 끝에는 '{SOURCE_NOTICE}'를 붙인다.\n\n"
        f"검색 결과:\n{context_block}\n\n"
        f"질문: {message}"
    )
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.create(model=settings.openai_model, input=prompt)
        text = (response.output_text or "").strip()
        return text or None
    except Exception:
        # 네트워크·인증·쿼터 등 어떤 실패든 로컬 답변으로 대체한다.
        return None


def answer_chat(db: Session, payload: ChatRequest) -> dict:
    context = parse_query(payload.message, payload.history)
    route = resolve_route(db, context)
    locations = search_locations(db, context)
    posts = search_posts(db, context)

    references = build_references(locations, posts, route)
    fallback = local_reply(context, locations, posts, route)

    if not settings.use_openai or not settings.openai_api_key:
        return {
            "reply": fallback,
            "references": references,
            "mode": "local",
            "source_notice": SOURCE_NOTICE,
        }

    context_block = build_openai_context(locations, posts, route)
    reply = try_openai_reply(payload.message, context_block)
    if reply is None:
        # LLM 실패 시에도 대화를 끊지 않고 로컬 결과를 반환한다.
        return {
            "reply": fallback,
            "references": references,
            "mode": "local",
            "source_notice": SOURCE_NOTICE,
        }

    return {
        "reply": reply,
        "references": references,
        "mode": "openai",
        "source_notice": SOURCE_NOTICE,
    }
