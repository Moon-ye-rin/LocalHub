from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..responses import ok
from ..schemas import AStarRouteData, AStarRouteRequest, ApiResponse
from ..services import route_service

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/astar", response_model=ApiResponse[AStarRouteData])
async def create_astar_route(
    payload: AStarRouteRequest,
    db: Session = Depends(get_db),
):
    return ok(await route_service.find_astar_route(db, payload))
