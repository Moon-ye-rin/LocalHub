-- =====================================================================
-- LocalHub - SQLite 스키마 v3.1
-- 기준: LocalHub API 명세서 v1.0(개정) + SCHEMA.md(TourAPI 4.0) + SOURCE.md
--       + 실제 제공 서울·경기 JSON 16개 파일(12,512건) 파싱 결과
--
-- [필수] posts / tags / post_tags / locations
-- [권장] post_likes / post_views          (명세서 5.7 보완 — 아래 주석)
-- [여유] post_images
-- [선택] content_types                    (코드→한글명 매핑)
-- =====================================================================
PRAGMA foreign_keys = ON;

-- =====================================================================
-- 1. 커뮤니티 (게시판)
-- =====================================================================

-- [필수] posts — 명세서 3.1
--   password  : 평문 저장(교육 목적 의도된 설계). 응답 스키마에서 반드시 제외.
--   updated_at: 수정 전에는 NULL (명세서 5.2 응답 예시)
--   view/like_count: 목록 정렬(sort=views/likes)용 캐시. 트리거가 관리.
CREATE TABLE posts (
    id         INTEGER PRIMARY KEY,
    category   VARCHAR(30)  NOT NULL,   -- 관광지/문화시설/축제공연행사/여행코스/레포츠/숙박/쇼핑/음식점/자유
    region     VARCHAR(10),               -- 서울/경기 (신규 글은 필수)
    district   VARCHAR(30),               -- 서울 자치구 또는 경기 시·군
    title      VARCHAR(200) NOT NULL,
    content    TEXT         NOT NULL,
    password   VARCHAR(100) NOT NULL,
    view_count INTEGER      NOT NULL DEFAULT 0,
    like_count INTEGER      NOT NULL DEFAULT 0,
    created_at DATETIME     NOT NULL DEFAULT (datetime('now')),  -- UTC 저장 → 응답 시 KST 변환
    updated_at DATETIME,
    CHECK (length(title) BETWEEN 1 AND 200),
    CHECK (length(password) >= 4)
);
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX idx_posts_view_count ON posts(view_count DESC);
CREATE INDEX idx_posts_like_count ON posts(like_count DESC);
CREATE INDEX idx_posts_category   ON posts(category, created_at DESC);
CREATE INDEX idx_posts_region_district ON posts(region, district);

-- [추가] comments — 익명 댓글 CRUD
CREATE TABLE comments (
    id         INTEGER PRIMARY KEY,
    post_id    INTEGER      NOT NULL,
    content    TEXT         NOT NULL,
    password   VARCHAR(100) NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at DATETIME,
    CHECK (length(content) BETWEEN 1 AND 1000),
    CHECK (length(password) >= 4),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);
CREATE INDEX idx_comments_post_created ON comments(post_id, created_at);

-- [필수] tags / post_tags — 명세서 3.2 / 3.3
CREATE TABLE tags (
    id   INTEGER PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE post_tags (
    post_id INTEGER NOT NULL,
    tag_id  INTEGER NOT NULL,
    PRIMARY KEY (post_id, tag_id),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id)  REFERENCES tags(id)  ON DELETE CASCADE
);
CREATE INDEX idx_post_tags_tag ON post_tags(tag_id);

-- [여유] post_images — 명세서 3.4
CREATE TABLE post_images (
    id          INTEGER PRIMARY KEY,
    post_id     INTEGER      NOT NULL,
    image_url   VARCHAR(255) NOT NULL,
    uploaded_at DATETIME     NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);
CREATE INDEX idx_post_images_post ON post_images(post_id);

