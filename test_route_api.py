"""
Route Congestion API 테스트 스크립트 (혼잡 RAG 검증용)
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_check():
    print("=" * 50)
    print("🔍 헬스 체크 테스트")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"상태 코드: {response.status_code}")
    print(f"응답: {json.dumps(response.json(), ensure_ascii=False, indent=2)}\n")


def test_analyze_single_route():
    """
    🔥 신도림 환승 피크 테스트 (07:55, 매우 혼잡 케이스)
    """
    print("=" * 50)
    print("📍 단일 경로 분석 테스트 - 신도림 환승 피크")
    print("=" * 50)
    
    request_data = {
        "route": {
            "route_id": "route_peak_sindorim",
            "total_time": 42.0,
            "segments": [
                {
                    "line": "1호선",
                    "station": "신도림역",
                    "direction": "상행",
                    "time_str": "07:55",
                    "travel_time": 10.0,
                    "is_transfer": False
                },
                {
                    "line": "2호선",
                    "station": "신도림역",
                    "direction": "하행",
                    "time_str": "08:00",
                    "travel_time": 5.0,
                    "is_transfer": True
                },
                {
                    "line": "2호선",
                    "station": "강남역",
                    "direction": "하행",
                    "time_str": "08:20",
                    "travel_time": 27.0,
                    "is_transfer": False
                }
            ]
        },
        "day": "평일",
        "time_str": "07:55"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/routes/analyze",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"상태 코드: {response.status_code}")
    print(f"응답:\n{json.dumps(response.json(), ensure_ascii=False, indent=2)}\n")


def test_analyze_batch_routes():
    """
    📊 배치 테스트 - 혼잡/보통/매우혼잡 비교
    """
    print("=" * 50)
    print("📊 배치 경로 분석 테스트 - 혼잡 RAG 검증")
    print("=" * 50)
    
    request_data = [
        # 🔥 고속터미널 환승 매우 혼잡
        {
            "route": {
                "route_id": "route_terminal_peak",
                "total_time": 38.0,
                "segments": [
                    {
                        "line": "3호선",
                        "station": "고속터미널역",
                        "direction": "상행",
                        "time_str": "08:15",
                        "travel_time": 8.0,
                        "is_transfer": False
                    },
                    {
                        "line": "7호선",
                        "station": "고속터미널역",
                        "direction": "하행",
                        "time_str": "08:20",
                        "travel_time": 6.0,
                        "is_transfer": True
                    },
                    {
                        "line": "7호선",
                        "station": "논현역",
                        "direction": "하행",
                        "time_str": "08:30",
                        "travel_time": 24.0,
                        "is_transfer": False
                    }
                ]
            },
            "day": "평일"
        },

        # 🟡 강남 하차 보통 케이스
        {
            "route": {
                "route_id": "route_gangnam_normal",
                "total_time": 30.0,
                "segments": [
                    {
                        "line": "2호선",
                        "station": "강남역",
                        "direction": "상행",
                        "time_str": "08:20",
                        "travel_time": 30.0,
                        "is_transfer": False
                    }
                ]
            },
            "day": "평일"
        },

        # 🔥 가산디지털단지 출근 폭주 케이스
        {
            "route": {
                "route_id": "route_gasan_peak",
                "total_time": 45.0,
                "segments": [
                    {
                        "line": "1호선",
                        "station": "가산디지털단지역",
                        "direction": "상행",
                        "time_str": "08:40",
                        "travel_time": 15.0,
                        "is_transfer": False
                    },
                    {
                        "line": "7호선",
                        "station": "가산디지털단지역",
                        "direction": "하행",
                        "time_str": "08:45",
                        "travel_time": 5.0,
                        "is_transfer": True
                    },
                    {
                        "line": "7호선",
                        "station": "철산역",
                        "direction": "하행",
                        "time_str": "08:55",
                        "travel_time": 25.0,
                        "is_transfer": False
                    }
                ]
            },
            "day": "평일"
        }
    ]
    
    response = requests.post(
        f"{BASE_URL}/api/routes/analyze-batch",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"상태 코드: {response.status_code}")
    result = response.json()
    
    print(f"\n총 분석된 경로: {result['total_routes']}")
    print(f"추천 경로: {result['recommendation']}")
    
    print(f"\n상세 결과:")
    for route in result['routes']:
        print(f"\n  🚇 {route['route_id']}")
        print(f"    - 총 소요시간: {route['total_time']}분")
        print(f"    - 혼잡도 점수: {route['congestion_score']}")
        print(f"    - 혼잡도 레벨: {route['congestion_level']}")
        print(f"    - 환승 횟수: {route['num_transfers']}")
        print(f"    - LLM 설명: {route['llm_description']}")
    print()


if __name__ == "__main__":
    print("\n🚀 Route Congestion API 혼잡 RAG 테스트 시작\n")
    
    # 서버 연결 확인
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ API 서버 연결 성공\n")
    except Exception as e:
        print(f"❌ API 서버에 연결할 수 없습니다: {e}")
        print("먼저 `python route_api.py`로 서버를 시작하세요.\n")
        exit(1)
    
    # 테스트 실행
    test_health_check()
    test_analyze_single_route()
    test_analyze_batch_routes()
    
    print("\n✅ 혼잡 RAG 테스트 완료!\n")
