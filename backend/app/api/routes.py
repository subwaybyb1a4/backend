from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.schemas.route import RouteRequest, MultiRouteResponse
from app.services.route_service import route_service
from app.db.session import get_db

router = APIRouter(
    prefix="/routes",
    tags=["routes"]
)


@router.post(
    "/search",
    response_model=MultiRouteResponse,
    status_code=status.HTTP_200_OK
)
async def search_routes(
    route_request: RouteRequest,
    db: Session = Depends(get_db)
):
    """
    출발역 → 도착역 경로 탐색

    반환:
    - 최단 경로
    - 최소 걸음 경로
    - 시간부자(혼잡 최소) 경로
    """
    
    try:
        return await route_service.find_routes(route_request, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route search failed: {str(e)}"
        )
