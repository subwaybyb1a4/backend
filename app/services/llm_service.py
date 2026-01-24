"""
LLM 서비스 (Azure OpenAI를 사용한 편안함 설명 생성)
"""
from typing import Optional, Dict, Any, List
from app.core.config import settings
from openai import AzureOpenAI
import json


class LLMService:
    """Azure OpenAI LLM 서비스"""
    
    def __init__(self):
        """
        Azure OpenAI 클라이언트 초기화
        """
        if not settings.AZURE_OPENAI_API_KEY:
            self.client = None
            print("경고: Azure OpenAI API 키가 설정되지 않았습니다.")
        else:
            self.client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
    
    async def generate_comfort_explanation(
        self,
        route_info: Dict[str, Any],
        congestion_data: Dict[str, Any],
        fastest_duration: int,
        comfort_duration: int
    ) -> str:
        """
        편안함 근거 설명 생성 (Azure OpenAI 사용)
        
        Args:
            route_info: 경로 정보 (segments, transfers 등)
            congestion_data: 혼잡도 데이터
            fastest_duration: 최단 경로 소요 시간 (초)
            comfort_duration: 시간부자 경로 소요 시간 (초)
        
        Returns:
            편안함 근거 설명
        """
        if not self.client:
            # API 키가 없으면 기본 설명 반환
            time_diff = (comfort_duration - fastest_duration) // 60
            return f"이 경로는 최단 경로 대비 {time_diff}분 추가 소요되지만, 혼잡도가 낮아 편안하게 이동할 수 있습니다."
        
        try:
            # 프롬프트 구성
            time_diff_minutes = (comfort_duration - fastest_duration) // 60
            avg_congestion = congestion_data.get("avg_congestion", 0.5)
            congestion_level = congestion_data.get("congestion_level", "보통")
            
            # 경로 구간 정보 요약
            segments_summary = []
            for segment in route_info.get("segments", []):
                segments_summary.append({
                    "from": segment.get("from_station", {}).get("station_name", ""),
                    "to": segment.get("to_station", {}).get("station_name", ""),
                    "line": segment.get("line_number", ""),
                    "duration_minutes": segment.get("duration", 0) // 60,
                    "congestion": segment.get("congestion_level", "보통")
                })
            
            # 환승 정보
            transfers_count = len(route_info.get("transfers", []))
            
            prompt = f"""당신은 지하철 경로 추천 서비스의 설명 생성 AI입니다. 
사용자에게 시간부자 전용 경로의 편안함을 친근하고 이해하기 쉽게 설명해주세요.

경로 정보:
- 최단 경로 소요 시간: {fastest_duration // 60}분
- 시간부자 경로 소요 시간: {comfort_duration // 60}분
- 추가 소요 시간: {time_diff_minutes}분
- 평균 혼잡도: {congestion_level} (점수: {avg_congestion:.2f})
- 경로 구간: {len(segments_summary)}개
- 환승 횟수: {transfers_count}회

요구사항:
1. 한 문장으로 간결하게 설명
2. 친근하고 자연스러운 톤
3. 혼잡도와 시간 차이를 명확히 언급
4. 사용자가 이 경로를 선택할 이유를 강조

예시 스타일:
- "이 경로는 평균 혼잡도가 낮아 여유롭게 이동할 수 있습니다. 최단 경로보다 {time_diff_minutes}분 정도 더 소요되지만, 체감 스트레스가 적습니다."
- "주요 구간의 혼잡도가 낮아 상대적으로 편안하게 이동할 수 있습니다. 최단 경로 대비 {time_diff_minutes}분 추가 소요됩니다."

설명을 생성해주세요:"""

            # Azure OpenAI API 호출
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 지하철 경로 추천 서비스의 설명 생성 전문가입니다. 사용자에게 친근하고 이해하기 쉬운 한 문장 설명을 제공합니다."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            explanation = response.choices[0].message.content.strip()
            return explanation
        
        except Exception as e:
            # API 호출 실패 시 기본 설명 반환
            print(f"Azure OpenAI API 호출 실패: {str(e)}")
            time_diff = (comfort_duration - fastest_duration) // 60
            avg_congestion = congestion_data.get("avg_congestion", 0.5)
            
            if avg_congestion < 0.4:
                return f"이 경로는 평균 혼잡도가 낮아 여유롭게 이동할 수 있습니다. 최단 경로보다 {time_diff}분 정도 더 소요되지만, 체감 스트레스가 적습니다."
            elif avg_congestion < 0.6:
                return f"이 경로는 주요 구간의 혼잡도가 낮아 상대적으로 편안하게 이동할 수 있습니다. 최단 경로 대비 {time_diff}분 추가 소요됩니다."
            else:
                return f"이 경로는 최단 경로 대비 {time_diff}분 추가 소요되지만, 일부 구간에서 혼잡도를 피할 수 있습니다."
