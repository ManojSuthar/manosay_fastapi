# routes/admin_web.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from bson import ObjectId
from datetime import datetime
import re
import logging
from pymongo.errors import DuplicateKeyError
# add near other imports
from fastapi import UploadFile, File, HTTPException
import aiofiles
from uuid import uuid4
from pathlib import Path


from db import get_database

logger = logging.getLogger(__name__)
router = APIRouter()  # routes: /admin/login, /admin/logout, /admin/create-post


def get_templates(request: Request) -> Jinja2Templates:
    """
    Resolve the Jinja2Templates instance used by the main app.
    Priority:
      1) try import main.templates
      2) try request.app.state.templates
      3) create a local Jinja2Templates(directory='templates')
    """
    try:
        # If main.py defines `templates` at module level, use it
        from main import templates as main_templates  # type: ignore
        return main_templates
    except Exception:
        pass

    try:
        t = getattr(request.app.state, "templates", None)
        if t is not None:
            return t
    except Exception:
        pass

    # Fallback: create a new templates object (works but may duplicate config)
    return Jinja2Templates(directory="templates")


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """
    Render admin login page. If already logged in, redirect to dashboard.
    """
    if request.cookies.get("admin_user_id"):
        return RedirectResponse(url="/admin/dashboard")
    templates = get_templates(request)
    return templates.TemplateResponse("admin_login.html", {"request": request})


@router.get("/admin/logout")
def admin_logout():
    """
    Clear admin cookie and redirect to home.
    """
    resp = RedirectResponse(url="/")
    resp.delete_cookie("admin_user_id", path="/")
    return resp


def make_slug(s: str) -> str:
    slug = s.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug).strip("-")
    return slug[:120]


# @router.post("/admin/create-post")
# async def admin_create_post(
#     request: Request,
#     title: str = Form(...),
#     content: str = Form(...),
#     slug: Optional[str] = Form(None),
#     image: Optional[str] = Form(None),
#     tags: Optional[str] = Form(None),
# ):
#     """
#     Handle blog post creation from admin dashboard form.
#     Verifies admin via cookie and inserts into `posts` collection.
#     """
#     admin_user_id = request.cookies.get("admin_user_id")
#     if not admin_user_id:
#         return RedirectResponse("/admin/login")

#     db = get_database()
#     users = db["users"]
#     try:
#         admin_user = await users.find_one({"_id": ObjectId(admin_user_id)})
#     except Exception as e:
#         logger.exception("Invalid admin_user_id cookie: %s", e)
#         return RedirectResponse("/admin/login")

#     if not admin_user or admin_user.get("role", "").lower() != "admin":
#         return RedirectResponse("/admin/login")

#     final_slug = slug or make_slug(title)
#     tags_list = [t.strip() for t in tags.split(",")] if tags else []

#     post_doc = {
#         "title": title,
#         "slug": final_slug,
#         "excerpt": (content[:160] + "...") if len(content) > 160 else content,
#         "content": content,
#         "author": admin_user.get("name") or admin_user.get("email"),
#         "published_date": datetime.utcnow(),
#         "image": image or "",
#         "tags": tags_list,
#         "status": "published",
#     }

#     posts = db["posts"]
#     result = await posts.insert_one(post_doc)
#     inserted_id = str(result.inserted_id)
#     logger.info("Admin %s created post %s (%s)",
#                 admin_user.get("email"), title, inserted_id)

#     # Redirect back to dashboard (could redirect to post page instead)
#     return RedirectResponse(url="/admin/dashboard", status_code=302)


