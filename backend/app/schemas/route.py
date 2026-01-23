from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class RouteTypeEnum(str, Enum):
    """Route type enumeration for API"""
    FASTEST = "fastest"
    LEAST_WALKING = "least_walking"
    COMFORT_OPTIMIZED = "comfort_optimized"


class RouteRequest(BaseModel):
    """Request schema for route search"""
    
    start_location: str = Field(..., description="Starting location (address or coordinates)")
    end_location: str = Field(..., description="Destination location (address or coordinates)")
    search_types: Optional[List[RouteTypeEnum]] = Field(
        default=None,
        description="Types of routes to search (defaults to all 3 types)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_location": "서울역",
                "end_location": "강남역",
                "search_types": ["fastest", "least_walking", "comfort_optimized"]
            }
        }


class TransitInfo(BaseModel):
    """Transit information schema"""
    
    total_time: int = Field(..., description="Total travel time in minutes")
    total_distance: float = Field(..., description="Total distance in kilometers")
    fare: int = Field(..., description="Total fare in KRW")
    transfer_count: int = Field(..., description="Number of transfers")
    path_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed path information")


class RouteResponse(BaseModel):
    """Response schema for a single route"""
    
    id: Optional[int] = None
    search_group_id: Optional[str] = None
    route_type: RouteTypeEnum
    
    start_location: str
    end_location: str
    
    transit_info: TransitInfo
    
    # Scores and metrics
    comfort_score: Optional[float] = Field(None, ge=0, le=100, description="Comfort score (deprecated)")
    crowding_score: float = Field(..., ge=0, le=100, description="Crowding score (0-100, lower is better)")
    walking_distance: float = Field(..., description="Total walking distance in meters")
    stairs_count: Optional[int] = Field(None, description="Estimated number of stairs")
    
    # LLM-generated explanation
    explanation: str = Field(..., description="Natural language explanation of why this route is recommended")
    
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "search_group_id": "search_20260121_001",
                "route_type": "comfort_optimized",
                "start_location": "서울역",
                "end_location": "강남역",
                "transit_info": {
                    "total_time": 28,
                    "total_distance": 10.5,
                    "transfer_count": 1,
                    "path_details": {}
                },
                "crowding_score": 35.5,
                "walking_distance": 250.0,
                "stairs_count": 2,
                "explanation": "이 경로는 비교적 여유로운 이동이 가능한 '시간부자 경로'입니다 (최단 경로 대비 +3분). 혼잡도가 낮은 시간대와 구간을 선택하여, 스트레스 없이 편안하게 이동하실 수 있습니다.",
                "created_at": "2026-01-21T14:18:40"
            }
        }


class MultiRouteResponse(BaseModel):
    """Response schema containing all 3 route options"""
    
    search_group_id: str = Field(..., description="Unique identifier for this search")
    routes: List[RouteResponse] = Field(..., description="List of route options (up to 3)")
    
    # Comparison metadata
    comparison: Dict[str, Any] = Field(
        default_factory=dict,
        description="Comparison data between routes"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "search_group_id": "search_20260121_001",
                "routes": [
                    {
                        "route_type": "fastest",
                        "transit_info": {"total_time": 25, "total_distance": 10.5, "fare": 1500, "transfer_count": 1},
                        "crowding_score": 75.0,
                        "walking_distance": 350.0,
                        "explanation": "이 경로는 총 25분으로 가장 빠른 경로입니다."
                    },
                    {
                        "route_type": "least_walking",
                        "transit_info": {"total_time": 30, "total_distance": 11.0, "fare": 1500, "transfer_count": 2},
                        "crowding_score": 60.0,
                        "walking_distance": 150.0,
                        "explanation": "이 경로는 도보 거리가 약 150m로 가장 짧습니다."
                    },
                    {
                        "route_type": "comfort_optimized",
                        "transit_info": {"total_time": 28, "total_distance": 10.8, "fare": 1500, "transfer_count": 1},
                        "crowding_score": 35.5,
                        "walking_distance": 250.0,
                        "explanation": "이 경로는 혼잡도가 낮아 쾌적하게 이동하실 수 있습니다."
                    }
                ],
                "comparison": {
                    "fastest_time": 25,
                    "least_crowded_score": 35.5,
                    "least_walking_distance": 150.0
                }
            }
        }


class CrowdingInfo(BaseModel):
    """Crowding information for a station/route"""
    
    station_name: str
    line_name: str
    crowding_level: int = Field(..., ge=1, le=5, description="Crowding level (1=empty, 5=very crowded)")
    crowding_text: str = Field(..., description="Human-readable crowding description")
    time_period: str = Field(..., description="Time period (morning_peak, evening_peak, off_peak)")
    next_train_crowding: Optional[int] = Field(None, ge=1, le=5, description="Next train crowding level")
    is_realtime: bool = Field(default=False, description="Whether this is real-time data")


class TrainStatusResponse(BaseModel):
    """Real-time train status response"""
    
    train_id: str
    line_name: str
    current_station: Optional[str] = None
    next_station: Optional[str] = None
    direction: Optional[str] = None
    arrival_minutes: Optional[int] = Field(None, description="Minutes until arrival")
    delay_minutes: int = Field(default=0, description="Delay in minutes")
    crowding_level: Optional[int] = Field(None, ge=1, le=5, description="Current crowding level")
    crowding_text: Optional[str] = None
    train_type: Optional[str] = Field(None, description="Train type (일반, 급행)")
    updated_at: datetime


class SavedRouteRequest(BaseModel):
    """Request schema for saving a route"""
    
    route_id: int
    name: Optional[str] = None
    user_id: Optional[str] = None


class SavedRouteResponse(BaseModel):
    """Response schema for saved route"""
    
    id: int
    route_id: int
    name: Optional[str]
    saved_at: datetime
    
    class Config:
        from_attributes = True


class ComfortExplainRequest(BaseModel):
    """Request schema for comfort route explanation"""
    
    path: Dict[str, Any] = Field(..., description="Path information")
    crowdingSummary: Dict[str, Any] = Field(..., description="Crowding summary data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "path": {
                    "total_time": 28,
                    "transfer_count": 1
                },
                "crowdingSummary": {
                    "average_crowding": 35.5,
                    "peak_sections": []
                }
            }
        }


class ComfortExplainResponse(BaseModel):
    """Response schema for comfort route explanation"""
    
    sentence: str = Field(..., description="Generated explanation sentence")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sentence": "이 경로는 혼잡도가 낮은 시간대와 구간을 선택한 '시간부자 경로'입니다."
            }
        }


class FavoriteRequest(BaseModel):
    """Request schema for saving favorite route"""
    
    deviceId: str = Field(..., description="Device identifier")
    from_station: str = Field(..., description="Starting station")
    to_station: str = Field(..., description="Destination station")
    type: str = Field(..., description="Route type (fastest, least_walking, comfort_optimized)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "deviceId": "device123",
                "from_station": "서울역",
                "to_station": "강남역",
                "type": "comfort_optimized"
            }
        }


class FavoriteResponse(BaseModel):
    """Response schema for favorite route"""
    
    id: int = Field(..., description="Favorite ID")
    deviceId: str = Field(..., description="Device identifier")
    from_station: str = Field(..., description="Starting station")
    to_station: str = Field(..., description="Destination station")
    type: str = Field(..., description="Route type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "deviceId": "device123",
                "from_station": "서울역",
                "to_station": "강남역",
                "type": "comfort_optimized"
            }
        }

