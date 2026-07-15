# LocalHub 지역정보 데이터 출처

- 제공 기관: 한국관광공사
- 데이터명: 국문 관광정보 서비스(TourAPI 4.0)
- 공공데이터포털: https://www.data.go.kr/data/15101578/openapi.do
- 라이선스: 공공누리 제3유형(출처 표시, 변경 금지, 상업적 이용 허용)
- 적재 방식: 사전 수집된 JSON 파일을 SQLite `locations` 테이블에 캐시
- 표시 정책: 원본 `firstimage`가 빈 문자열 또는 NULL인 항목은 사용자 화면과 챗봇에서 제외
- 원본 보존: mapx/mapy의 숫자 변환 외 원본 필드값을 수정하지 않음

- 수집 지역: 경기
