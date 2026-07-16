# LocalHub 서울·경기 최종 구현본 v1.10.2

Figma Make 프로토타입을 Vue.js 3 + FastAPI + SQLite 구조로 구현하고, 서울·경기 TourAPI 데이터를 적용한 실행 가능한 프로젝트입니다.

## v1.10.2 주요 변경

- 지역정보 지도 영역을 `위치`와 `경로찾기` 토글 화면으로 분리
- 최초 진입 시 v1.9.1 방식의 현재 장소 위치 지도를 기본 표시
- 경로찾기 화면은 출발지·도착지 핀과 계산된 경로를 표시
- 지도 타일이 차단된 환경에서도 핀과 경로가 사라지지 않도록 중립 지도 배경 제공
- 경로 탐색 중 문구를 `탐색 중...`으로 변경
- 지도 범례의 `A* 경로` 문구를 `경로`로 변경
- 이동 방식 선택과 탐색 노드 표시를 사용자 화면에서 제거
- 경로 결과를 거리, 예상 시간(자동차), 예상 시간(도보)로 표시

## v1.10.1 주요 변경

- 외부 Leaflet CDN 의존성을 제거해 학교·사내망에서 발생하던 지도 로딩 오류 수정
- OpenStreetMap 타일을 직접 표시하는 프로젝트 내장형 상호작용 지도로 교체
- 현재 보고 있는 지역정보를 출발지로 자동 설정
- 서울·경기 전체 지역정보에서 도착 장소 검색 및 가까운 5곳 빠른 선택
- OpenStreetMap 도로망을 Overpass API로 불러와 A* 알고리즘으로 최단 경로 계산
- 출발·도착 핀 2개와 이동 경로를 하나의 지도에 표시

## v1.9 주요 변경

- 게시글·지역정보 상세에서 좋아요·북마크와 공유 버튼을 그룹별로 분리해 재배치
- 기능 없는 `공유` 라벨과 아이콘 제거
- 카카오톡 버튼 문구를 `카카오톡 공유`로 변경
- 근처 지역정보 안내 문구를 간결하게 수정
- 홈 화면의 대표 이미지 노출 건수 문구 제거
- 익명 커뮤니티 안내 문구를 `비밀번호 기반 게시글·댓글`로 변경

## v1.8 주요 변경

- `backend/requirements.txt`에 `tzdata` 추가
- 게시글·지역정보 상세에 카카오톡 공유 및 링크 복사 기능 추가
- 콘텐츠별 동적 OG/Twitter 메타데이터 적용
- 소셜 크롤러용 `/share/posts/{id}`, `/share/locations/{contentid}` 랜딩 페이지 추가
- 기본 OG 대표 이미지 포함

## v1.7 주요 변경

- 홈·지역정보 화면 하단의 중복 데이터 출처 프레임 제거
- 게시글 작성 화면의 교육용 평문 비밀번호 안내 문구 숨김
- 실시간 알림별 삭제 버튼 추가
- 알림 목록은 한 화면에 5개 높이만 표시하고 초과 알림은 스크롤 제공
- 마우스/포인터 드래그로 알림 목록 스크롤 가능
- 지역정보 카드에서 북마크 등록·해제 가능
- 지역정보 검색창 옆에 북마크만 보기 필터 추가
- 북마크 목록도 서버 페이지네이션과 검색·지역·카테고리 필터를 함께 지원

## 기술 스택

- Frontend: Vue.js 3 + TypeScript + Vite SPA
- Backend: FastAPI + SQLAlchemy 2.0
- Database: SQLite
- Realtime: FastAPI WebSocket
- Charts: Chart.js + vue-chartjs
- Map: OpenStreetMap 위치 iframe + 프로젝트 내장형 OSM 타일 지도 + Overpass API
- Social Share: Kakao JavaScript SDK + Open Graph
- Deployment: Netlify + Render

## 주요 기능

- 익명 게시글 CRUD, 댓글 CRUD, 태그, 검색, 이미지 첨부·삭제
- 게시글 조회수, 좋아요 토글, 북마크
- 게시글 서울/경기·자치구/시군 선택
- 서울·경기 지역정보 12,512건 적재 및 대표 이미지 보유 데이터 노출
- 지역정보 전체/서울/경기 전환, 페이지당 21개 및 10페이지 단위 페이지네이션
- 지역정보 상세 내부 지도, 좌표 기준 근처 5곳, 복수 장소 A* 길찾기
- 지역정보 댓글·별점·수정·삭제·좋아요·북마크·조회수
- 새 게시글 실시간 알림과 접속자 현황
- 월별 카테고리, 지역 순위, 지역정보 순위, 평점 순위, 주간 트렌드 대시보드
- 서울·경기 지역정보와 게시글 기반 챗봇

## Windows 실행

압축 해제 후 다음 파일을 순서대로 실행합니다.

1. `start_backend.bat`
2. `start_frontend.bat`

접속 주소:

- 프론트엔드: `http://localhost:5173`
- API 문서: `http://localhost:8000/docs`
- 상태 확인: `http://localhost:8000/health`
- 실시간 채널: `ws://localhost:8000/ws/notifications`

## 실시간 기능 참고

현재 접속자 집계와 게시글 알림은 단일 FastAPI 프로세스의 메모리에 연결 상태를 관리합니다. 기본 Render 설정처럼 worker 1개로 실행할 때 정상 동작합니다. 여러 worker로 확장할 때는 Redis pub/sub 같은 공용 메시지 저장소가 필요합니다.

## 환경변수

백엔드는 `backend/.env.example`, 프론트엔드는 `frontend/.env.example`을 각각 `.env`로 복사해 사용합니다. 실제 `.env`와 API 키는 Git에 올리지 않습니다.

카카오톡 공유를 사용하려면 `frontend/.env`의 `VITE_KAKAO_JAVASCRIPT_KEY`를 설정하고, 배포 시 `VITE_PUBLIC_SITE_URL`과 백엔드 `FRONTEND_PUBLIC_URL`을 실제 주소로 변경합니다.

## 검증

```bash
cd backend
pytest -q

cd ../frontend
npm ci
npm run build
```

상세 변경은 `docs/기능추가_v1.10.md`를 확인하세요.

