# routes/blog.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from db import get_database
from datetime import datetime

router = APIRouter(prefix="/blog", tags=["blog"])


@router.get("/", response_class=HTMLResponse)
async def blog_list(request: Request):
    db = get_database()
    posts_coll = db["posts"]
    cursor = posts_coll.find({"status": "published"}
                             ).sort("published_date", -1)
    posts = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        pd = doc.get("published_date")
        if isinstance(pd, datetime):
            doc["published_date"] = pd.isoformat()
        posts.append(doc)

    try:
        from main import templates  # type: ignore
        return templates.TemplateResponse(
            "blog.html",
            {"request": request, "posts": posts,
                "page_title": "Blog - Manosay", "active_page": "blog"},
        )
    except Exception:
        templates = Jinja2Templates(directory="templates")
        return templates.TemplateResponse(
            "blog.html",
            {"request": request, "posts": posts,
                "page_title": "Blog - Manosay", "active_page": "blog"},
        )


@router.get("/{slug}", response_class=HTMLResponse)
async def blog_post(request: Request, slug: str):
    db = get_database()
    post = await db["posts"].find_one({"slug": slug, "status": "published"})
    if not post:
        return RedirectResponse("/blog")

    post["_id"] = str(post["_id"])
    pd = post.get("published_date")
    if isinstance(pd, datetime):
        post["published_date"] = pd.isoformat()

    try:
        from main import templates  # type: ignore
        return templates.TemplateResponse(
            "blog-post.html",
            {"request": request, "post": post,
                "page_title": f"{post['title']} - Manosay", "active_page": "blog"},
        )
    except Exception:
        templates = Jinja2Templates(directory="templates")
        return templates.TemplateResponse(
            "blog-post.html",
            {"request": request, "post": post,
                "page_title": f"{post['title']} - Manosay", "active_page": "blog"},
        )
