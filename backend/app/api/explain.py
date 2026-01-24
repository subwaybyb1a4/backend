from fastapi import APIRouter, HTTPException
from app.schemas.route import ComfortExplainRequest, ComfortExplainResponse
from app.services.llm_service import llm_service

router = APIRouter(
    prefix="/explain",
    tags=["explain"]
)

@router.post(
    "/comfort",
    response_model=ComfortExplainResponse
)
async def explain_comfort_route(req: ComfortExplainRequest):
    """
    시간부자(혼잡 최소) 경로에 대한 설명 생성 (LLM)
    """
    try:
        sentence = await llm_service.generate_comfort_explanation(
            path=req.path,
            crowding_summary=req.crowdingSummary
        )
        return {"sentence": sentence}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Explanation failed: {str(e)}"
        )
