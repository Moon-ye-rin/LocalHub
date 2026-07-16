# API 명세서 적용 결과 및 v1.3 확장

## 적용 기준

- LocalHub API 명세서 v1.0
- DB ERD/SQLite 스키마 v3.0
- 서울·경기 TourAPI 4.0 JSON 16개 파일

## 기존 명세 구현

- 공통 응답 `{ success, data, message }`
- 게시글·댓글 CRUD
- 비밀번호 확인과 수정·삭제 재검증
- 검색, 태그, 카테고리, 페이지네이션, 정렬
- 조회수·좋아요
- 지역정보 목록·상세
- 챗봇 `POST /api/chat`
- 게시글 이미지 업로드·삭제
- KST ISO 8601 응답
- 환경변수 기반 민감정보 관리

## v1.3 확장

### 지역 필터

`GET /api/locations`에 다음 선택 파라미터를 추가했습니다.

```text
region=서울
region=경기
```

허용되지 않은 지역값은 FastAPI 검증 오류(422)를 반환합니다.

### 이미지 없는 데이터 비노출

원본 데이터는 SQLite에 모두 보존하지만 아래 조건을 만족하지 않는 항목은 목록, 상세, 홈 추천, 챗봇에서 제외합니다.

```text
firstimage IS NOT NULL
trim(firstimage) != ''
```

따라서 API의 `total_count`와 `total_pages`는 실제 화면에 노출 가능한 항목을 기준으로 계산됩니다.

## 데이터 현황

| 지역 | 원본 | 노출(firstimage 보유) |
|---|---:|---:|
| 서울 | 7,615 | 7,102 |
| 경기 | 4,897 | 4,496 |
| 합계 | 12,512 | 11,598 |

서울 음식점 데이터는 원본 1,097건이며 이 중 953건이 화면에 노출됩니다.

## v1.10 확장 — A* 길찾기

기존 API 명세에 없던 선택 기능으로 아래 엔드포인트를 추가했습니다.

```text
POST /api/routes/astar
```

요청:

```json
{
  "start_contentid": "126508",
  "end_contentid": "999001",
  "mode": "walk"
}
```

응답에는 A*로 계산한 도로 경로 좌표, 경로 거리, 예상 시간, 탐색 노드 수가 포함됩니다. `mode`는 `walk` 또는 `drive`입니다. 도로망은 OpenStreetMap Overpass API에서 조회하며, 공용 서버 오류·시간 초과 시 503을 반환합니다.
