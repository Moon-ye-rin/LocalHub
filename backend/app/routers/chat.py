from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..responses import ok
from ..schemas import ApiResponse, ChatData, ChatRequest
from ..services.chat_service import answer_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ApiResponse[ChatData])
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        return ok(answer_chat(db, payload))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
