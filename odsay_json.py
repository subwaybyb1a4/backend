# =========================
# 시작역->도착역 경로 json 형식으로 받을 수 있는 코드
# =========================
 
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
import json

# =========================
# 0. env 로드
# =========================
env_path = Path(r"C:/Users/JWHEO/Desktop/backend/.env")
load_dotenv(env_path)
api_key = os.getenv("API_KEY")
if not api_key:
    raise Exception("❌ API_KEY를 불러오지 못했습니다. .env 파일 확인!")

# =========================
# 1. 사용자 입력
# =========================
start_station = input("출발역: ").replace("역", "")
end_station = input("도착역: ").replace("역", "")

# =========================
# 2. 역 이름 → 좌표 변환
# =========================
def get_coord(station):
    url = "https://api.odsay.com/v1/api/searchStation"
    res = requests.get(url, params={"apiKey": api_key, "stationName": station}).json()
    if "result" not in res or not res["result"]["station"]:
        raise Exception(f"❌ '{station}' 역을 찾을 수 없습니다.")
    s = res["result"]["station"][0]
    return float(s["x"]), float(s["y"])

startX, startY = get_coord(start_station)
endX, endY = get_coord(end_station)

# =========================
# 3. 지하철 경로 조회
# =========================
url = "https://api.odsay.com/v1/api/searchPubTransPathT"
params = {
    "apiKey": api_key,
    "SX": startX,
    "SY": startY,
    "EX": endX,
    "EY": endY,
    "OPT": 1
}
res = requests.get(url, params=params).json()
paths = res.get("result", {}).get("path", [])

if not paths:
    raise Exception("❌ 경로를 찾을 수 없습니다.")

# =========================
# 4. 버스 포함된 경로 삭제
# =========================
clean_paths = []

for path in paths:
    has_bus = any(sub.get("trafficType") == 2 for sub in path.get("subPath", []))
    if has_bus:
        continue  # 버스 포함 경로는 무시
    # 지하철(1)과 도보(3)만 남기기
    sub_paths = [sub for sub in path.get("subPath", []) if sub.get("trafficType") in [1, 3]]
    if sub_paths:  # 남은 구간이 있으면
        path["subPath"] = sub_paths
        clean_paths.append(path)

paths = clean_paths

if not paths:
    raise Exception("❌ 버스 없는 지하철/도보 경로가 없습니다.")

# =========================
# 5. JSON 구조 생성
# =========================
json_paths = []

for idx, path in enumerate(paths, 1):
    info = path.get("info", {})
    path_json = {
        "경로번호": idx,
        "총소요시간": info.get("totalTime"),
        "환승횟수": info.get("subwayTransitCount"),
        "도보시간": info.get("totalWalkTime"),
        "출발역": info.get("startName") or start_station,
        "도착역": info.get("endName") or end_station,
        "구간": []
    }

    for sub in path.get("subPath", []):
        t = sub.get("trafficType")
        sub_json = {}

        if t == 1:  # 지하철
            stations = sub.get("passStopList", {}).get("stations", [])
            if not stations:
                continue
            station_names = [st.get("stationName") for st in stations]
            sub_json = {
                "구간유형": "지하철",
                "라인": sub.get("lane", [{}])[0].get("name"),
                "시작역": station_names[0],
                "종료역": station_names[-1],
                "정거장수": sub.get("stationCount"),
                "소요시간": sub.get("sectionTime"),
                "환승정보": sub.get("way"),
                "역좌표": [[float(st.get("y")), float(st.get("x"))] for st in stations]
            }

        elif t == 3:  # 도보
            section_path = sub.get("sectionPath", [])
            if not section_path:
                # 좌표 없으면 시작/종료 역 좌표로 기본 2점 생성
                sx = float(sub.get("startX", startX))
                sy = float(sub.get("startY", startY))
                ex = float(sub.get("endX", endX))
                ey = float(sub.get("endY", endY))
                section_path = [{"x": sx, "y": sy}, {"x": ex, "y": ey}]
            sub_json = {
                "구간유형": "도보",
                "소요시간": sub.get("sectionTime"),
                "좌표": [[float(p.get("y")), float(p.get("x"))] for p in section_path]
            }

        path_json["구간"].append(sub_json)

    json_paths.append(path_json)

# =========================
# 6. JSON 파일 저장
# =========================
with open("clean_paths.json", "w", encoding="utf-8") as f:
    json.dump(json_paths, f, ensure_ascii=False, indent=2)

print("✅ clean_paths.json 생성 완료! (지하철 + 좌표 있는 도보 + 환승 포함)")
