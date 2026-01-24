from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
from app.core.config import settings


class RealtimeService:
    """Service for real-time train tracking and crowding data"""
    
    def __init__(self):
        self.use_mock_data = settings.USE_MOCK_REALTIME_DATA
        
    async def get_train_position(
        self,
        line_name: str,
        station_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get real-time train positions for a line
        
        Args:
            line_name: Name of the subway/train line
            station_name: Optional station name filter
            
        Returns:
            List of train position data
        """
        if self.use_mock_data:
            return self._generate_mock_train_positions(line_name, station_name)
        else:
            # TODO: Implement real API integration
            return await self._fetch_real_train_positions(line_name, station_name)
    
    async def get_crowding_data(
        self,
        station_name: str,
        line_name: str,
        time_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get crowding data for a specific station and line
        
        Args:
            station_name: Station name
            line_name: Line name
            time_period: Optional time period filter
            
        Returns:
            Crowding data dictionary
        """
        if self.use_mock_data:
            return self._generate_mock_crowding_data(station_name, line_name, time_period)
        else:
            # TODO: Implement real API integration
            return await self._fetch_real_crowding_data(station_name, line_name, time_period)
    
    async def get_next_train_info(
        self,
        station_name: str,
        line_name: str,
        direction: str
    ) -> Dict[str, Any]:
        """
        Get information about the next arriving train
        
        Args:
            station_name: Current station name
            line_name: Line name
            direction: Direction (e.g., "상행", "하행")
            
        Returns:
            Next train information including crowding level
        """
        if self.use_mock_data:
            return self._generate_mock_next_train(station_name, line_name, direction)
        else:
            # TODO: Implement real API integration
            return await self._fetch_real_next_train(station_name, line_name, direction)
    
    def _generate_mock_train_positions(
        self,
        line_name: str,
        station_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate mock train position data for testing"""
        
        # Mock stations for testing
        stations = ["강남역", "역삼역", "선릉역", "삼성역", "종합운동장역"]
        
        trains = []
        for i in range(3):
            current_idx = random.randint(0, len(stations) - 2)
            trains.append({
                "train_id": f"{line_name}-{i+1:03d}",
                "line_name": line_name,
                "current_station": stations[current_idx],
                "next_station": stations[current_idx + 1],
                "direction": "상행" if i % 2 == 0 else "하행",
                "delay_minutes": random.randint(0, 3),
                "crowding_level": random.randint(2, 5),
                "train_type": "일반",
                "updated_at": datetime.now().isoformat()
            })
        
        return trains
    
    def _generate_mock_crowding_data(
        self,
        station_name: str,
        line_name: str,
        time_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate mock crowding data"""
        
        # Determine time period if not provided
        if not time_period:
            current_hour = datetime.now().hour
            if 7 <= current_hour <= 9:
                time_period = "morning_peak"
            elif 18 <= current_hour <= 20:
                time_period = "evening_peak"
            else:
                time_period = "off_peak"
        
        # Higher crowding during peak hours
        base_crowding = {
            "morning_peak": 4,
            "evening_peak": 5,
            "off_peak": 2
        }.get(time_period, 3)
        
        crowding_level = base_crowding + random.randint(-1, 1)
        crowding_level = max(1, min(5, crowding_level))  # Clamp to 1-5
        
        return {
            "station_name": station_name,
            "line_name": line_name,
            "time_period": time_period,
            "crowding_level": crowding_level,
            "passenger_count": crowding_level * 200,  # Rough estimate
            "is_realtime": False,
            "source": "mock",
            "recorded_at": datetime.now().isoformat(),
            "trend": self._get_crowding_trend(crowding_level),
            "next_train_crowding": max(1, min(5, crowding_level + random.randint(-1, 1)))
        }
    
    def _generate_mock_next_train(
        self,
        station_name: str,
        line_name: str,
        direction: str
    ) -> Dict[str, Any]:
        """Generate mock next train information"""
        
        arrival_minutes = random.randint(1, 8)
        crowding_level = random.randint(2, 5)
        
        return {
            "station_name": station_name,
            "line_name": line_name,
            "direction": direction,
            "arrival_minutes": arrival_minutes,
            "crowding_level": crowding_level,
            "crowding_text": self._get_crowding_text(crowding_level),
            "train_type": "일반",
            "next_next_train_minutes": arrival_minutes + random.randint(4, 8),
            "updated_at": datetime.now().isoformat()
        }
    
    def _get_crowding_trend(self, current_level: int) -> str:
        """Get crowding trend description"""
        if current_level <= 2:
            return "여유로움"
        elif current_level <= 3:
            return "보통"
        elif current_level <= 4:
            return "혼잡"
        else:
            return "매우 혼잡"
    
    def _get_crowding_text(self, level: int) -> str:
        """Convert crowding level to Korean text"""
        crowding_map = {
            1: "여유",
            2: "보통",
            3: "약간 혼잡",
            4: "혼잡",
            5: "매우 혼잡"
        }
        return crowding_map.get(level, "알 수 없음")
    
    async def _fetch_real_train_positions(
        self,
        line_name: str,
        station_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch real train positions from API (TODO: implement)"""
        # Placeholder for real API integration
        import httpx
        
        api_key = settings.REALTIME_TRANSIT_API_KEY
        if not api_key:
            return self._generate_mock_train_positions(line_name, station_name)
        
        # TODO: Implement actual API call
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(...)
        #     return response.json()
        
        return self._generate_mock_train_positions(line_name, station_name)
    
    async def _fetch_real_crowding_data(
        self,
        station_name: str,
        line_name: str,
        time_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch real crowding data from API (TODO: implement)"""
        # Placeholder for real API integration
        return self._generate_mock_crowding_data(station_name, line_name, time_period)
    
    async def _fetch_real_next_train(
        self,
        station_name: str,
        line_name: str,
        direction: str
    ) -> Dict[str, Any]:
        """Fetch real next train info from API (TODO: implement)"""
        # Placeholder for real API integration
        return self._generate_mock_next_train(station_name, line_name, direction)
    
    def calculate_route_crowding_score(
        self,
        path_details: List[Dict[str, Any]],
        time_period: Optional[str] = None
    ) -> float:
        """
        Calculate overall crowding score for a route
        
        Args:
            path_details: List of route segments
            time_period: Time period for the journey
            
        Returns:
            Crowding score (0-100, lower is better)
        """
        if not path_details:
            return 50.0  # Default moderate score
        
        total_crowding = 0
        segment_count = 0
        
        for segment in path_details:
            # Only score transit segments (not walking)
            if segment.get("trafficType") in [1, 2]:  # Subway or bus
                station = segment.get("startName", "")
                line = segment.get("lane", [{}])[0].get("name", "") if segment.get("lane") else ""
                
                if station and line:
                    crowding_data = self._generate_mock_crowding_data(station, line, time_period)
                    # Convert 1-5 scale to 0-100 scale
                    crowding_score = (crowding_data["crowding_level"] - 1) * 25
                    total_crowding += crowding_score
                    segment_count += 1
        
        if segment_count == 0:
            return 50.0
        
        return round(total_crowding / segment_count, 2)


# Singleton instance
realtime_service = RealtimeService()