-- [권장] post_likes / post_views  ※ 명세서에는 없는 테이블
--   명세서 5.7은 "서버는 like_count만 +1, 중복 방지는 프론트"인데,
--   그러면 새로고침·시크릿창·스토리지 삭제로 좋아요/조회수가 무한 증가한다.
--   client_key(프론트가 crypto.randomUUID()로 만들어 localStorage 보관 →
--   요청 헤더 X-Client-Key)로 1인 1회를 DB가 강제한다. API 형태는 그대로.
CREATE TABLE post_likes (
    id         INTEGER PRIMARY KEY,
    post_id    INTEGER     NOT NULL,
    client_key VARCHAR(64) NOT NULL,
    created_at DATETIME    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (post_id, client_key),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

CREATE TABLE post_views (
    id         INTEGER PRIMARY KEY,
    post_id    INTEGER     NOT NULL,
    client_key VARCHAR(64) NOT NULL,
    viewed_at  DATETIME    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (post_id, client_key),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- =====================================================================
-- 2. 제공 관광 데이터 (TourAPI 4.0 원본 캐시)
-- =====================================================================

-- [필수] locations — 명세서 3.5 + SCHEMA.md
--   공공누리 3유형(변경 금지): 원본 필드명·값을 그대로 유지한다.
--   - 빈 문자열("")도 원본 그대로 저장 (NULL로 치환하지 않음)
--   - mapx/mapy만 REAL로 형변환 (명세서 3.5 허용 범위)
--   ★ 명세서 3.5에 빠져 있으나 실제 데이터에 100% 존재하고 반드시 필요한 필드:
--     lDongRegnCd / lDongSignguCd (법정동 코드) → 실질적인 '구' 단위 필터
--     lclsSystm1~3 (신 분류체계)               → 실질적인 카테고리 필터
--     cpyrhtDivCd (저작권 구분)                → 이미지 사용 가능 여부 판단
--     ※ 이유: areacode/sigungucode와 cat1~3은 지역별 결측이 있어
--        명세서 5.9의 areacode 필터는 실데이터에서 거의 동작하지 않는다.
CREATE TABLE locations (
    contentid     VARCHAR(20)  PRIMARY KEY,        -- 원본 고유 ID (12,512건 전부 유니크 확인)
    contenttypeid VARCHAR(2)   NOT NULL,           -- 12/14/15/25/28/32/38/39
    region        VARCHAR(20)  NOT NULL DEFAULT '서울',  -- 파일 최상위 region
    title         VARCHAR(200) NOT NULL,
    addr1         VARCHAR(200),                    -- "" = 주소 미제공
    addr2         VARCHAR(200),
    zipcode       VARCHAR(10),
    tel           VARCHAR(50),                     -- 97%가 "" (실데이터)
    mapx          REAL,                            -- 경도 (원본 string → float)
    mapy          REAL,                            -- 위도
    mlevel        VARCHAR(2),
    areacode      VARCHAR(5),                      -- 79%가 "" → 필터로 쓰지 말 것
    sigungucode   VARCHAR(5),                      -- 79%가 ""
    lDongRegnCd   VARCHAR(2),                      -- '11' = 서울
    lDongSignguCd VARCHAR(3),                      -- 구 코드 (99.97% 존재) → 지역 필터는 이걸로
    cat1          VARCHAR(10),                     -- 78%가 ""
    cat2          VARCHAR(10),
    cat3          VARCHAR(10),
    lclsSystm1    VARCHAR(3),                      -- 신 분류 대분류 (100% 존재)
    lclsSystm2    VARCHAR(5),
    lclsSystm3    VARCHAR(9),
    firstimage    VARCHAR(255),                    -- "" = 이미지 없음
    firstimage2   VARCHAR(255),
    cpyrhtDivCd   VARCHAR(5),                      -- Type1/Type3 등
    createdtime   VARCHAR(14),                     -- 원본 YYYYMMDDHHmmss (문자열 유지)
    modifiedtime  VARCHAR(14),
    loaded_at     DATETIME NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_loc_type    ON locations(contenttypeid);
CREATE INDEX idx_loc_title   ON locations(title);
CREATE INDEX idx_loc_signgu  ON locations(lDongSignguCd, contenttypeid);
CREATE INDEX idx_loc_lcls    ON locations(lclsSystm1);
-- keyword 검색(title/addr1 LIKE '%..%')은 일반 B-tree 인덱스를 활용하기 어렵다.

-- [추가] 지역정보 댓글·별점·좋아요·북마크·조회
CREATE TABLE location_comments (
    id         INTEGER PRIMARY KEY,
    contentid  VARCHAR(20) NOT NULL,
    nickname   VARCHAR(30) NOT NULL DEFAULT '익명',
    content    TEXT        NOT NULL,
    rating     INTEGER      NOT NULL DEFAULT 0,
    password   VARCHAR(100) NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at DATETIME,
    CHECK (length(content) BETWEEN 1 AND 1000),
    CHECK (rating BETWEEN 0 AND 5),
    CHECK (length(password) >= 4),
    FOREIGN KEY (contentid) REFERENCES locations(contentid) ON DELETE CASCADE
);
CREATE INDEX idx_location_comments_content_created ON location_comments(contentid, created_at);

CREATE TABLE location_likes (
    id         INTEGER PRIMARY KEY,
    contentid  VARCHAR(20) NOT NULL,
    client_key VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    UNIQUE (contentid, client_key),
    FOREIGN KEY (contentid) REFERENCES locations(contentid) ON DELETE CASCADE
);
CREATE INDEX idx_location_likes_content ON location_likes(contentid);

CREATE TABLE location_bookmarks (
    id         INTEGER PRIMARY KEY,
    contentid  VARCHAR(20) NOT NULL,
    client_key VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    UNIQUE (contentid, client_key),
    FOREIGN KEY (contentid) REFERENCES locations(contentid) ON DELETE CASCADE
);
CREATE INDEX idx_location_bookmarks_content ON location_bookmarks(contentid);

CREATE TABLE location_views (
    id         INTEGER PRIMARY KEY,
    contentid  VARCHAR(20) NOT NULL,
    client_key VARCHAR(64) NOT NULL,
    viewed_at  DATETIME NOT NULL DEFAULT (datetime('now')),
    UNIQUE (contentid, client_key),
    FOREIGN KEY (contentid) REFERENCES locations(contentid) ON DELETE CASCADE
);
CREATE INDEX idx_location_views_content ON location_views(contentid);

-- [선택] content_types — 코드→한글명 (화면 필터·챗봇 의도 매핑용)
CREATE TABLE content_types (
    contenttypeid VARCHAR(2)  PRIMARY KEY,
    name          VARCHAR(20) NOT NULL
);
INSERT INTO content_types (contenttypeid, name) VALUES
    ('12','관광지'), ('14','문화시설'), ('15','축제공연행사'), ('25','여행코스'),
    ('28','레포츠'), ('32','숙박'), ('38','쇼핑'), ('39','음식점');

-- =====================================================================
-- 3. 트리거
-- =====================================================================

-- 게시글 "내용"이 실제로 바뀔 때만 updated_at 갱신
-- (WHEN 절이 없으면 조회수만 올라도 '수정된 글'로 표시된다)
CREATE TRIGGER trg_posts_updated_at
AFTER UPDATE ON posts FOR EACH ROW
WHEN OLD.title IS NOT NEW.title OR OLD.content IS NOT NEW.content OR OLD.category IS NOT NEW.category
  OR OLD.region IS NOT NEW.region OR OLD.district IS NOT NEW.district
BEGIN
    UPDATE posts SET updated_at = datetime('now') WHERE id = OLD.id;
END;

CREATE TRIGGER trg_comments_updated_at
AFTER UPDATE ON comments FOR EACH ROW
WHEN OLD.content IS NOT NEW.content
BEGIN UPDATE comments SET updated_at = datetime('now') WHERE id = OLD.id; END;

CREATE TRIGGER trg_location_comments_updated_at
AFTER UPDATE ON location_comments FOR EACH ROW
WHEN OLD.nickname IS NOT NEW.nickname OR OLD.content IS NOT NEW.content
  OR OLD.rating IS NOT NEW.rating
BEGIN UPDATE location_comments SET updated_at = datetime('now') WHERE id = OLD.id; END;

-- 카운터 자동 동기화: 앱은 INSERT OR IGNORE 한 줄이면 끝
CREATE TRIGGER trg_like_insert
AFTER INSERT ON post_likes FOR EACH ROW
BEGIN UPDATE posts SET like_count = like_count + 1 WHERE id = NEW.post_id; END;

CREATE TRIGGER trg_like_delete
AFTER DELETE ON post_likes FOR EACH ROW
BEGIN UPDATE posts SET like_count = MAX(like_count - 1, 0) WHERE id = OLD.post_id; END;

CREATE TRIGGER trg_view_insert
AFTER INSERT ON post_views FOR EACH ROW
BEGIN UPDATE posts SET view_count = view_count + 1 WHERE id = NEW.post_id; END;

-- =====================================================================
-- API ↔ 테이블 매핑
--   GET  /api/posts                  posts + tags 조인 (category/keyword/tag/sort)
--   GET  /api/posts/{id}             posts + tags + post_images / post_views INSERT
--   POST /api/posts                  posts + tags UPSERT + post_tags
--   PUT/DELETE /api/posts/{id}       password 비교 후 처리 (CASCADE 정리)
--   POST/DELETE /api/posts/{id}/like post_likes 추가/삭제 → like_count 자동
--   GET  /api/tags                   tags + post_tags COUNT
--   GET  /api/locations              locations (contenttypeid/keyword/페이지네이션)
--   GET  /api/locations/{contentid}  locations PK 조회 + 조회 기록 + 근처 5곳
--   GET/POST/PUT/DELETE /api/locations/{id}/comments 지역정보 댓글·별점 + password 검증
--   POST/DELETE /api/locations/{id}/like, /bookmark 지역정보 반응 토글
--   POST /api/chat                   locations(의도별 contenttypeid) + posts 조회 → 프롬프트
--   GET/POST/PUT/DELETE comments     comments CRUD + password 검증
--   POST /api/posts/{id}/images      post_images INSERT
--   GET  /api/dashboard              월별 카테고리/지역·지역정보 순위/평점/주간 트렌드 집계
--   WS   /ws/notifications           새 게시글 실시간 알림 + 현재 접속자 수
-- =====================================================================
