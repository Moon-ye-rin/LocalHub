def test_health_and_locations(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["locations"] == 3
    assert health.json()["visible_locations"] == 2
    assert health.json()["visible_by_region"] == {"경기": 1, "서울": 1}

    all_items = client.get("/api/locations")
    assert all_items.status_code == 200
    assert all_items.json()["data"]["region"] == "전체"
    assert all_items.json()["data"]["total_count"] == 2

    all_explicit = client.get("/api/locations", params={"region": "전체"})
    assert all_explicit.status_code == 200
    assert all_explicit.json()["data"]["total_count"] == 2

    seoul = client.get(
        "/api/locations",
        params={"region": "서울", "contenttypeid": "12", "keyword": "경복궁"},
    )
    assert seoul.status_code == 200
    body = seoul.json()
    assert body["success"] is True
    assert body["data"]["region"] == "서울"
    assert body["data"]["total_count"] == 1
    assert body["data"]["items"][0]["contentid"] == "126508"

    gyeonggi = client.get("/api/locations", params={"region": "경기"})
    assert gyeonggi.status_code == 200
    assert gyeonggi.json()["data"]["total_count"] == 1
    assert gyeonggi.json()["data"]["items"][0]["title"] == "수원화성"

    detail = client.get("/api/locations/126508")
    assert detail.status_code == 200
    assert detail.json()["data"]["title"] == "경복궁"

    hidden_detail = client.get("/api/locations/999002")
    assert hidden_detail.status_code == 404


def test_post_crud_and_password(client):
    created = client.post(
        "/api/posts",
        json={
            "category": "문화시설",
            "region": "경기",
            "district": "수원시",
            "title": "새 글",
            "content": "본문",
            "password": "5678",
            "tags": ["서울", "문화"],
        },
    )
    assert created.status_code == 201
    post_id = created.json()["data"]["id"]

    wrong = client.post(f"/api/posts/{post_id}/verify-password", json={"password": "0000"})
    assert wrong.status_code == 403
    assert wrong.json()["data"]["match"] is False

    verified = client.post(f"/api/posts/{post_id}/verify-password", json={"password": "5678"})
    assert verified.status_code == 200

    updated = client.put(
        f"/api/posts/{post_id}",
        json={
            "category": "문화시설",
            "region": "서울",
            "district": "중구",
            "title": "수정 글",
            "content": "수정 본문",
            "password": "5678",
            "tags": ["수정"],
        },
    )
    assert updated.status_code == 200

    deleted = client.request("DELETE", f"/api/posts/{post_id}", json={"password": "5678"})
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "게시글이 삭제되었습니다."


def test_duplicate_view_and_like_toggle(client):
    headers = {"X-Client-Key": "pytest-client"}
    first = client.get("/api/posts/1", headers=headers).json()["data"]
    second = client.get("/api/posts/1", headers=headers).json()["data"]
    assert first["view_count"] == second["view_count"]

    like1 = client.post("/api/posts/1/like", headers=headers).json()["data"]
    like2 = client.post("/api/posts/1/like", headers=headers).json()["data"]
    assert like1["like_count"] == like2["like_count"]
    assert like2["already_liked"] is True
    assert like2["liked"] is True

    unlike = client.delete("/api/posts/1/like", headers=headers).json()["data"]
    assert unlike["liked"] is False
    assert unlike["like_count"] == max(like1["like_count"] - 1, 0)


def test_posts_list_tags_and_chat(client):
    listing = client.get("/api/posts", params={"keyword": "경복궁", "tag": "경복궁"})
    assert listing.status_code == 200
    assert listing.json()["data"]["total_count"] >= 1

    tags = client.get("/api/tags", params={"popular": True})
    assert tags.status_code == 200
    assert tags.json()["data"]["tags"][0]["name"] == "경복궁"

    chat = client.post("/api/chat", json={"message": "경복궁 관광지 알려줘", "history": []})
    assert chat.status_code == 200
    assert chat.json()["data"]["references"]
    assert "한국관광공사" in chat.json()["data"]["source_notice"]


def test_comment_crud(client):
    created = client.post(
        "/api/posts/1/comments",
        json={"content": "좋은 정보 감사합니다.", "password": "2468"},
    )
    assert created.status_code == 201
    comment_id = created.json()["data"]["id"]

    listing = client.get("/api/posts/1/comments")
    assert listing.status_code == 200
    assert listing.json()["data"]["total_count"] == 1
    assert listing.json()["data"]["comments"][0]["content"] == "좋은 정보 감사합니다."

    wrong = client.put(
        f"/api/posts/1/comments/{comment_id}",
        json={"content": "수정 댓글", "password": "0000"},
    )
    assert wrong.status_code == 403

    updated = client.put(
        f"/api/posts/1/comments/{comment_id}",
        json={"content": "수정 댓글", "password": "2468"},
    )
    assert updated.status_code == 200

    detail = client.get("/api/posts/1").json()["data"]
    assert detail["comment_count"] == 1

    deleted = client.request(
        "DELETE",
        f"/api/posts/1/comments/{comment_id}",
        json={"password": "2468"},
    )
    assert deleted.status_code == 200
    assert client.get("/api/posts/1/comments").json()["data"]["total_count"] == 0


def test_image_upload_and_delete(client):
    response = client.post(
        "/api/posts/1/images",
        files={"file": ("sample.png", b"fake-png-content", "image/png")},
    )
    assert response.status_code == 201
    image_url = response.json()["data"]["image_url"]
    assert image_url.startswith("/uploads/1/")

    post = client.get("/api/posts/1").json()["data"]
    assert image_url in post["images"]

    wrong = client.request(
        "DELETE",
        "/api/posts/1/images",
        json={"image_url": image_url, "password": "0000"},
    )
    assert wrong.status_code == 403

    deleted = client.request(
        "DELETE",
        "/api/posts/1/images",
        json={"image_url": image_url, "password": "1234"},
    )
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "첨부 이미지가 삭제되었습니다."

    post = client.get("/api/posts/1").json()["data"]
    assert image_url not in post["images"]


def test_location_engagement_nearby_and_reviews(client):
    headers = {"X-Client-Key": "location-client"}
    first = client.get("/api/locations/126508", headers=headers)
    second = client.get("/api/locations/126508", headers=headers)
    assert first.status_code == 200
    assert first.json()["data"]["nearby"][0]["contentid"] == "999001"
    assert first.json()["data"]["view_count"] == second.json()["data"]["view_count"]

    comment = client.post(
        "/api/locations/126508/comments",
        json={"nickname": "", "content": "방문하기 좋은 곳입니다.", "rating": 5, "password": "1357"},
    )
    assert comment.status_code == 201
    reviews = client.get("/api/locations/126508/comments").json()["data"]
    assert reviews["comments"][0]["nickname"] == "익명"
    assert reviews["average_rating"] == 5.0
    location_comment_id = reviews["comments"][0]["id"]

    wrong_update = client.put(
        f"/api/locations/126508/comments/{location_comment_id}",
        json={"nickname": "방문자", "content": "수정 후기", "rating": 4, "password": "0000"},
    )
    assert wrong_update.status_code == 403

    updated = client.put(
        f"/api/locations/126508/comments/{location_comment_id}",
        json={"nickname": "방문자", "content": "수정 후기", "rating": 4, "password": "1357"},
    )
    assert updated.status_code == 200
    updated_reviews = client.get("/api/locations/126508/comments").json()["data"]
    assert updated_reviews["comments"][0]["nickname"] == "방문자"
    assert updated_reviews["average_rating"] == 4.0

    liked = client.post("/api/locations/126508/like", headers=headers).json()["data"]
    assert liked == {"count": 1, "active": True}
    unliked = client.delete("/api/locations/126508/like", headers=headers).json()["data"]
    assert unliked == {"count": 0, "active": False}

    bookmarked = client.post("/api/locations/126508/bookmark", headers=headers).json()["data"]
    assert bookmarked == {"count": 1, "active": True}

    listed = client.get("/api/locations", headers=headers).json()["data"]
    listed_item = next(item for item in listed["items"] if item["contentid"] == "126508")
    assert listed_item["bookmarked"] is True

    bookmark_only = client.get(
        "/api/locations", params={"bookmarked_only": True}, headers=headers
    ).json()["data"]
    assert bookmark_only["total_count"] == 1
    assert bookmark_only["items"][0]["contentid"] == "126508"

    unbookmarked = client.delete("/api/locations/126508/bookmark", headers=headers).json()["data"]
    assert unbookmarked == {"count": 0, "active": False}


def test_dashboard(client):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["monthly_category"]["labels"]) == 7
    assert len(data["monthly_category"]["series"]) == 4
    assert "total" in data["category_distribution"]
    assert data["popular_regions"][0]["label"] == "서울 종로구"
    assert data["score_formula"] == "(댓글 수 × 3) + (좋아요 수 × 2) + 조회 수"
    assert "popular_locations" in data
    assert "top_rated_locations" in data
    assert data["top_rated_locations"][0]["contentid"] == "126508"
    assert data["weekly_trend"]["labels"] == ["월", "화", "수", "목", "금", "토", "일"]


