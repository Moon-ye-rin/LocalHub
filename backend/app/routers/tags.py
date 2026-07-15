from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..responses import ok
from ..schemas import ApiResponse, TagListData
from ..services.post_service import list_tags

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=ApiResponse[TagListData])
def get_tags(popular: bool = Query(False), db: Session = Depends(get_db)):
    return ok({"tags": list_tags(db, popular)})
