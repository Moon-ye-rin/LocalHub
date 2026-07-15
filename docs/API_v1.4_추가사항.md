# API v1.4 추가사항

## 게시글 작성·수정

`POST /api/posts`, `PUT /api/posts/{post_id}` 요청에 아래 필드가 추가됩니다.

```json
{
  "category": "관광지",
  "region": "서울",
  "district": "종로구",
  "title": "게시글 제목",
  "content": "게시글 내용",
  "password": "1234",
  "tags": ["경복궁"]
}
```

- `region`: `서울` 또는 `경기`
- `district`: 서울 25개 자치구 또는 경기 31개 시·군
- 지역과 세부 지역이 일치하지 않으면 422를 반환합니다.
- 게시글 목록·상세 응답에도 `region`, `district`가 포함됩니다.

## 대시보드

### `GET /api/dashboard`

응답 항목:

- `monthly_category`: 최근 7개월 관광지·맛집·문화·축제 게시글 수
- `category_distribution.total`: 전체 카테고리 분포
- `category_distribution.seoul`: 서울 카테고리 분포
- `category_distribution.gyeonggi`: 경기 카테고리 분포
- `popular_regions`: 지역별 참여 점수 상위 6개
- `weekly_trend`: 현재 주 월~일 조회·좋아요 이벤트 수
- `score_formula`: `(댓글 수 × 3) + (좋아요 수 × 2) + 조회 수`
