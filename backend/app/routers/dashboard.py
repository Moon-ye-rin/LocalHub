from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..responses import ok
from ..schemas import ApiResponse, DashboardData
from ..services.dashboard_service import build_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=ApiResponse[DashboardData])
def get_dashboard(db: Session = Depends(get_db)):
    return ok(build_dashboard(db))
