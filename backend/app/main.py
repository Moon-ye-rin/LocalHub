from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select

from .config import get_settings
from .database import Base, SessionLocal, engine, migrate_legacy_schema
from .models import Location
from .responses import fail
from .realtime import realtime_manager
from .routers import chat, dashboard, locations, posts, routes, share, tags
from .seed import seed_posts
from .seed_locations import seed_locations
from .services.location_service import visible_location_conditions

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_legacy_schema()
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    if settings.seed_data or settings.seed_locations:
        with SessionLocal() as db:
            if settings.seed_data:
                seed_posts(db)
            if settings.seed_locations:
                count = db.scalar(select(func.count()).select_from(Location)) or 0
                if count == 0:
                    seed_locations(db, settings.data_path)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.10.0-final",
    description=(
        "LocalHub 서울·경기 익명 커뮤니티 API. 제공된 서울·경기 TourAPI 데이터를 "
        "SQLite 캐시에 적재하고, 대표 이미지(firstimage)가 있는 항목만 노출합니다. "
        "게시글 좋아요 토글, 지역정보 댓글 CRUD·별점·좋아요·북마크·조회·근처 추천, "
        "OpenStreetMap 도로망 기반 A* 길찾기와 WebSocket 새 게시글 알림·접속자 현황을 제공합니다."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.upload_path, check_dir=False), name="uploads")
app.mount("/static", StaticFiles(directory="app/static", check_dir=False), name="static")
app.include_router(posts.router, prefix=settings.api_prefix)
app.include_router(tags.router, prefix=settings.api_prefix)
app.include_router(locations.router, prefix=settings.api_prefix)
app.include_router(routes.router, prefix=settings.api_prefix)
app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(share.router)


@app.websocket("/ws/notifications")
async def notifications_socket(websocket: WebSocket):
    client_key = (websocket.query_params.get("client_key") or "")[:64]
    await realtime_manager.connect(websocket, client_key)
    try:
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await realtime_manager.disconnect(websocket)
    except Exception:
        await realtime_manager.disconnect(websocket)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    data = {"match": False} if exc.status_code == 403 and "비밀번호" in str(exc.detail) else None
    return JSONResponse(status_code=exc.status_code, content=fail(str(exc.detail), data))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    message = first.get("msg", "요청 값 검증에 실패했습니다.")
    return JSONResponse(status_code=422, content=fail(str(message)))


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content=fail("서버 내부 오류가 발생했습니다."))


@app.get("/health", tags=["system"])
def health():
    with SessionLocal() as db:
        locations_count = db.scalar(select(func.count()).select_from(Location)) or 0
        visible_count = db.scalar(
            select(func.count()).select_from(Location).where(*visible_location_conditions())
        ) or 0
        rows = db.execute(
            select(Location.region, func.count())
            .where(*visible_location_conditions())
            .group_by(Location.region)
        ).all()
    return {
        "status": "ok",
        "service": "localhub-api",
        "locations": locations_count,
        "visible_locations": visible_count,
        "visible_by_region": {region: count for region, count in rows},
        "dataset": "서울·경기 TourAPI 4.0",
    }
