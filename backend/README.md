# 안끼길 Backend

FastAPI 기반의 대중교통 경로 추천 API입니다. ODSay API를 활용하여 경로를 검색하고, 쾌적도 점수를 계산합니다.

## 기능

- 🚇 대중교통 경로 검색 (ODSay API)
- 😊 경로 쾌적도 분석
- 💾 경로 저장 및 관리
- 📊 환승, 도보거리, 소요시간 기반 점수 계산

## 설치 방법

### 1. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows
```

### 2. 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 ODSay API 키를 입력합니다:

```bash
cp .env.example .env
```

`.env` 파일을 열어 수정:
```env
ODSAY_API_KEY=여기에_발급받은_API_키_입력
```

> **ODSay API 키 발급**: https://lab.odsay.com/ 에서 회원가입 후 발급받을 수 있습니다.

## 실행 방법

### 개발 서버 실행

```bash
cd backend
uvicorn app.main:app --reload
```

또는:

```bash
python -m app.main
```

서버가 시작되면 다음 주소로 접속:
- API: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 대체 API 문서: http://localhost:8000/redoc

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py              # FastAPI 애플리케이션 진입점
│   ├── api/
│   │   └── routes.py        # API 엔드포인트
│   ├── schemas/
│   │   └── route.py         # Pydantic 스키마
│   ├── services/
│   │   ├── odsay_service.py    # ODSay API 연동
│   │   ├── comfort_service.py   # 쾌적도 계산
│   │   └── route_service.py     # 경로 관리
│   ├── db/
│   │   ├── session.py       # 데이터베이스 세션
│   │   └── models.py        # SQLAlchemy 모델
│   └── core/
│       └── config.py        # 설정 관리
├── requirements.txt         # Python 의존성
└── .env.example            # 환경 변수 예시
```

## API 엔드포인트

### 경로 검색
- **POST** `/api/v1/routes/search`
  - Body: `{"start_location": "서울역", "end_location": "강남역", "prefer_comfort": true}`

### 경로 조회
- **GET** `/api/v1/routes/{route_id}`

### 경로 목록
- **GET** `/api/v1/routes/`

### 경로 저장
- **POST** `/api/v1/routes/save`
  - Body: `{"route_id": 1, "name": "출근길"}`

### 저장된 경로 목록
- **GET** `/api/v1/routes/saved/`

## 쾌적도 계산 기준

쾌적도는 다음 요소를 종합하여 0-100점으로 계산됩니다:

- **환승 횟수** (30%): 환승이 적을수록 높은 점수
- **도보 거리** (25%): 걷는 거리가 짧을수록 높은 점수
- **소요 시간** (20%): 이동 시간이 짧을수록 높은 점수
- **혼잡도** (15%): 덜 혼잡할수록 높은 점수 (추후 실시간 데이터 연동 예정)
- **경로 복잡도** (10%): 경로가 단순할수록 높은 점수

## 개발 예정 기능

- [ ] 실시간 혼잡도 데이터 연동
- [ ] 사용자 인증 시스템
- [ ] 즐겨찾기 위치 관리
- [ ] 시간대별 경로 추천
- [ ] 경로 비교 기능

## 기술 스택

- **FastAPI**: 고성능 Python 웹 프레임워크
- **SQLAlchemy**: ORM
- **Pydantic**: 데이터 검증
- **httpx**: 비동기 HTTP 클라이언트
- **ODSay API**: 대중교통 경로 검색
