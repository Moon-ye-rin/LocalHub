import os
import shutil
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_localhub.db"
os.environ["SEED_DATA"] = "false"
os.environ["SEED_LOCATIONS"] = "false"
os.environ["UPLOAD_DIR"] = "test_uploads"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Location, Post, Tag


@pytest.fixture(scope="session", autouse=True)
def database():
    Path("test_localhub.db").unlink(missing_ok=True)
    shutil.rmtree("test_uploads", ignore_errors=True)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        post = Post(
            category="관광지",
            region="서울",
            district="종로구",
            title="테스트 경복궁 후기",
            content="경복궁 산책 후기입니다.",
            password="1234",
            tags=[Tag(name="경복궁")],
        )
        seoul_location = Location(
            contentid="126508",
            contenttypeid="12",
            region="서울",
            title="경복궁",
            addr1="서울특별시 종로구 사직로 161",
            addr2="",
            tel="",
            mapx=126.9769,
            mapy=37.5796,
            lDongRegnCd="11",
            lDongSignguCd="110",
            lclsSystm1="AC",
            lclsSystm2="AC01",
            lclsSystm3="AC01010100",
            firstimage="https://example.com/gyeongbokgung.jpg",
            firstimage2="https://example.com/gyeongbokgung-thumb.jpg",
            cpyrhtDivCd="Type1",
            createdtime="20080904090852",
            modifiedtime="20250115110000",
        )
        gyeonggi_location = Location(
            contentid="999001",
            contenttypeid="12",
            region="경기",
            title="수원화성",
            addr1="경기도 수원시 팔달구",
            addr2="",
            tel="",
            mapx=127.0180,
            mapy=37.2870,
            lDongRegnCd="41",
            lDongSignguCd="110",
            lclsSystm1="AC",
            lclsSystm2="AC01",
            lclsSystm3="AC01010100",
            firstimage="https://example.com/suwon.jpg",
            firstimage2="https://example.com/suwon-thumb.jpg",
            cpyrhtDivCd="Type1",
            createdtime="20200101000000",
            modifiedtime="20260101000000",
        )
        hidden_location = Location(
            contentid="999002",
            contenttypeid="12",
            region="경기",
            title="이미지 없는 장소",
            addr1="경기도 테스트시",
            firstimage="",
            firstimage2="",
        )
        db.add_all([post, seoul_location, gyeonggi_location, hidden_location])
        db.commit()
    yield
    Base.metadata.drop_all(engine)
    Path("test_localhub.db").unlink(missing_ok=True)
    shutil.rmtree("test_uploads", ignore_errors=True)


@pytest.fixture()
def client():
    with TestClient(app) as value:
        yield value
