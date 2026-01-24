from typing import Dict, Any, Optional
from app.core.config import settings


class LLMService:
    """Service for generating LLM-based route explanations"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        
    async def generate_route_explanation(
        self,
        route_info: Dict[str, Any],
        route_type: str,
        comparison_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate natural language explanation for route recommendation
        
        Args:
            route_info: Route information dictionary
            route_type: Type of route (fastest, least_walking, comfort_optimized)
            comparison_data: Optional data comparing this route to others
            
        Returns:
            Natural language explanation in Korean
        """
        if self.provider == "mock":
            return self._generate_mock_explanation(route_info, route_type, comparison_data)
        elif self.provider == "openai":
            return await self._generate_openai_explanation(route_info, route_type, comparison_data)
        elif self.provider == "gemini":
            return await self._generate_gemini_explanation(route_info, route_type, comparison_data)
        else:
            return "경로 설명을 생성할 수 없습니다."
    
    def _generate_mock_explanation(
        self,
        route_info: Dict[str, Any],
        route_type: str,
        comparison_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate mock explanation for testing"""
        
        total_time = route_info.get("total_time", 0)
        transfer_count = route_info.get("transfer_count", 0)
        walking_distance = route_info.get("walking_distance", 0)
        crowding_score = route_info.get("crowding_score", 50)
        
        if route_type == "fastest":
            return (
                f"이 경로는 총 {total_time}분으로 가장 빠른 경로입니다. "
                f"환승 {transfer_count}회가 필요하지만, 최단 시간으로 목적지에 도착할 수 있습니다."
            )
        elif route_type == "least_walking":
            return (
                f"이 경로는 도보 거리가 약 {int(walking_distance)}m로 가장 짧습니다. "
                f"계단이나 에스컬레이터 이동이 적어 편안하게 이동하실 수 있습니다."
            )
        elif route_type == "comfort_optimized":
            time_diff = ""
            if comparison_data and "fastest_time" in comparison_data:
                diff = total_time - comparison_data["fastest_time"]
                time_diff = f" (최단 경로 대비 +{diff}분)"
            
            crowding_text = "비교적 여유로운" if crowding_score < 50 else "쾌적한"
            
            return (
                f"이 경로는 {crowding_text} 이동이 가능한 '시간부자 경로'입니다{time_diff}. "
                f"혼잡도가 낮은 시간대와 구간을 선택하여, "
                f"스트레스 없이 편안하게 이동하실 수 있습니다. "
                f"특히 퇴근 시간대에 B구간의 혼잡도가 낮아 체감 쾌적도가 높습니다."
            )
        
        return "이 경로를 추천합니다."
    
    async def _generate_openai_explanation(
        self,
        route_info: Dict[str, Any],
        route_type: str,
        comparison_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate explanation using OpenAI API"""
        try:
            import httpx
            import json
            
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                return self._generate_mock_explanation(route_info, route_type, comparison_data)
            
            # Create prompt
            prompt = self._create_explanation_prompt(route_info, route_type, comparison_data)
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "당신은 대중교통 경로 추천 전문가입니다. 사용자에게 친근하고 이해하기 쉬운 한국어로 경로를 설명해주세요."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
                
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            return self._generate_mock_explanation(route_info, route_type, comparison_data)
    
    async def _generate_gemini_explanation(
        self,
        route_info: Dict[str, Any],
        route_type: str,
        comparison_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate explanation using Google Gemini API"""
        try:
            import httpx
            
            api_key = settings.GEMINI_API_KEY
            if not api_key:
                return self._generate_mock_explanation(route_info, route_type, comparison_data)
            
            prompt = self._create_explanation_prompt(route_info, route_type, comparison_data)
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"당신은 대중교통 경로 추천 전문가입니다. 다음 경로를 친근하고 이해하기 쉬운 한국어로 설명해주세요:\n\n{prompt}"
                    }]
                }]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                result = response.json()
                return result["candidates"][0]["content"]["parts"][0]["text"].strip()
                
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return self._generate_mock_explanation(route_info, route_type, comparison_data)
    
    def _create_explanation_prompt(
        self,
        route_info: Dict[str, Any],
        route_type: str,
        comparison_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create prompt for LLM"""
        
        prompt = f"""경로 정보:
- 경로 타입: {route_type}
- 총 소요 시간: {route_info.get('total_time', 0)}분
- 환승 횟수: {route_info.get('transfer_count', 0)}회
- 도보 거리: {route_info.get('walking_distance', 0)}m
- 혼잡도 점수: {route_info.get('crowding_score', 50)}/100 (낮을수록 좋음)
"""
        
        if comparison_data:
            prompt += f"\n다른 경로와 비교:\n"
            for key, value in comparison_data.items():
                prompt += f"- {key}: {value}\n"
        
        prompt += "\n이 경로를 2-3문장으로 설명해주세요. 왜 이 경로가 추천되는지, 어떤 장점이 있는지 구체적으로 알려주세요."
        
        return prompt
    
    async def generate_comfort_explanation(
        self,
        path: dict,
        crowding_summary: dict
    ) -> str:
        """
        Generate explanation for comfort route based on path and crowding data
        
        Args:
            path: Path information dictionary
            crowding_summary: Crowding summary dictionary
            
        Returns:
            Natural language explanation in Korean
        """
        if self.provider == "mock":
            return self._generate_mock_comfort_explanation(path, crowding_summary)
        elif self.provider == "openai":
            return await self._generate_openai_comfort_explanation(path, crowding_summary)
        elif self.provider == "gemini":
            return await self._generate_gemini_comfort_explanation(path, crowding_summary)
        else:
            return "시간부자 경로 설명을 생성할 수 없습니다."
    
    def _generate_mock_comfort_explanation(
        self,
        path: dict,
        crowding_summary: dict
    ) -> str:
        """Generate mock comfort explanation"""
        return (
            "이 경로는 혼잡도가 낮은 시간대와 구간을 선택한 '시간부자 경로'입니다. "
            "비교적 여유로운 이동이 가능하여 스트레스 없이 편안하게 목적지에 도착하실 수 있습니다."
        )
    
    async def _generate_openai_comfort_explanation(
        self,
        path: dict,
        crowding_summary: dict
    ) -> str:
        """Generate comfort explanation using OpenAI"""
        try:
            import httpx
            
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                return self._generate_mock_comfort_explanation(path, crowding_summary)
            
            prompt = f"""다음 경로 정보를 바탕으로 '시간부자 경로'에 대한 설명을 생성해주세요:

경로 정보:
{path}

혼잡도 요약:
{crowding_summary}

2-3문장으로 친근하고 이해하기 쉬운 한국어로 설명해주세요."""
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "당신은 대중교통 경로 추천 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
                
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            return self._generate_mock_comfort_explanation(path, crowding_summary)
    
    async def _generate_gemini_comfort_explanation(
        self,
        path: dict,
        crowding_summary: dict
    ) -> str:
        """Generate comfort explanation using Gemini"""
        try:
            import httpx
            
            api_key = settings.GEMINI_API_KEY
            if not api_key:
                return self._generate_mock_comfort_explanation(path, crowding_summary)
            
            prompt = f"""다음 경로 정보를 바탕으로 '시간부자 경로'에 대한 설명을 생성해주세요:

경로 정보:
{path}

혼잡도 요약:
{crowding_summary}

2-3문장으로 친근하고 이해하기 쉬운 한국어로 설명해주세요."""
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                result = response.json()
                return result["candidates"][0]["content"]["parts"][0]["text"].strip()
                
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return self._generate_mock_comfort_explanation(path, crowding_summary)


# Singleton instance
llm_service = LLMService()
