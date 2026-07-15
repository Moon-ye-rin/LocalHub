from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Header, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import PostImage
from ..responses import ok
from ..realtime import realtime_manager
from ..schemas import (
    ApiResponse,
    CommentCreate,
    CommentListData,
    CommentUpdate,
    CreatedId,
    ImageData,
    ImageDeleteRequest,
    LikeData,
    PasswordMatch,
    PasswordRequest,
    PostCreate,
    PostDetail,
    PostListData,
    PostUpdate,
)
from ..services import post_service

router = APIRouter(prefix="/posts", tags=["posts"])
settings = get_settings()
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}


@router.get("", response_model=ApiResponse[PostListData])
def get_posts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    category: str | None = Query(None, max_length=30),
    keyword: str | None = Query(None, max_length=100),
    tag: str | None = Query(None, max_length=30),
    sort: str = Query("latest", pattern="^(latest|views|likes)$"),
    db: Session = Depends(get_db),
):
    data = post_service.list_posts(
        db,
        page=page,
        size=size,
        category=category,
        keyword=keyword,
        tag=tag,
        sort=sort,
    )
    return ok(data)


@router.get("/{post_id}", response_model=ApiResponse[PostDetail])
def get_post(
    post_id: int,
    x_client_key: str | None = Header(None, alias="X-Client-Key", max_length=64),
    db: Session = Depends(get_db),
):
    return ok(post_service.read_post(db, post_id, x_client_key))


@router.post("", response_model=ApiResponse[CreatedId], status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, db: Session = Depends(get_db)):
    post_id = post_service.create_post(db, payload)
    await realtime_manager.publish_post_created(
        post_id=post_id,
        title=payload.title,
        category=payload.category,
        region=payload.region,
        district=payload.district,
    )
    return ok({"id": post_id}, "게시글이 등록되었습니다.")


@router.post("/{post_id}/verify-password", response_model=ApiResponse[PasswordMatch])
def verify_password(post_id: int, payload: PasswordRequest, db: Session = Depends(get_db)):
    post_service.verify_password(db, post_id, payload.password)
    return ok({"match": True})


@router.put("/{post_id}", response_model=ApiResponse[CreatedId])
def update_post(post_id: int, payload: PostUpdate, db: Session = Depends(get_db)):
    updated_id = post_service.update_post(db, post_id, payload)
    return ok({"id": updated_id}, "게시글이 수정되었습니다.")


@router.delete("/{post_id}", response_model=ApiResponse[None])
def delete_post(post_id: int, payload: PasswordRequest, db: Session = Depends(get_db)):
    post_service.delete_post(db, post_id, payload.password)
    return ok(None, "게시글이 삭제되었습니다.")


@router.post("/{post_id}/like", response_model=ApiResponse[LikeData])
def like_post(
    post_id: int,
    x_client_key: str | None = Header(None, alias="X-Client-Key", max_length=64),
    db: Session = Depends(get_db),
):
    return ok(post_service.like_post(db, post_id, x_client_key))


@router.delete("/{post_id}/like", response_model=ApiResponse[LikeData])
def unlike_post(
    post_id: int,
    x_client_key: str | None = Header(None, alias="X-Client-Key", max_length=64),
    db: Session = Depends(get_db),
):
    return ok(post_service.unlike_post(db, post_id, x_client_key))


@router.get("/{post_id}/comments", response_model=ApiResponse[CommentListData])
def get_comments(post_id: int, db: Session = Depends(get_db)):
    return ok(post_service.list_comments(db, post_id))


@router.post("/{post_id}/comments", response_model=ApiResponse[CreatedId], status_code=status.HTTP_201_CREATED)
def create_comment(post_id: int, payload: CommentCreate, db: Session = Depends(get_db)):
    comment_id = post_service.create_comment(db, post_id, payload)
    return ok({"id": comment_id}, "댓글이 등록되었습니다.")


@router.put("/{post_id}/comments/{comment_id}", response_model=ApiResponse[CreatedId])
def update_comment(post_id: int, comment_id: int, payload: CommentUpdate, db: Session = Depends(get_db)):
    updated_id = post_service.update_comment(db, post_id, comment_id, payload)
    return ok({"id": updated_id}, "댓글이 수정되었습니다.")


@router.delete("/{post_id}/comments/{comment_id}", response_model=ApiResponse[None])
def delete_comment(post_id: int, comment_id: int, payload: PasswordRequest, db: Session = Depends(get_db)):
    post_service.delete_comment(db, post_id, comment_id, payload.password)
    return ok(None, "댓글이 삭제되었습니다.")


@router.post("/{post_id}/images", response_model=ApiResponse[ImageData], status_code=status.HTTP_201_CREATED)
async def upload_post_image(
    post_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    post_service.require_post(db, post_id, options=False)
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="이미지는 5MB 이하만 업로드할 수 있습니다.")
    target_dir = settings.upload_path / str(post_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    target = target_dir / filename
    target.write_bytes(content)
    image_url = f"/uploads/{post_id}/{filename}"
    db.add(PostImage(post_id=post_id, image_url=image_url))
    db.commit()
    return ok({"image_url": image_url}, "이미지가 업로드되었습니다.")

@router.delete("/{post_id}/images", response_model=ApiResponse[None])
def delete_post_image(
    post_id: int,
    payload: ImageDeleteRequest,
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException

    post_service.verify_password(db, post_id, payload.password)
    image = db.scalar(
        select(PostImage).where(
            PostImage.post_id == post_id,
            PostImage.image_url == payload.image_url,
        )
    )
    if not image:
        raise HTTPException(status_code=404, detail="첨부 이미지를 찾을 수 없습니다.")

    relative_name = image.image_url.removeprefix("/uploads/")
    upload_root = settings.upload_path.resolve()
    target = (settings.upload_path / relative_name).resolve()
    if target.is_relative_to(upload_root) and target.is_file():
        target.unlink()
        try:
            target.parent.rmdir()
        except OSError:
            pass

    db.delete(image)
    db.commit()
    return ok(None, "첨부 이미지가 삭제되었습니다.")

