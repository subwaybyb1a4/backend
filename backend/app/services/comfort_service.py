from typing import Dict, Any, List


class ComfortService:
    """Service for calculating route comfort scores"""
    
    # Weights for different comfort factors
    WEIGHTS = {
        "transfer_count": 0.3,      # Less transfers = more comfortable
        "walking_distance": 0.25,   # Less walking = more comfortable
        "travel_time": 0.2,         # Shorter time = more comfortable
        "congestion": 0.15,         # Less crowded = more comfortable
        "route_complexity": 0.1     # Simpler route = more comfortable
    }
    
    def calculate_comfort_score(self, route_info: Dict[str, Any]) -> float:
        """
        Calculate comfort score for a route
        
        Args:
            route_info: Route information from ODSay service
            
        Returns:
            Comfort score (0-100)
        """
        scores = {
            "transfer": self._score_transfers(route_info.get("transfer_count", 0)),
            "walking": self._score_walking(route_info.get("path_details", [])),
            "time": self._score_time(route_info.get("total_time", 0)),
            "congestion": self._score_congestion(route_info.get("path_details", [])),
            "complexity": self._score_complexity(route_info.get("path_details", []))
        }
        
        # Calculate weighted average
        comfort_score = (
            scores["transfer"] * self.WEIGHTS["transfer_count"] +
            scores["walking"] * self.WEIGHTS["walking_distance"] +
            scores["time"] * self.WEIGHTS["travel_time"] +
            scores["congestion"] * self.WEIGHTS["congestion"] +
            scores["complexity"] * self.WEIGHTS["route_complexity"]
        )
        
        return round(comfort_score, 2)
    
    def _score_transfers(self, transfer_count: int) -> float:
        """Score based on number of transfers (0 transfers = 100, decreases with more)"""
        if transfer_count == 0:
            return 100.0
        elif transfer_count == 1:
            return 85.0
        elif transfer_count == 2:
            return 65.0
        elif transfer_count == 3:
            return 45.0
        else:
            return max(20.0, 100 - (transfer_count * 20))
    
    def _score_walking(self, path_details: List[Dict[str, Any]]) -> float:
        """Score based on walking distance"""
        total_walking = 0
        
        for segment in path_details:
            if segment.get("trafficType") == 3:  # Walking segment
                total_walking += segment.get("distance", 0)
        
        # Convert to meters
        walking_meters = total_walking
        
        # Score: 0-200m = 100, 200-500m = 80, 500-1000m = 60, 1000+ = 40
        if walking_meters <= 200:
            return 100.0
        elif walking_meters <= 500:
            return 80.0
        elif walking_meters <= 1000:
            return 60.0
        else:
            return max(20.0, 100 - (walking_meters / 50))
    
    def _score_time(self, total_time: int) -> float:
        """Score based on total travel time"""
        # Score: 0-20min = 100, 20-40min = 80, 40-60min = 60, 60+ = 40
        if total_time <= 20:
            return 100.0
        elif total_time <= 40:
            return 80.0
        elif total_time <= 60:
            return 60.0
        else:
            return max(20.0, 100 - (total_time / 2))
    
    def _score_congestion(self, path_details: List[Dict[str, Any]]) -> float:
        """
        Score based on estimated congestion
        (This is a placeholder - would need real-time congestion data)
        """
        # TODO: Integrate with real-time congestion API
        # For now, return a moderate score
        return 70.0
    
    def _score_complexity(self, path_details: List[Dict[str, Any]]) -> float:
        """Score based on route complexity (number of segments, mode changes)"""
        segment_count = len(path_details)
        
        # Fewer segments = simpler route = higher score
        if segment_count <= 3:
            return 100.0
        elif segment_count <= 5:
            return 80.0
        elif segment_count <= 7:
            return 60.0
        else:
            return max(20.0, 100 - (segment_count * 10))
    
    def get_comfort_recommendations(self, comfort_score: float) -> List[str]:
        """
        Get recommendations based on comfort score
        
        Args:
            comfort_score: The calculated comfort score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if comfort_score >= 80:
            recommendations.append("이 경로는 매우 쾌적합니다! 👍")
        elif comfort_score >= 60:
            recommendations.append("괜찮은 경로입니다.")
        else:
            recommendations.append("더 쾌적한 경로를 찾아볼까요?")
            recommendations.append("다른 시간대를 고려해보세요.")
        
        return recommendations


# Singleton instance
comfort_service = ComfortService()
