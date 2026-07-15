from __future__ import annotations

import json
from html import escape
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import CONTENT_TYPES
from ..services.location_service import require_location
from ..services.post_service import require_post

router = APIRouter(prefix="/share", tags=["share"])
settings = get_settings()


def _absolute_url(request: Request, value: str | None) -> str:
    if not value:
        return urljoin(str(request.base_url), "static/og-default.png")
    if value.startswith(("http://", "https://")):
        return value
    return urljoin(str(request.base_url), value.lstrip("/"))


def _summary(value: str, limit: int = 160) -> str:
    normalized = " ".join(value.split())
    return normalized if len(normalized) <= limit else normalized[: limit - 1].rstrip() + "…"


def _share_page(
    *,
    request: Request,
    title: str,
    description: str,
    image_url: str,
    destination_url: str,
) -> HTMLResponse:
    canonical_url = str(request.url)
    safe_title = escape(title, quote=True)
    safe_description = escape(description, quote=True)
    safe_image = escape(image_url, quote=True)
    safe_canonical = escape(canonical_url, quote=True)
    safe_destination = escape(destination_url, quote=True)
    destination_json = json.dumps(destination_url, ensure_ascii=False).replace("<", "\\u003c")

    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{safe_title}</title>
  <meta name="description" content="{safe_description}" />
  <meta name="robots" content="noindex,follow" />
  <link rel="canonical" href="{safe_canonical}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="LocalHub" />
  <meta property="og:locale" content="ko_KR" />
  <meta property="og:title" content="{safe_title}" />
  <meta property="og:description" content="{safe_description}" />
  <meta property="og:image" content="{safe_image}" />
  <meta property="og:url" content="{safe_canonical}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{safe_title}" />
  <meta name="twitter:description" content="{safe_description}" />
  <meta name="twitter:image" content="{safe_image}" />
  <meta http-equiv="refresh" content="1;url={safe_destination}" />
  <style>
    body {{ min-height: 100vh; margin: 0; display: grid; place-items: center; font-family: system-ui, sans-serif; background: #fff9f0; color: #2a2119; }}
    main {{ max-width: 560px; padding: 36px; text-align: center; }}
    a {{ color: #a86200; font-weight: 700; }}
  </style>
</head>
<body>
  <main>
    <h1>{safe_title}</h1>
    <p>{safe_description}</p>
    <p>LocalHub 상세 페이지로 이동합니다.</p>
    <a href="{safe_destination}">바로 이동</a>
  </main>
  <script>window.setTimeout(function () {{ window.location.replace({destination_json}); }}, 100);</script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/posts/{post_id}", response_class=HTMLResponse)
def share_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    post = require_post(db, post_id)
    destination = f"{settings.frontend_public_url.rstrip('/')}/posts/{post.id}"
    image = post.images[0].image_url if post.images else None
    region_label = " ".join(part for part in (post.region, post.district) if part)
    description = _summary(
        f"{region_label + ' · ' if region_label else ''}{post.content}",
    )
    return _share_page(
        request=request,
        title=f"{post.title} | LocalHub",
        description=description,
        image_url=_absolute_url(request, image),
        destination_url=destination,
    )


@router.get("/locations/{contentid}", response_class=HTMLResponse)
def share_location(contentid: str, request: Request, db: Session = Depends(get_db)):
    location = require_location(db, contentid)
    destination = f"{settings.frontend_public_url.rstrip('/')}/locations/{location.contentid}"
    category = CONTENT_TYPES.get(location.contenttypeid, "지역정보")
    description = _summary(
        " · ".join(
            part for part in (
                location.region,
                category,
                location.addr1 or "주소 미제공",
            ) if part
        )
    )
    return _share_page(
        request=request,
        title=f"{location.title} | LocalHub",
        description=description,
        image_url=_absolute_url(request, location.firstimage),
        destination_url=destination,
    )
