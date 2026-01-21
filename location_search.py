import requests
import webbrowser

APP_KEY = "k9SiBHJ8U25AL7rsT2wYX8LLuw6wcqLY1mwo5z2U"


# 1. 사용자 입력
start_station = input("출발역을 입력하세요: ")
end_station = input("도착역을 입력하세요: ")

# 2. 역 이름 → 좌표 변환 함수
def get_coord(station_name):
    url = "https://apis.openapi.sk.com/tmap/geo/fullAddrGeo"
    params = {
        "version": "1",
        "fullAddr": station_name,
        "format": "json",
        "appKey": APP_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    print("지오코딩 응답 전체:")
    print(data)

    coord = data["coordinateInfo"]["coordinate"][0]
    return coord["lon"], coord["lat"]

startX, startY = get_coord(start_station)
endX, endY = get_coord(end_station)

print("출발 좌표:", startX, startY)
print("도착 좌표:", endX, endY)

# 3. 경로 검색 API 호출
url = "https://apis.openapi.sk.com/transit/routes/sub/"

payload = {
    "startX": startX,
    "startY": startY,
    "endX": endX,
    "endY": endY,
    "format": "json",
    "count": 5
}

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "appKey": APP_KEY
}

response = requests.post(url, json=payload, headers=headers)

result = response.json()

print("경로 결과:")
print(result)

# url = f"https://map.kakao.com/link/from/{start_station},{startY},{startX}/to/{end_station},{endY},{endX}"
# webbrowser.open(url)

url = f"https://map.naver.com/v5/directions/{startX},{startY},{start_station}/{endX},{endY},{end_station}/-/transit"
webbrowser.open(url)