def test_realtime_new_post_notification_and_presence(client):
    with client.websocket_connect("/ws/notifications?client_key=pytest-ws") as websocket:
        first = websocket.receive_json()
        assert first["type"] == "connected"
        assert first["online_count"] >= 1
        presence = websocket.receive_json()
        assert presence["type"] == "presence"

        created = client.post(
            "/api/posts",
            json={
                "category": "관광지",
                "region": "서울",
                "district": "중구",
                "title": "실시간 알림 테스트",
                "content": "웹소켓 알림 확인",
                "password": "1234",
                "tags": [],
            },
        )
        assert created.status_code == 201
        event = websocket.receive_json()
        assert event["type"] == "post_created"
        assert event["post"]["id"] == created.json()["data"]["id"]
        assert event["post"]["title"] == "실시간 알림 테스트"


def test_share_pages_have_open_graph_metadata(client):
    post_share = client.get('/share/posts/1')
    assert post_share.status_code == 200
    assert 'property="og:title"' in post_share.text
    assert '테스트 경복궁 후기 | LocalHub' in post_share.text
    assert 'http://localhost:5173/posts/1' in post_share.text
    assert '/static/og-default.png' in post_share.text

    location_share = client.get('/share/locations/126508')
    assert location_share.status_code == 200
    assert '경복궁 | LocalHub' in location_share.text
    assert 'https://example.com/gyeongbokgung.jpg' in location_share.text
    assert 'http://localhost:5173/locations/126508' in location_share.text
