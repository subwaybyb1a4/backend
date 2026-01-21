# =========================
# 지도 상에 시작역->도착역 경로 3가지 볼 수 있는 코드
# =========================
 
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
import folium
import random

# =========================
# 0. env 로드
# =========================
env_path = Path(r"C:/Users/JWHEO/Desktop/backend/.env")
load_dotenv(env_path)
api_key = os.getenv("API_KEY")
if not api_key:
    raise Exception("❌ API_KEY를 불러오지 못했습니다. .env 파일 확인!")

# =========================
# 1. 노선 색상
# =========================
LINE_COLORS = {
    "1호선": "#0D3692", "2호선": "#33A23D", "3호선": "#FE5B10", "4호선": "#00A2D1",
    "5호선": "#8B50A4", "6호선": "#C55C1D", "7호선": "#54640D", "8호선": "#F51361",
    "9호선": "#BDB092", "경의중앙선": "#77C4A3", "분당선": "#F5A200", "신분당선": "#D4003B",
    "공항철도": "#3681B7", "경춘선": "#0C8E72", "수인분당선": "#F5A200",
}

# =========================
# 2. 사용자 입력
# =========================
start_station = input("출발역: ").replace("역", "")
end_station = input("도착역: ").replace("역", "")

# =========================
# 3. 역 → 좌표
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
# 4. 경로 조회 (지하철만)
# =========================
url = "https://api.odsay.com/v1/api/searchPubTransPathT"
res = requests.get(url, params={"apiKey": api_key, "SX": startX, "SY": startY, "EX": endX, "EY": endY, "OPT": 1}).json()
paths = [p for p in res["result"]["path"][:10] if all(sub["trafficType"] != 2 for sub in p["subPath"])]
if not paths:
    raise Exception("❌ 버스 없는 지하철 경로 없음!")

# =========================
# 5. 보조 함수
# =========================
def normalize_line_name(raw_name):
    return raw_name.replace("서울", "").replace("수도권", "").split("(")[0].strip()

def create_curve(start, end, segments=5, max_offset=0.0005):
    """Bezier 느낌으로 선을 굽이치게 만드는 함수"""
    points = [start]
    for i in range(1, segments):
        t = i / segments
        offset_lat = random.uniform(-max_offset, max_offset)
        offset_lon = random.uniform(-max_offset, max_offset)
        mid_lat = start[0]*(1-t) + end[0]*t + offset_lat
        mid_lon = start[1]*(1-t) + end[1]*t + offset_lon
        points.append([mid_lat, mid_lon])
    points.append(end)
    return points

def add_walk_line(map_obj, start, end, tooltip_text):
    coords = create_curve(start, end)
    folium.PolyLine(coords, color="yellow", weight=3, dash_array="5,5",
                    tooltip=tooltip_text).add_to(map_obj)
    return coords[-1]

# =========================
# 6. 지도 생성
# =========================
m = folium.Map(location=[startY, startX], zoom_start=13)
top3 = paths[:3]

for i, path in enumerate(top3):
    last_coords = [startY, startX]

    for idx_sub, sub in enumerate(path["subPath"]):
        t = sub["trafficType"]

        # --------------------
        # 지하철 구간
        # --------------------
        if t == 1 and "passStopList" in sub:
            stations = sub["passStopList"]["stations"]
            first_station = stations[0]
            last_station = stations[-1]

            # 시작역 → 첫 지하철역 도보
            if idx_sub == 0 and start_station != first_station["stationName"]:
                last_coords = add_walk_line(m, last_coords, [float(first_station["y"]), float(first_station["x"])],
                                            f"🚶 {start_station} → {first_station['stationName']}")

            # 지하철 PolyLine
            coords = [[float(st["y"]), float(st["x"])] for st in stations]
            line_name = normalize_line_name(sub["lane"][0]["name"])
            color = LINE_COLORS.get(line_name, "gray")
            folium.PolyLine(coords, color=color, weight=5, opacity=0.9,
                            tooltip=f"🚇 {line_name} / {i+1}").add_to(m)
            last_coords = coords[-1]

            # 환승역 표시 (도착역 제외)
            if last_station["stationName"] != end_station and sub.get("way", ""):
                folium.Marker(last_coords, tooltip=f"🔄 환승: {last_station['stationName']}",
                              icon=folium.Icon(color="orange", icon="arrows-alt", prefix="fa")).add_to(m)

            # 다음 지하철 시작역과 도보 연결
            if idx_sub + 1 < len(path["subPath"]) and path["subPath"][idx_sub + 1]["trafficType"] == 1:
                next_first = path["subPath"][idx_sub + 1]["passStopList"]["stations"][0]
                last_coords = add_walk_line(m, last_coords,
                                            [float(next_first["y"]), float(next_first["x"])],
                                            f"🚶 {last_station['stationName']} → {next_first['stationName']}")

        # --------------------
        # 도보 구간 (trafficType == 3)
        # --------------------
        elif t == 3:
            if "sectionPath" in sub and sub["sectionPath"]:
                coords = [[float(p["y"]), float(p["x"])] for p in sub["sectionPath"]]
                folium.PolyLine(coords, color="yellow", weight=3, dash_array="5,5",
                                tooltip=f"🚶 도보 구간 / {i+1}").add_to(m)
                last_coords = coords[-1]

    # 마지막 지하철역 → 도착역 도보
    last_sub = [s for s in path["subPath"] if s["trafficType"] == 1][-1]
    last_station = last_sub["passStopList"]["stations"][-1]
    if last_station["stationName"] != end_station:
        last_coords = add_walk_line(m, last_coords, [endY, endX],
                                    f"🚶 {last_station['stationName']} → {end_station}")

# 출발/도착 마커
folium.Marker([startY, startX], tooltip="출발", icon=folium.Icon(color="green")).add_to(m)
folium.Marker([endY, endX], tooltip="도착", icon=folium.Icon(color="red")).add_to(m)

# =========================
# 7. HTML 저장
# =========================
m.save("route_top3_curve.html")
print("🗺️ route_top3_curve.html 생성 완료! (모든 도보 구간 노란 점선 적용)")
