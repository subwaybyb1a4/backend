from fastapi import APIRouter, HTTPException, Query
from app.schemas.route import FavoriteRequest, FavoriteResponse

router = APIRouter(
    prefix="/favorites",
    tags=["favorites"]
)

FAKE_DB: list[dict] = []
ID_SEQ = 1


@router.post("", response_model=FavoriteResponse)
def save_favorite(req: FavoriteRequest):
    global ID_SEQ
    favorite = {
        "id": ID_SEQ,
        "deviceId": req.deviceId,
        "from_station": req.from_station,
        "to_station": req.to_station,
        "type": req.type
    }
    FAKE_DB.append(favorite)
    ID_SEQ += 1
    return favorite


@router.get("", response_model=list[FavoriteResponse])
def get_favorites(
    deviceId: str = Query(..., description="디바이스 식별자")
):
    return [f for f in FAKE_DB if f["deviceId"] == deviceId]


@router.delete("/{favorite_id}")
def delete_favorite(favorite_id: int):
    global FAKE_DB
    FAKE_DB = [f for f in FAKE_DB if f["id"] != favorite_id]
    return {"status": "deleted"}