@router.post("/admin/upload-image")
async def admin_upload_image(request: Request, file: UploadFile = File(...)):
    """
    Accepts an uploaded image file from admin, saves it to static/uploads/,
    and returns JSON with the public URL: {"url": "/static/uploads/..."}

    Requires admin cookie (same auth check as other admin endpoints).
    """
    # --- simple admin check (reuse same cookie logic) ---
    admin_user_id = request.cookies.get("admin_user_id")
    if not admin_user_id:
        # unauthorized for uploads
        raise HTTPException(status_code=401, detail="Not authenticated")

    # You may optionally verify admin_user exists/role here (like in create-post)
    # Basic file validation
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Limit file size (rough check: you can also stream and check length)
    MAX_BYTES = 5 * 1024 * 1024  # 5 MB
    # Read first chunk to ensure not empty and check size while streaming
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 5MB)")

    # Validate content type (basic)
    allowed = ("image/jpeg", "image/png", "image/gif", "image/webp")
    if file.content_type not in allowed:
        # Be permissive if you want, but better to allow common image types only
        raise HTTPException(status_code=400, detail="Unsupported image type")

    # Ensure uploads directory exists inside your static folder
    uploads_dir = Path("static") / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Make a unique filename
    extension = Path(file.filename).suffix or {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp"
    }.get(file.content_type, "")
    filename = f"{uuid4().hex}{extension}"
    dest_path = uploads_dir / filename

    # Write file to disk
    try:
        async with aiofiles.open(dest_path, "wb") as f:
            await f.write(contents)
    except Exception as e:
        logger.exception("Failed to save uploaded image: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Public URL (since main mounts /static -> static/)
    public_url = f"/static/uploads/{filename}"
    return {"url": public_url}


@router.post("/admin/create-post")
async def admin_create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    slug: Optional[str] = Form(None),
    image: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
):
    """
    Handle blog post creation from admin dashboard form.
    Verifies admin via cookie and inserts into `posts` collection.
    Ensures slug uniqueness by appending numeric suffixes on DuplicateKeyError.
    """
    admin_user_id = request.cookies.get("admin_user_id")
    if not admin_user_id:
        return RedirectResponse("/admin/login")

    db = get_database()
    users = db["users"]
    try:
        admin_user = await users.find_one({"_id": ObjectId(admin_user_id)})
    except Exception as e:
        logger.exception("Invalid admin_user_id cookie: %s", e)
        return RedirectResponse("/admin/login")

    if not admin_user or admin_user.get("role", "").lower() != "admin":
        return RedirectResponse("/admin/login")

    final_slug = (slug or make_slug(title)).strip()
    # normalize tags and remove empties
    tags_list = [t.strip() for t in (tags or "").split(",") if t.strip()]

    post_doc = {
        "title": title.strip(),
        "slug": final_slug,
        "excerpt": (content[:160] + "...") if len(content) > 160 else content,
        "content": content,
        "author": admin_user.get("name") or admin_user.get("email"),
        # optional: store author_id for future ownership logic
        "author_id": ObjectId(admin_user_id),
        "published_date": datetime.utcnow(),
        "image": (image or "").strip(),
        "tags": tags_list,
        "status": "published",
    }

    posts = db["posts"]

    # Try insert; on DuplicateKeyError for slug, append -1, -2, ... until success
    max_attempts = 10
    attempt = 0
    base_slug = final_slug

    while True:
        try:
            result = await posts.insert_one(post_doc)
            inserted_id = str(result.inserted_id)
            logger.info("Admin %s created post %s (%s)",
                        admin_user.get("email"), title, inserted_id)
            return RedirectResponse(url="/admin/dashboard", status_code=302)
        except DuplicateKeyError as dke:
            # If duplicate slug, make a new candidate slug
            attempt += 1
            if attempt > max_attempts:
                logger.exception(
                    "Could not generate unique slug after %d attempts: %s", max_attempts, dke)
                templates = get_templates(request)
                return templates.TemplateResponse(
                    "admin_dashboard.html",
                    {"request": request, "error": "Could not create post — slug conflict. Try a different title or slug."},
                )
            # Append suffix: base-slug, base-slug-1, base-slug-2, ...
            new_slug = f"{base_slug}-{attempt}"
            post_doc["slug"] = new_slug
            logger.info("Slug duplicate, retrying with slug=%s", new_slug)
            # loop will retry insert
        except Exception as e:
            logger.exception("Error inserting post: %s", e)
            templates = get_templates(request)
            return templates.TemplateResponse(
                "admin_dashboard.html",
                {"request": request,
                    "error": "Could not save post. Please try again later."},
            )
