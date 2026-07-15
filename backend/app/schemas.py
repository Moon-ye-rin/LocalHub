from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator

T = TypeVar("T")

from .regions import is_valid_region_district


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None


class PostPayloadBase(BaseModel):
    category: str = Field(min_length=1, max_length=30)
    region: Literal["서울", "경기"]
    district: str = Field(min_length=1, max_length=30)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=20000)
    tags: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("category", "district", "title", "content")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("필수 입력값은 공백일 수 없습니다.")
        return value

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        result: list[str] = []
        for raw in values:
            tag = raw.strip().lstrip("#")[:30]
            if tag and tag.casefold() not in {item.casefold() for item in result}:
                result.append(tag)
        return result[:10]

    @model_validator(mode="after")
    def validate_region_district(self):
        if not is_valid_region_district(self.region, self.district):
            raise ValueError("선택한 지역과 세부 지역이 일치하지 않습니다.")
        return self


class PostCreate(PostPayloadBase):
    password: str = Field(min_length=4, max_length=100)


class PostUpdate(PostPayloadBase):
    password: str = Field(min_length=4, max_length=100)


class PasswordRequest(BaseModel):
    password: str = Field(min_length=1, max_length=100)


class PostSummary(BaseModel):
    id: int
    category: str
    region: str | None = None
    district: str | None = None
    title: str
    content: str
    view_count: int
    like_count: int
    comment_count: int = 0
    tags: list[str]
    created_at: str
    updated_at: str | None = None


class PostDetail(PostSummary):
    images: list[str] = Field(default_factory=list)
    liked: bool = False


class PostListData(BaseModel):
    posts: list[PostSummary]
    page: int
    size: int
    total_count: int
    total_pages: int


class CreatedId(BaseModel):
    id: int


class PasswordMatch(BaseModel):
    match: bool


class LikeData(BaseModel):
    like_count: int
    liked: bool
    already_liked: bool = False


class TagCount(BaseModel):
    name: str
    count: int


class TagListData(BaseModel):
    tags: list[TagCount]


class ImageData(BaseModel):
    image_url: str


class ImageDeleteRequest(PasswordRequest):
    image_url: str = Field(min_length=1, max_length=255)


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    password: str = Field(min_length=4, max_length=100)

    @field_validator("content")
    @classmethod
    def strip_comment(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("댓글 내용은 공백일 수 없습니다.")
        return value


class CommentUpdate(CommentCreate):
    pass


class CommentItem(BaseModel):
    id: int
    post_id: int
    content: str
    created_at: str
    updated_at: str | None = None


class CommentListData(BaseModel):
    comments: list[CommentItem]
    total_count: int


class LocationItem(BaseModel):
    contentid: str
    contenttypeid: str
    region: str
    title: str
    addr1: str | None = None
    addr2: str | None = None
    tel: str | None = None
    mapx: float | None = None
    mapy: float | None = None
    lDongRegnCd: str | None = None
    lDongSignguCd: str | None = None
    lclsSystm1: str | None = None
    lclsSystm2: str | None = None
    lclsSystm3: str | None = None
    firstimage: str | None = None
    firstimage2: str | None = None
    cpyrhtDivCd: str | None = None
    bookmarked: bool = False


class LocationDetail(LocationItem):
    zipcode: str | None = None
    mlevel: str | None = None
    areacode: str | None = None
    sigungucode: str | None = None
    cat1: str | None = None
    cat2: str | None = None
    cat3: str | None = None
    createdtime: str | None = None
    modifiedtime: str | None = None
    view_count: int = 0
    like_count: int = 0
    bookmark_count: int = 0
    comment_count: int = 0
    average_rating: float = 0
    rating_count: int = 0
    liked: bool = False
    bookmarked: bool = False
    nearby: list[LocationItem] = Field(default_factory=list)


class LocationCommentCreate(BaseModel):
    nickname: str = Field(default="", max_length=30)
    content: str = Field(min_length=1, max_length=1000)
    rating: int = Field(default=0, ge=0, le=5)
    password: str = Field(min_length=4, max_length=100)

    @field_validator("nickname")
    @classmethod
    def normalize_nickname(cls, value: str) -> str:
        value = value.strip()
        return value or "익명"

    @field_validator("content")
    @classmethod
    def normalize_location_comment(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("댓글 내용은 공백일 수 없습니다.")
        return value


class LocationCommentUpdate(LocationCommentCreate):
    pass


class LocationCommentItem(BaseModel):
    id: int
    contentid: str
    nickname: str
    content: str
    rating: int
    created_at: str
    updated_at: str | None = None


class LocationCommentListData(BaseModel):
    comments: list[LocationCommentItem]
    total_count: int
    average_rating: float
    rating_count: int


class LocationReactionData(BaseModel):
    count: int
    active: bool


class LocationListData(BaseModel):
    region: str
    items: list[LocationItem]
    page: int
    size: int
    total_count: int
    total_pages: int


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=20)
    language: Literal["ko", "en"] = "ko"


class ChatReference(BaseModel):
    type: Literal["location", "post"]
    id: str
    name: str


class ChatData(BaseModel):
    reply: str
    references: list[ChatReference] = Field(default_factory=list)
    mode: Literal["local", "openai"] = "local"
    source_notice: str = "출처: 한국관광공사 TourAPI 4.0 · 공공누리 제3유형"


class DashboardSeries(BaseModel):
    name: str
    data: list[int]


class MonthlyCategoryData(BaseModel):
    labels: list[str]
    series: list[DashboardSeries]


class CategorySlice(BaseModel):
    label: str
    count: int


class CategoryDistributionData(BaseModel):
    total: list[CategorySlice]
    seoul: list[CategorySlice]
    gyeonggi: list[CategorySlice]


class PopularRegionItem(BaseModel):
    region: str
    district: str
    label: str
    score: int
    post_count: int
    comment_count: int
    like_count: int
    view_count: int


class WeeklyTrendData(BaseModel):
    labels: list[str]
    views: list[int]
    likes: list[int]


class PopularLocationItem(BaseModel):
    contentid: str
    title: str
    region: str
    firstimage: str | None = None
    score: int
    comment_count: int
    like_count: int
    view_count: int
    average_rating: float = 0
    rating_count: int = 0


class TopRatedLocationItem(BaseModel):
    contentid: str
    title: str
    region: str
    firstimage: str | None = None
    average_rating: float
    rating_count: int
    comment_count: int


class DashboardData(BaseModel):
    monthly_category: MonthlyCategoryData
    category_distribution: CategoryDistributionData
    popular_regions: list[PopularRegionItem]
    popular_locations: list[PopularLocationItem]
    top_rated_locations: list[TopRatedLocationItem]
    weekly_trend: WeeklyTrendData
    score_formula: str = "(댓글 수 × 3) + (좋아요 수 × 2) + 조회 수"
