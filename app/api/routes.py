"""
경로 조회 API 라우터
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from app.schemas.route import RouteResponse, StationInfo
from app.services.route_service import RouteService, ComfortRouteService
from app.services.odsay_service import ODSayService

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


@router.get("", response_model=RouteResponse)
async def get_routes(
    departure: str = Query(..., description="출발역 이름 또는 ID"),
    arrival: str = Query(..., description="도착역 이름 또는 ID"),
    route_service: RouteService = Depends(get_route_service),
    comfort_route_service: ComfortRouteService = Depends(get_comfort_route_service)
):
    """
    경로 조회 API
    
    출발역과 도착역을 입력받아 3가지 경로를 반환합니다.
    출발 시간은 현재 시간으로 자동 설정됩니다.
    
    1. 최단 경로 (Fastest Route)
    2. 최소 걸음 경로 (Minimum Walk Route)
    3. 시간부자 전용 경로 (Comfort-Optimized Route)
    
    Args:
        departure: 출발역 이름 또는 ID
        arrival: 도착역 이름 또는 ID
        route_service: 경로 서비스
        comfort_route_service: 시간부자 경로 서비스
    
    Returns:
        RouteResponse: 3가지 경로 정보를 포함한 응답
    """
    try:
        # ODSay 서비스 인스턴스 생성 (역 정보 조회용)
        odsay_service = None
        try:
            odsay_service = ODSayService()
        except ValueError:
            pass  # API 키가 없으면 None으로 진행
        
        # 1. 먼저 ODSay API로 역 정보 조회 (역 이름으로 station_id, line_number 확인)
        departure_station = None
        arrival_station = None
        
        if odsay_service:
            try:
                # 출발역 정보 조회
                dep_stations = await odsay_service.search_station(departure)
                if dep_stations and len(dep_stations) > 0:
                    dep_station = dep_stations[0]
                    print(f"[API] 출발역 검색 결과: {dep_station}")
                    # ODSay API 응답 필드명 확인 (대소문자 주의)
                    # ODSay API는 "수도권 2호선" 형식으로 반환할 수 있음
                    station_id = dep_station.get("stationID") or dep_station.get("stationId") or dep_station.get("station_id") or ""
                    station_name = dep_station.get("stationName") or dep_station.get("station_name") or dep_station.get("name") or departure
                    lane_name = dep_station.get("laneName") or dep_station.get("lane_name") or dep_station.get("lane") or dep_station.get("line") or ""
                    
                    # "수도권 2호선" 형식 그대로 사용 (필요시 "2호선"만 추출 가능)
                    # if lane_name and "수도권" in lane_name:
                    #     lane_name = lane_name.replace("수도권 ", "")
                    
                    print(f"[API] 출발역 정보: ID={station_id}, 이름={station_name}, 호선={lane_name}")
                    print(f"[API] 출발역 원본 데이터: {dep_station}")
                    departure_station = StationInfo(
                        station_id=str(station_id) if station_id else "",
                        station_name=station_name if station_name else departure,
                        line_number=lane_name if lane_name else ""
                    )
            except Exception as e:
                print(f"출발역 정보 조회 실패: {str(e)}")
            
            try:
                # 도착역 정보 조회
                arr_stations = await odsay_service.search_station(arrival)
                if arr_stations and len(arr_stations) > 0:
                    arr_station = arr_stations[0]
                    print(f"[API] 도착역 검색 결과: {arr_station}")
                    # ODSay API 응답 필드명 확인 (대소문자 주의)
                    # ODSay API는 "수도권 2호선" 형식으로 반환할 수 있음
                    station_id = arr_station.get("stationID") or arr_station.get("stationId") or arr_station.get("station_id") or ""
                    station_name = arr_station.get("stationName") or arr_station.get("station_name") or arr_station.get("name") or arrival
                    lane_name = arr_station.get("laneName") or arr_station.get("lane_name") or arr_station.get("lane") or arr_station.get("line") or ""
                    
                    # "수도권 2호선" 형식 그대로 사용 (필요시 "2호선"만 추출 가능)
                    # if lane_name and "수도권" in lane_name:
                    #     lane_name = lane_name.replace("수도권 ", "")
                    
                    print(f"[API] 도착역 정보: ID={station_id}, 이름={station_name}, 호선={lane_name}")
                    print(f"[API] 도착역 원본 데이터: {arr_station}")
                    arrival_station = StationInfo(
                        station_id=str(station_id) if station_id else "",
                        station_name=station_name if station_name else arrival,
                        line_number=lane_name if lane_name else ""
                    )
            except Exception as e:
                print(f"도착역 정보 조회 실패: {str(e)}")
        
        # 역 정보가 없으면 기본값 설정
        if not departure_station:
            departure_station = StationInfo(
                station_id="",
                station_name=departure,
                line_number=""
            )
        if not arrival_station:
            arrival_station = StationInfo(
                station_id="",
                station_name=arrival,
                line_number=""
            )
        
        # 출발 시간은 현재 시간으로 자동 설정 (None 전달 시 서비스에서 현재 시간 사용)
        # 2. 최단 경로 조회
        fastest_route = await route_service.get_fastest_route(
            departure, arrival, None
        )
        
        # 3. 최소 걸음 경로 조회
        min_walk_route = await route_service.get_min_walk_route(
            departure, arrival, None
        )
        
        # 4. 시간부자 전용 경로 조회
        comfort_route = await comfort_route_service.get_comfort_route(
            departure, arrival, None
        )
        
        # 5. 경로 정보에서 역 정보가 더 정확하면 업데이트
        # (경로 정보의 역 정보가 더 정확할 수 있음)
        if fastest_route.segments:
            first_segment = fastest_route.segments[0]
            last_segment = fastest_route.segments[-1]
            
            # 출발역 정보 업데이트 (경로 정보가 더 정확하면)
            if first_segment.from_station.station_id or first_segment.from_station.line_number:
                departure_station = first_segment.from_station
            
            # 도착역 정보 업데이트 (경로 정보가 더 정확하면)
            if last_segment.to_station.station_id or last_segment.to_station.line_number:
                arrival_station = last_segment.to_station
        
        return RouteResponse(
            departure_station=departure_station,
            arrival_station=arrival_station,
            routes=[fastest_route, min_walk_route, comfort_route]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"경로 조회 중 오류가 발생했습니다: {str(e)}"
        )
