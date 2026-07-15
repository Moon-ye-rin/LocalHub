from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..responses import ok
from ..schemas import (
    ApiResponse,
    CreatedId,
    LocationCommentCreate,
    LocationCommentListData,
    LocationCommentUpdate,
    LocationDetail,
    LocationListData,
    LocationReactionData,
    PasswordRequest,
)
from ..services import location_service

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=ApiResponse[LocationListData])
def get_locations(
    region: str | None = Query(None, pattern="^(전체|서울|경기)$"),
    bookmarked_only: bool = Query(False),
    contenttypeid: str | None = Query(None, pattern="^(12|14|15|25|28|32|38|39)$"),
    keyword: str | None = Query(None, max_length=100),
    lDongSignguCd: str | None = Query(None, max_length=5),
    lclsSystm1: str | None = Query(None, max_length=10),
    lclsSystm2: str | None = Query(None, max_length=10),
    lclsSystm3: str | None = Query(None, max_length=10),
    page: int = Query(1, ge=1),
    size: int = Query(21, ge=1, le=100),
    x_client_key: str | None = Header(None, alias="X-Client-Key", max_length=64),
    db: Session = Depends(get_db),
):
    data = location_service.list_locations(
        db,
        region=region,
        bookmarked_only=bookmarked_only,
        client_key=x_client_key,
        contenttypeid=contenttypeid,
        keyword=keyword,
        lDongSignguCd=lDongSignguCd,
        lclsSystm1=lclsSystm1,
        lclsSystm2=lclsSystm2,
        lclsSystm3=lclsSystm3,
        page=page,
        size=size,
    )
    return ok(data)


@router.get("/{contentid}", response_model=ApiResponse[LocationDetail])
def get_location_detail(
    contentid: str,
    x_client_key: str | None = Header(None, alias="X-Client-Key", max_length=64),
    db: Session = Depends(get_db),
):
    return ok(location_service.get_location(db, contentid, x_client_key))


@router.get("/{contentid}/comments", response_model=ApiResponse[LocationCommentListData])
def get_location_comments(contentid: str, db: Session = Depends(get_db)):
    return ok(location_service.list_location_comments(db, contentid))


@router.post(
    "/{contentid}/comments",
    response_model=ApiResponse[CreatedId],
    status_code=status.HTTP_201_CREATED,
)
def create_location_comment(
    contentid: str,
    payload: LocationCommentCreate,
    db: Session = Depends(get_db),
):
    comment_id = location_service.create_location_comment(db, contentid, payload)
    return ok({"id": comment_id}, "댓글과 별점이 등록되었습니다.")


@router.put(
    "/{contentid}/comments/{comment_id}",
    response_model=ApiResponse[CreatedId],
)
def update_location_comment(
    contentid: str,
    comment_id: int,
    payload: LocationCommentUpdate,
    db: Session = Depends(get_db),
):
    updated_id = location_service.update_location_comment(db, contentid, comment_id, payload)
    return ok({"id": updated_id}, "댓글과 별점이 수정되었습니다.")


@router.delete(
    "/{contentid}/comments/{comment_id}",
    response_model=ApiResponse[None],
)
def delete_location_comment(
    contentid: str,
    comment_id: int,
    payload: PasswordRequest,
    db: Session = Depends(get_db),
):
    location_service.delete_location_comment(db, contentid, comment_id, payload.password)
    return ok(None, "댓글이 삭제되었습니다.")


@router.post("/{contentid}/like", response_model=ApiResponse[LocationReactionData])
def like_location(
    contentid: str,
    x_client_key: str | None = Header(None, alias="X-Client-Key", max_length=64),
    db: Session = Depends(get_db),
):
    return ok(location_service.like_location(db, contentid, x_client_key))


@router.delete("/{contentid}/like", response_model=ApiResponse[LocationReactionData])
def unlike_location(
    contentid: str,
    x_client_key: str | None = Header(None, alias="X-Client-Key", max_length=64),
    db: Session = Depends(get_db),
):
    return ok(location_service.unlike_location(db, contentid, x_client_key))


@router.post("/{contentid}/bookmark", response_model=ApiResponse[LocationReactionData])
def bookmark_location(
    contentid: str,
    x_client_key: str | None = Header(None, alias="X-Client-Key", max_length=64),
    db: Session = Depends(get_db),
):
    return ok(location_service.bookmark_location(db, contentid, x_client_key))


@router.delete("/{contentid}/bookmark", response_model=ApiResponse[LocationReactionData])
def unbookmark_location(
    contentid: str,
    x_client_key: str | None = Header(None, alias="X-Client-Key", max_length=64),
    db: Session = Depends(get_db),
):
    return ok(location_service.unbookmark_location(db, contentid, x_client_key))
