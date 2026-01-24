"""
혼잡도 서비스
"""
from datetime import datetime
from app.schemas.route import CongestionLevel


class CongestionService:
    """혼잡도 서비스"""
    
    def __init__(self):
        # TODO: 실제 혼잡도 데이터 소스 연동
        pass
    
    def get_congestion_score(
        self,
        station_id: str,
        line_number: str,
        time: datetime
    ) -> float:
        """
        특정 역/호선의 혼잡도 점수 반환 (0-1, 낮을수록 덜 혼잡)
        """
        # TODO: 실제 혼잡도 데이터 조회 로직 구현
        # 현재는 더미 데이터 반환
        hour = time.hour
        # 퇴근 시간대 (17-19시)는 높은 혼잡도
        if 17 <= hour <= 19:
            return 0.8
        else:
            return 0.4
    
    def get_congestion_level(self, score: float) -> CongestionLevel:
        """혼잡도 점수를 레벨로 변환"""
        if score < 0.4:
            return CongestionLevel.SPACIOUS
        elif score < 0.7:
            return CongestionLevel.NORMAL
        else:
            return CongestionLevel.CROWDED
