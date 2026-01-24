from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.db.models import Route, SavedRoute, RouteType
from app.schemas.route import (
    RouteRequest,
    RouteResponse,
    MultiRouteResponse,
    TransitInfo,
    RouteTypeEnum
)
from app.services.odsay_service import odsay_service
from app.services.llm_service import llm_service
from app.services.realtime_service import realtime_service
from app.core.config import settings


class RouteService:
    """Service for managing routes and integrating ODSay + Crowding + LLM services"""
    
    async def find_routes(
        self,
        route_request: RouteRequest,
        db: Session
    ) -> MultiRouteResponse:
        """
        Find all 3 optimal route types based on user request
        
        Args:
            route_request: Route search request
            db: Database session
            
        Returns:
            Multi-route response with all 3 route options
        """
        # Generate unique search group ID
        search_group_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Get coordinates
        start_coords = await self._get_coordinates(route_request.start_location)
        end_coords = await self._get_coordinates(route_request.end_location)
        
        # Determine which route types to search
        search_types = route_request.search_types or [
            RouteTypeEnum.FASTEST,
            RouteTypeEnum.LEAST_WALKING,
            RouteTypeEnum.COMFORT_OPTIMIZED
        ]
        
        routes = []
        fastest_time = None
        
        # Search for each route type
        # FASTEST and LEAST_WALKING: directly from ODSay API
        # COMFORT_OPTIMIZED: custom prediction model (TODO: 미완성)
        for route_type in search_types:
            try:
                route = await self._search_single_route(
                    route_type=route_type,
                    start_location=route_request.start_location,
                    end_location=route_request.end_location,
                    start_coords=start_coords,
                    end_coords=end_coords,
                    search_group_id=search_group_id,
                    db=db
                )
                
                if route:
                    routes.append(route)
                    
                    # Track fastest time for comfort route constraint
                    if route_type == RouteTypeEnum.FASTEST:
                        fastest_time = route.transit_info.total_time
                        
            except Exception as e:
                print(f"Error searching {route_type}: {str(e)}")
                continue
        
        # Apply comfort route time constraint (max +15 min from fastest)
        # TODO: 자체 예측 모델 개발 시 이 필터링 로직은 모델 내부로 이동 예정
        if fastest_time is not None:
            routes = self._filter_comfort_route_time(routes, fastest_time)
        
        # Generate LLM explanations with comparison data
        routes = await self._add_explanations(routes, fastest_time)
        
        # Build comparison metadata
        comparison = self._build_comparison_data(routes)
        
        return MultiRouteResponse(
            search_group_id=search_group_id,
            routes=routes,
            comparison=comparison
        )
    
    async def _search_single_route(
        self,
        route_type: RouteTypeEnum,
        start_location: str,
        end_location: str,
        start_coords: dict,
        end_coords: dict,
        search_group_id: str,
        db: Session,
        fastest_time: Optional[int] = None
    ) -> Optional[RouteResponse]:
        """Search for a single route type"""
        
        # Map route type to ODSay search type
        # FASTEST and LEAST_WALKING are directly from ODSay API
        # COMFORT_OPTIMIZED will use custom prediction model (TODO: 미완성)
        odsay_search_type = {
            RouteTypeEnum.FASTEST: 0,  # ODSay: Optimal (fastest)
            RouteTypeEnum.LEAST_WALKING: 3,  # ODSay: Least walking
            RouteTypeEnum.COMFORT_OPTIMIZED: 0  # TODO: 자체 예측 모델 개발 예정 (현재 임시로 최적 경로 사용)
        }.get(route_type, 0)
        
        # Search route using ODSay API
        raw_route = await odsay_service.search_pub_trans_path(
            start_x=start_coords["x"],
            start_y=start_coords["y"],
            end_x=end_coords["x"],
            end_y=end_coords["y"],
            search_type=odsay_search_type
        )
        
        # Parse route information
        route_info = odsay_service.parse_route_info(raw_route)
        
        if not route_info:
            return None
        
        # Calculate crowding score
        crowding_score = realtime_service.calculate_route_crowding_score(
            route_info.get("path_details", [])
        )
        
        # Extract walking distance and stairs
        walking_distance = self._calculate_walking_distance(route_info.get("path_details", []))
        stairs_count = self._estimate_stairs(route_info.get("path_details", []))
        
        # Save to database
        db_route = Route(
            search_group_id=search_group_id,
            route_type=RouteType(route_type.value),
            start_location=start_location,
            end_location=end_location,
            transit_info=route_info,
            comfort_score=0,  # Deprecated
            crowding_score=crowding_score,
            walking_distance=walking_distance,
            stairs_count=stairs_count,
            explanation=""  # Will be filled later by LLM
        )
        db.add(db_route)
        db.commit()
        db.refresh(db_route)
        
        # Create response
        transit_info = TransitInfo(**route_info)
        
        return RouteResponse(
            id=db_route.id,
            search_group_id=search_group_id,
            route_type=route_type,
            start_location=start_location,
            end_location=end_location,
            transit_info=transit_info,
            crowding_score=crowding_score,
            walking_distance=walking_distance,
            stairs_count=stairs_count,
            explanation="",  # Will be filled later
            created_at=db_route.created_at
        )
    
    # TODO: 시간부자 경로 자체 예측 모델 개발 예정
    # async def _predict_comfort_route(
    #     self,
    #     start_coords: dict,
    #     end_coords: dict,
    #     fastest_time: int,
    #     all_route_candidates: List[Dict[str, Any]]
    # ) -> Optional[Dict[str, Any]]:
    #     """
    #     자체 예측 모델을 사용하여 시간부자 경로 결정
    #     
    #     Args:
    #         start_coords: 출발지 좌표
    #         end_coords: 도착지 좌표
    #         fastest_time: 최단 경로 소요 시간
    #         all_route_candidates: 모든 경로 후보들
    #         
    #     Returns:
    #         예측 모델이 선택한 최적의 시간부자 경로
    #     """
    #     # TODO: 예측 모델 구현
    #     # - 혼잡도 예측
    #     # - 시간대별 패턴 분석
    #     # - 사용자 선호도 반영
    #     # - 최단 경로 대비 +15분 이내 제약
    #     pass
    
    def _filter_comfort_route_time(
        self,
        routes: List[RouteResponse],
        fastest_time: int
    ) -> List[RouteResponse]:
        """Filter comfort route to meet time constraint (+15 min max)"""
        
        max_time = fastest_time + settings.COMFORT_ROUTE_MAX_TIME_DELTA
        
        filtered = []
        for route in routes:
            if route.route_type == RouteTypeEnum.COMFORT_OPTIMIZED:
                if route.transit_info.total_time <= max_time:
                    filtered.append(route)
            else:
                filtered.append(route)
        
        return filtered
    
    async def _add_explanations(
        self,
        routes: List[RouteResponse],
        fastest_time: Optional[int]
    ) -> List[RouteResponse]:
        """Add LLM-generated explanations to routes"""
        
        for route in routes:
            # Build comparison data
            comparison_data = {}
            if fastest_time is not None:
                comparison_data["fastest_time"] = fastest_time
                comparison_data["time_difference"] = route.transit_info.total_time - fastest_time
            
            # Build route info for LLM
            route_info_dict = {
                "total_time": route.transit_info.total_time,
                "transfer_count": route.transit_info.transfer_count,
                "walking_distance": route.walking_distance,
                "crowding_score": route.crowding_score
            }
            
            # Generate explanation
            explanation = await llm_service.generate_route_explanation(
                route_info=route_info_dict,
                route_type=route.route_type.value,
                comparison_data=comparison_data
            )
            
            route.explanation = explanation
        
        return routes
    
    def _build_comparison_data(self, routes: List[RouteResponse]) -> dict:
        """Build comparison metadata between routes"""
        
        if not routes:
            return {}
        
        comparison = {}
        
        # Find fastest time
        fastest = min(routes, key=lambda r: r.transit_info.total_time)
        comparison["fastest_time"] = fastest.transit_info.total_time
        
        # Find least crowded
        least_crowded = min(routes, key=lambda r: r.crowding_score)
        comparison["least_crowded_score"] = least_crowded.crowding_score
        
        # Find least walking
        least_walking = min(routes, key=lambda r: r.walking_distance)
        comparison["least_walking_distance"] = least_walking.walking_distance
        
        return comparison
    
    def _calculate_walking_distance(self, path_details: List[dict]) -> float:
        """Calculate total walking distance from path details"""
        
        total_walking = 0.0
        for segment in path_details:
            if segment.get("trafficType") == 3:  # Walking segment
                total_walking += segment.get("distance", 0)
        
        return round(total_walking, 2)
    
    def _estimate_stairs(self, path_details: List[dict]) -> int:
        """Estimate number of stairs/transfers"""
        
        # Simple estimation: 1 stair set per transfer + walking segments with elevation
        transfer_count = sum(
            1 for segment in path_details 
            if segment.get("trafficType") in [1, 2]  # Subway or bus
        )
        
        return max(0, transfer_count - 1)  # Transfers usually involve stairs
    
    async def _get_coordinates(self, location: str) -> dict:
        """
        Convert location name to coordinates
        TODO: Implement geocoding or use ODSay station search
        
        Args:
            location: Location name or address
            
        Returns:
            Dictionary with x, y coordinates
        """
        # Placeholder - implement geocoding
        # For now, return dummy coordinates for Seoul
        return {"x": "126.9780", "y": "37.5665"}
    
    def get_route_by_id(self, route_id: int, db: Session) -> Optional[Route]:
        """Get route by ID"""
        return db.query(Route).filter(Route.id == route_id).first()
    
    def get_routes(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 10
    ) -> List[Route]:
        """Get list of routes"""
        return db.query(Route).offset(skip).limit(limit).all()
    
    def save_route(
        self,
        route_id: int,
        name: Optional[str],
        user_id: Optional[str],
        db: Session
    ) -> SavedRoute:
        """Save a route to favorites"""
        saved_route = SavedRoute(
            route_id=route_id,
            name=name,
            user_id=user_id
        )
        db.add(saved_route)
        db.commit()
        db.refresh(saved_route)
        return saved_route
    
    def get_saved_routes(
        self,
        db: Session,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> List[SavedRoute]:
        """Get saved routes, optionally filtered by user"""
        query = db.query(SavedRoute).filter(SavedRoute.is_active == True)
        if user_id:
            query = query.filter(SavedRoute.user_id == user_id)
        return query.offset(skip).limit(limit).all()


# Singleton instance
route_service = RouteService()

