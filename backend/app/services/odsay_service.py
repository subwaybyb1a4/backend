import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings


class ODSayService:
    """Service for interacting with ODSay API (Korean public transit API)"""
    
    BASE_URL = "https://api.odsay.com/v1/api"
    
    def __init__(self):
        self.api_key = settings.ODSAY_API_KEY
        
    async def search_pub_trans_path(
        self,
        start_x: str,
        start_y: str,
        end_x: str,
        end_y: str,
        search_type: int = 0
    ) -> Dict[str, Any]:
        """
        Search public transportation routes
        
        Args:
            start_x: Starting point longitude
            start_y: Starting point latitude
            end_x: Destination longitude
            end_y: Destination latitude
            search_type: 0(최적), 1(최소시간), 2(최소환승), 3(최소도보), 4(최저요금)
            
        Returns:
            Route information from ODSay API
        """
        url = f"{self.BASE_URL}/searchPubTransPathT"
        
        params = {
            "SX": start_x,
            "SY": start_y,
            "EX": end_x,
            "EY": end_y,
            "SearchType": search_type,
            "apiKey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise Exception(f"ODSay API request failed: {str(e)}")
    
    async def search_station(self, station_name: str) -> Dict[str, Any]:
        """
        Search for station information by name
        
        Args:
            station_name: Name of the station
            
        Returns:
            Station information
        """
        url = f"{self.BASE_URL}/searchStation"
        
        params = {
            "stationName": station_name,
            "apiKey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise Exception(f"Station search failed: {str(e)}")
    
    def parse_route_info(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse ODSay API response into structured route information
        Returns only the first (optimal) path
        
        Args:
            raw_data: Raw response from ODSay API
            
        Returns:
            Parsed route information for the first path
        """
        try:
            result = raw_data.get("result", {})
            path = result.get("path", [])
            
            if not path:
                return {}
            
            # Get the first (optimal) path
            optimal_path = path[0]
            info = optimal_path.get("info", {})
            
            return {
                "total_time": info.get("totalTime", 0),
                "total_distance": info.get("totalDistance", 0) / 1000,  # Convert to km
                "fare": info.get("payment", 0),
                "transfer_count": info.get("busTransitCount", 0) + info.get("subwayTransitCount", 0),
                "path_details": optimal_path.get("subPath", [])
            }
        except Exception as e:
            raise Exception(f"Failed to parse route info: {str(e)}")
    
    def parse_all_routes(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse ODSay API response and return all available route options
        
        Args:
            raw_data: Raw response from ODSay API
            
        Returns:
            List of parsed route information for all paths
        """
        try:
            result = raw_data.get("result", {})
            paths = result.get("path", [])
            
            if not paths:
                return []
            
            parsed_routes = []
            for path in paths:
                info = path.get("info", {})
                parsed_routes.append({
                    "total_time": info.get("totalTime", 0),
                    "total_distance": info.get("totalDistance", 0) / 1000,  # Convert to km
                    "fare": info.get("payment", 0),
                    "transfer_count": info.get("busTransitCount", 0) + info.get("subwayTransitCount", 0),
                    "path_details": path.get("subPath", [])
                })
            
            return parsed_routes
        except Exception as e:
            raise Exception(f"Failed to parse all routes: {str(e)}")


# Singleton instance
odsay_service = ODSayService()
