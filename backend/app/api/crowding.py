from fastapi import APIRouter, Query

router = APIRouter(
    prefix="/crowding",
    tags=["crowding"]
)

@router.get("/train")
def get_crowding(
    line: int = Query(..., description="지하철 노선 번호"),
    station: str = Query(..., description="역 이름"),
    direction: str = Query(..., description="상행 / 하행")
):
    """
    현재 / 다음 열차 혼잡도 반환
    """
    return {
        "currentTrain": "혼잡",
        "nextTrain": "보통",
        "trend": "down"
    }
