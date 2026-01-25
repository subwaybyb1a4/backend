"""
경로 조회 API 라우터
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
import uuid
from datetime import datetime, timedelta
from app.schemas.route import (
    RouteResponse, StationInfo, Route, RouteType, 
    SearchResponse, RouteDetail, SegmentResponse, SegmentType
)
from app.services.route_service import RouteService, ComfortRouteService
from app.services.odsay_service import ODSayService
from app.services.congestion_service import CongestionService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/routes", tags=["routes"])


def get_route_service() -> RouteService:
    """경로 서비스 의존성 주입"""
    odsay_service = None
    try:
        odsay_service = ODSayService()
        print(f"[API] ODSay 서비스 초기화 성공")
    except ValueError as e:
        print(f"[API] ODSay 서비스 초기화 실패: {str(e)}")
        odsay_service = None
    except Exception as e:
        print(f"[API] ODSay 서비스 초기화 중 예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        odsay_service = None
    return RouteService(odsay_service=odsay_service)


def get_comfort_route_service(route_service: RouteService = Depends(get_route_service)) -> ComfortRouteService:
    """시간부자 경로 서비스 의존성 주입"""
    return ComfortRouteService(route_service=route_service)


def map_route_to_detail(route: Route) -> RouteDetail:
    """Route 객체를 RouteDetail(Client용)로 변환"""
    
    # 1. Total Time (minutes)
    total_time = round(route.total_duration / 60)
    
    # 2. Arrival Time
    now = datetime.now()
    arrival_dt = now + timedelta(seconds=route.total_duration)
    # 24시간 형식 "HH:MM"
    arrival_time = arrival_dt.strftime("%H:%M")
    
    # 3. Total Walk Time (minutes)
    total_walk_time = round(route.total_walking_time / 60)
    
    # 4. Transfer Count
    transfer_count = len(route.transfers)
    
    # 5. Congestion Status
    congestion_status = "보통"
    if route.congestion_level:
        congestion_status = route.congestion_level
    
    # 6. Segments Construction
    # Interleave Subways with Transfer Walks
    new_segments = []
    
    transfer_idx = 0
    
    for i, seg in enumerate(route.segments):
        # Determine segment type and label
        seg_type = SegmentType.SUBWAY
        label = seg.line_number
        
        # Check if it is a walk segment
        # RouteService might label it "도보" or use empty line_number with walking logic
        is_walk_seg = (seg.line_number == "도보")
        
        start_name = None
        end_name = None
        
        if is_walk_seg:
            seg_type = SegmentType.WALK
            label = "도보"
        else:
            seg_type = SegmentType.SUBWAY
            label = seg.line_number
            if "수도권" in label:
                label = label.replace("수도권 ", "")
            
            # Populate start/end names for subway segments
            start_name = seg.from_station.station_name
            end_name = seg.to_station.station_name

        # Duration in minutes
        minutes = round(seg.duration / 60)
        # If less than 1 min but exists, show 1 min? Or 0? 
        if minutes == 0 and seg.duration > 0:
            minutes = 1
            
        new_segments.append(SegmentResponse(
            type=seg_type, 
            label=label, 
            minutes=minutes,
            start_station_name=start_name,
            end_station_name=end_name
        ))
        
        # Insert Transfer if needed
        # Condition: Current is Subway, Next is Subway, Lines differ
        if i < len(route.segments) - 1:
            next_seg = route.segments[i+1]
            curr_is_sub = (seg.line_number != "도보")
            next_is_sub = (next_seg.line_number != "도보")
            
            if curr_is_sub and next_is_sub and seg.line_number != next_seg.line_number:
                # Use transfer info if available
                trans_min = 5 # Default fallback
                if transfer_idx < len(route.transfers):
                    trans_info = route.transfers[transfer_idx]
                    trans_min = round(trans_info.walking_time / 60)
                    if trans_min == 0 and trans_info.walking_time > 0:
                        trans_min = 1
                    transfer_idx += 1
                
                new_segments.append(SegmentResponse(type=SegmentType.TRANSFER, label="환승", minutes=trans_min))

    # 7. Summary
    # Use comfort_explanation if comfort route, otherwise llm_description
    summary = route.llm_description
    if route.route_type == RouteType.COMFORT and route.comfort_explanation:
        summary = route.comfort_explanation

    return RouteDetail(
        congestion_status=congestion_status,
        total_time=total_time,
        arrival_time=arrival_time,
        total_walk_time=total_walk_time,
        transfer_count=transfer_count,
        segments=new_segments,
        summary=summary
    )


@router.get("", response_model=SearchResponse)
async def get_routes(
    departure: str = Query(..., description="출발역 이름 또는 ID"),
    arrival: str = Query(..., description="도착역 이름 또는 ID"),
    route_service: RouteService = Depends(get_route_service),
    comfort_route_service: ComfortRouteService = Depends(get_comfort_route_service)
):
    """
    경로 조회 API (Structured Response)
    """
    try:
        # Generate Search Group ID
        search_group_id = str(uuid.uuid4())
        
        # Services
        congestion_service = CongestionService()
        llm_service = LLMService()

        # 1. Get Fastest Route
        fastest_route = await route_service.get_fastest_route(departure, arrival, None)
        
        # 2. Get Min Walk Route
        min_walk_route = await route_service.get_min_walk_route(departure, arrival, None)
        
        # 3. Get Comfort Route Candidates (List[Route])
        comfort_candidates = await comfort_route_service.get_comfort_route(departure, arrival, None)
        
        # Process Fastest & Min Walk
        # Calculate congestion and LLM for them
        for r in [fastest_route, min_walk_route]:
            try:
                score, details = congestion_service.calculate_route_score(r)
                level = congestion_service.get_congestion_level(score)
                r.congestion_score = score
                r.congestion_level = level
                
                # Generate LLM desc
                r_dict = r.model_dump()
                desc = await llm_service.generate_route_explanation(r_dict, score, level, details)
                r.llm_description = desc
            except Exception as e:
                print(f"Error processing route {r.route_type}: {e}")
                r.congestion_level = "알 수 없음"

        # Process Comfort Candidates to find the BEST one (Min Crowding)
        # If list is empty, fallback to fastest
        best_comfort = None
        
        if not comfort_candidates:
            # Fallback: Just use fastest as comfort? Or clone it?
            best_comfort = fastest_route.model_copy()
            best_comfort.route_type = RouteType.COMFORT
            best_comfort.comfort_explanation = "추가적인 대안 경로가 없습니다."
        else:
            # Calculate congestion for all candidates
            for c in comfort_candidates:
                try:
                    score, details = congestion_service.calculate_route_score(c)
                    level = congestion_service.get_congestion_level(score)
                    c.congestion_score = score
                    c.congestion_level = level
                    # LLM desc might be expensive to run for ALL.
                    # ComfortRouteService already generated comfort_explanation?
                    # Let's check: comfort_candidates has comfort_explanation populated in service.
                except Exception as e:
                    print(f"Error processing comfort candidate: {e}")
            
            # Sort by Congestion Score (Ascending), then Total Duration
            # Filter valid scores if possible
            valid_candidates = [c for c in comfort_candidates if c.congestion_score is not None]
            if not valid_candidates:
                valid_candidates = comfort_candidates
                
            valid_candidates.sort(key=lambda x: (x.congestion_score or 1.0, x.total_duration))
            
            best_comfort = valid_candidates[0]
            
            # If best_comfort doesn't have explanation (maybe logic skipped it), generate it
            if not best_comfort.comfort_explanation:
                 # Generate LLM desc
                try:
                    score = best_comfort.congestion_score or 0.5
                    level = best_comfort.congestion_level or "보통"
                    details = {} # Need details? re-calc if needed but let's pass empty
                    r_dict = best_comfort.model_dump()
                    desc = await llm_service.generate_route_explanation(r_dict, score, level, details)
                    best_comfort.llm_description = desc
                    best_comfort.comfort_explanation = desc # Map to comfort explanation
                except:
                    pass

        # Map to Detail Models
        min_time_detail = map_route_to_detail(fastest_route)
        min_walking_detail = map_route_to_detail(min_walk_route)
        min_crowding_detail = map_route_to_detail(best_comfort)
        
        return SearchResponse(
            search_group_id=search_group_id,
            min_time=min_time_detail,
            min_crowding=min_crowding_detail,
            min_walking=min_walking_detail
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
