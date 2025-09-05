# main.py
import os
import logging
import asyncio
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, EmailStr

# Email
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# security / db utils
import bcrypt
from bson import ObjectId

# Import db helpers (Motor async)
from db import (
    get_database,
    connect_to_mongo,
    close_mongo_connection,
    ensure_indexes,
    ping_db,
)

# Optional route modules (if present)
# We'll include them below using try/except to keep app startup resilient.
# from routes.auth import router as auth_router
# from routes.admin import router as admin

# Load environment variables
load_dotenv()

# App & logging
app = FastAPI(title="ManoSay")
logger = logging.getLogger(__name__)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "https://manosay.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (CSS, JS, Images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates folder
templates = Jinja2Templates(directory="templates")

# Include routers if they exist
try:
    from routes import auth
    app.include_router(auth.router)
except ImportError:
    logger.info("Auth routes not found")

try:
    from routes.admin_web import router as admin_web_router
    app.include_router(admin_web_router)
except ImportError:
    logger.info("admin_web routes not found")

try:
    from routes import admin as admin_routes
    app.include_router(admin_routes.router)
except ImportError:
    logger.info("Admin routes not found")

try:
    from routes import blog
    app.include_router(blog.router)
except ImportError:
    logger.info("Blog routes not found")

try:
    from routes import leads
    app.include_router(leads.router)
except ImportError:
    logger.info("Leads routes not found")

# ------------------------------------------------------------------------
# Startup / Shutdown - MongoDB integration (Motor)
# ------------------------------------------------------------------------


@app.on_event("startup")
async def startup_event():
    # Initialize Motor client and database
    try:
        await connect_to_mongo()
    except Exception:
        logger.exception("Failed to connect to MongoDB during startup")
        # Optionally: raise to prevent app from starting if DB mandatory
        # raise

    # Ensure indexes (optional, idempotent). Errors shouldn't stop startup.
    try:
        await ensure_indexes()
    except Exception:
        logger.exception("ensure_indexes() failed during startup")


@app.on_event("shutdown")
def shutdown_event():
    try:
        close_mongo_connection()
    except Exception:
        logger.exception("Error while closing MongoDB connection on shutdown")


# ------------------------------------------------------------------------
# Pydantic models & configuration
# ------------------------------------------------------------------------
class ContactForm(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str


SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "manojmottyar@gmail.com")


# ------------------------------------------------------------------------
# Sample blog data (unchanged)
# ------------------------------------------------------------------------
BLOG_POSTS = [
    {
        "id": 1,
        "title": "Getting Started with Flutter Web Development",
        "slug": "getting-started-with-flutter-web",
        "excerpt": "Learn how to build responsive web applications using Flutter framework.",
        "content": """
        <h2>Introduction to Flutter Web</h2>
        <p>Flutter is Google's UI toolkit for building natively compiled applications for mobile, web, and desktop from a single codebase.</p>
        
        <h3>Why Choose Flutter for Web?</h3>
        <p>Flutter for web allows you to compile existing Flutter code written in Dart into a client experience that can be embedded in the browser and deployed to any web server.</p>
        
        <h3>Key Features</h3>
        <ul>
            <li>Single codebase for multiple platforms</li>
            <li>Hot reload for rapid development</li>
            <li>Rich set of customizable widgets</li>
            <li>Excellent performance characteristics</li>
        </ul>
        """,
        "author": "Manosay Team",
        "published_date": "2023-10-15",
        "image": "https://images.unsplash.com/photo-1527474305487-b87b222841cc?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=80",
        "tags": ["Flutter", "Web Development", "Dart"]
    },
    {
        "id": 2,
        "title": "Building Responsive UIs with Flutter",
        "slug": "building-responsive-uis-with-flutter",
        "excerpt": "Discover best practices for creating responsive user interfaces that work across all devices.",
        "content": """
        <h2>Understanding Responsive Design</h2>
        <p>Responsive design ensures that your application looks good and functions well on all screen sizes, from mobile phones to desktop computers.</p>
        
        <h3>Flutter Layout Widgets</h3>
        <p>Flutter provides several widgets to help build responsive layouts:</p>
        <ul>
            <li>MediaQuery - for accessing screen dimensions</li>
            <li>LayoutBuilder - for building responsive layouts</li>
            <li>Flexible and Expanded - for flexible UIs</li>
            <li>AspectRatio - for maintaining aspect ratios</li>
        </ul>
        
        <h3>Best Practices</h3>
        <p>Always test your application on multiple screen sizes and use breakpoints to adjust your layout for different devices.</p>
        """,
        "author": "Manosay Team",
        "published_date": "2023-10-10",
        "image": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=80",
        "tags": ["Flutter", "UI/UX", "Responsive Design"]
    },
    {
        "id": 3,
        "title": "State Management in Flutter Applications",
        "slug": "state-management-in-flutter",
        "excerpt": "Explore different state management approaches for Flutter applications.",
        "content": """
        <h2>What is State Management?</h2>
        <p>State management refers to how you manage and share the state (data) of your application between different widgets and components.</p>
        
        <h3>Popular State Management Solutions</h3>
        <ul>
            <li>Provider - Recommended by Flutter team</li>
            <li>Bloc - Business Logic Component pattern</li>
            <li>Riverpod - Provider's successor</li>
            <li>GetX - Lightweight solution</li>
            <li>Redux - Familiar to web developers</li>
        </ul>
        
        <h3>Choosing the Right Approach</h3>
        <p>The best state management solution depends on your project's complexity, team experience, and specific requirements.</p>
        """,
        "author": "Manosay Team",
        "published_date": "2023-10-05",
        "image": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=80",
        "tags": ["Flutter", "State Management", "Dart"]
    }
]

# ------------------------------------------------------------------------
# Email sending helper
# ------------------------------------------------------------------------


async def send_contact_email(form_data: ContactForm):
    """Send email from contact form (standalone function)."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = f"New Contact Form: {form_data.subject}"

        body = (
            f"New contact form submission from Manosay website:\n\n"
            f"Name: {form_data.name}\n"
            f"Email: {form_data.email}\n"
            f"Subject: {form_data.subject}\n\n"
            f"Message:\n{form_data.message}\n\n"
            f"---\nThis email was sent from the Manosay contact form."
        )
        msg.attach(MIMEText(body, "plain"))

        # Use STARTTLS for port 587
        await aiosmtplib.send(
            msg,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            start_tls=(SMTP_PORT == 587),
            use_tls=(SMTP_PORT == 465),
            timeout=30,
        )

        return True

    except Exception as e:
        logger.exception("Error sending email")
        # re-raise so FastAPI returns 500 with message
        raise

# ------------------------------------------------------------------------
# Routes (views + api)
# ------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    projects = [
        {
            'title': 'DailyNews24',
            'desc': 'The DailyNews24 app is a comprehensive and user-friendly news platform that delivers fast and accurate updates across a wide range of categories — including national and international news, entertainment, politics, sports, business, lifestyle, and more.',
            'link': 'https://apps.apple.com/in/app/dailynews24/id6744032665',
            'image': 'https://images.unsplash.com/photo-1588681664899-f142ff2dc9b1?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=400&q=80'
        },
        {
            'title': 'YLogLite',
            'desc': 'Real-time tracking with BLE, designed for seamless communication and vehicle tracking.',
            'link': 'https://play.google.com/store/apps/details?id=com.yloglite.activity&hl=en-I',
            'image': 'https://images.unsplash.com/photo-1563014959-7aaa83350992?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=400&q=80'
        },
        {
            'title': 'YLogForms',
            'desc': 'Innovative solution for feeding routine data in an electronic form with ease.',
            'link': 'https://play.google.com/store/apps/details?id=com.yusata.ylogforms&hl=en-IN',
            'image': 'https://images.unsplash.com/photo-1581291518633-83b4ebd1d83e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=400&q=80'
        },
        {
            'title': 'YLog365',
            'desc': 'Smart functions for real-time tracking with easy-to-use tracking interface.',
            'link': 'https://play.google.com/store/apps/details?id=com.app.ylog365&hl=en-IN',
            'image': 'https://images.unsplash.com/photo-1616007736933-54d2525a2c19?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=400&q=80'
        },
        {
            'title': 'ShootCx',
            'desc': 'SHOOT helps you with an affordable, quick and convenient Party Store, Grocery, Liquor, Lunch, Dinner and many more deliveries.',
            'link': 'https://play.google.com/store/apps/details?id=com.SHOOTCxnew.customer',
            'image': 'https://images.unsplash.com/photo-1607083206968-13611e3d76db?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=400&q=80'
        },
        {
            'title': 'MiniManager',
            'desc': 'App for PVS deliveries management, simplifying logistics and delivery tracking.',
            'link': 'https://play.google.com/store/apps/details?id=com.minimanager&hl=en',
            'image': 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=400&q=80'
        },
        {
            'title': 'Clinic Seeker',
            'desc': 'Helps you find healthcare facilities near you in Canada, with real-time waiting times.',
            'link': 'https://apkpure.com/clinic-seeker-is-no-longer-available-july-2019/dynaweb.clinicseeker',
            'image': 'https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=400&q=80'
        },
    ]

    # Pass all necessary data to template
    context = {
        "request": request,
        "projects": projects,
        "features": [
            {"title": "Fast Performance", "icon": "rocket",
                "desc": "Optimized for speed and performance"},
            {"title": "Fully Responsive", "icon": "mobile-alt",
                "desc": "Looks great on any device"},
            {"title": "Secure & Safe", "icon": "lock",
                "desc": "Built with security in mind"}
        ],
        "services": [
            {"title": "Web Design", "icon": "paint-brush",
                "desc": "Beautiful, modern website designs"},
            {"title": "Web Development", "icon": "code",
                "desc": "Custom web development solutions"},
            {"title": "E-commerce Solutions", "icon": "shopping-cart",
                "desc": "Complete online store development"},
            {"title": "SEO Optimization", "icon": "search",
                "desc": "Improve your website's visibility"},
            {"title": "Digital Marketing", "icon": "chart-line",
                "desc": "Data-driven marketing campaigns"},
            {"title": "Cloud Hosting", "icon": "cloud",
                "desc": "Reliable, scalable cloud hosting"}
        ],
        "recent_posts": BLOG_POSTS[:3],
        "page_title": "Home - Manosay",
        "active_page": "home"
    }

    return templates.TemplateResponse("index.html", context)


# # Blog list
# @app.get("/blog", response_class=HTMLResponse)
# async def blog_list(request: Request):
#     context = {
#         "request": request,
#         "posts": BLOG_POSTS,
#         "page_title": "Blog - Manosay",
#         "active_page": "blog"
#     }
#     return templates.TemplateResponse("blog.html", context)


# # Single blog post
# @app.get("/blog/{slug}", response_class=HTMLResponse)
# async def blog_post(request: Request, slug: str):
#     post = next((p for p in BLOG_POSTS if p["slug"] == slug), None)
#     if not post:
#         return RedirectResponse("/blog")
#     context = {"request": request, "post": post,
#                "page_title": f"{post['title']} - Manosay", "active_page": "blog"}
#     return templates.TemplateResponse("blog-post.html", context)


# Blog list - load from DB
@app.get("/blog", response_class=HTMLResponse)
async def blog_list(request: Request):
    db = get_database()
    posts_coll = db["posts"]
    cursor = posts_coll.find({"status": "published"}
                             ).sort("published_date", -1)
    posts = []
    async for doc in cursor:
        # convert _id and datetime for templates
        doc["_id"] = str(doc["_id"])
        pd = doc.get("published_date")
        if pd is not None:
            try:
                # Motor returns datetime objects already; convert to ISO for template display
                doc["published_date"] = pd.isoformat()
            except Exception:
                pass
        # ensure required fields exist to avoid template errors
        doc.setdefault("excerpt", "")
        doc.setdefault("author", "")
        doc.setdefault("image", "")
        doc.setdefault("tags", [])
        posts.append(doc)

    return templates.TemplateResponse("blog.html", {"request": request, "posts": posts, "page_title": "Blog - Manosay", "active_page": "blog"})


# Single blog post - load from DB by slug
@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_post(request: Request, slug: str):
    db = get_database()
    post = await db["posts"].find_one({"slug": slug, "status": "published"})
    if not post:
        # if not found, redirect to blog list
        return RedirectResponse("/blog")
    # normalize for template
    post["_id"] = str(post["_id"])
    pd = post.get("published_date")
    if pd is not None:
        try:
            post["published_date"] = pd.isoformat()
        except Exception:
            pass
    # Ensure fields exist
    post.setdefault("content", "")
    post.setdefault("excerpt", "")
    post.setdefault("author", "")
    post.setdefault("image", "")
    post.setdefault("tags", [])

    return templates.TemplateResponse("blog-post.html", {"request": request, "post": post, "page_title": f"{post.get('title','Post')} - Manosay", "active_page": "blog"})


# Privacy policy
@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    context = {"request": request,
               "page_title": "Privacy Policy - Manosay", "active_page": ""}
    return templates.TemplateResponse("privacy-policy.html", context)


# Ensure GET /admin/login exists and renders login page
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    # If already logged in redirect to dashboard
    if request.cookies.get("admin_user_id"):
        return RedirectResponse(url="/admin/dashboard")
    return templates.TemplateResponse("admin_login.html", {"request": request})


# Admin login (POST) - async with Motor
@app.post("/admin/login")
async def admin_login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    db = get_database()
    users = db["users"]

    # Motor find_one is async
    user = await users.find_one({"email": email})
    if not user:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid email or password"})

    # Role check
    if user.get("role", "").lower() != "admin":
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Not authorized"})

    # Normalize stored password to bytes
    stored = user.get("password")
    stored_bytes = None
    try:
        from bson.binary import Binary as BsonBinary
        if isinstance(stored, (bytes, bytearray)):
            stored_bytes = bytes(stored)
        elif isinstance(stored, str):
            try:
                stored_bytes = stored.encode("utf-8")
            except Exception:
                stored_bytes = stored
        elif isinstance(stored, BsonBinary):
            stored_bytes = bytes(stored)
        else:
            stored_bytes = bytes(stored)
    except Exception as e:
        print("Error normalizing stored password:", e)
        stored_bytes = None

    if not stored_bytes:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Server error (pwd stored wrong)"})

    # Check password
    try:
        ok = bcrypt.checkpw(password.encode("utf-8"), stored_bytes)
    except Exception as e:
        print("bcrypt error:", e)
        ok = False

    if not ok:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid email or password"})

    # Success — set cookie and redirect
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(key="admin_user_id", value=str(
        user.get("_id")), httponly=True, max_age=60*60*24, path="/")
    return response


# Admin dashboard - async with Motor
# @app.get("/admin/dashboard")
# async def admin_dashboard(request: Request):
#     db = get_database()
#     users = db["users"]

#     admin_user_id = request.cookies.get("admin_user_id")
#     if not admin_user_id:
#         return RedirectResponse(url="/admin/login")

#     try:
#         user = await users.find_one({"_id": ObjectId(admin_user_id)})
#     except Exception as e:
#         print("Invalid admin_user_id cookie:", e)
#         user = None

#     if not user or user.get("role", "").lower() != "admin":
#         return RedirectResponse(url="/admin/login")

#     return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": {"email": user.get("email"), "name": user.get("name")}})


@app.get("/admin/dashboard")
async def admin_dashboard(request: Request):
    db = get_database()
    users = db["users"]

    admin_user_id = request.cookies.get("admin_user_id")
    if not admin_user_id:
        return RedirectResponse(url="/admin/login")

    try:
        user = await users.find_one({"_id": ObjectId(admin_user_id)})
    except Exception as e:
        print("Invalid admin_user_id cookie:", e)
        user = None

    if not user or user.get("role", "").lower() != "admin":
        return RedirectResponse(url="/admin/login")

    # fetch recent posts by this admin (optional: fetch all posts)
    posts_cursor = db["posts"].find(
        {"author_id": ObjectId(admin_user_id)}).sort("published_date", -1)
    posts = []
    async for p in posts_cursor:
        p["_id"] = str(p["_id"])
        pd = p.get("published_date")
        if isinstance(pd, datetime):
            p["published_date"] = pd.isoformat()
        posts.append(p)

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "user": {"email": user.get(
            "email"), "name": user.get("name")}, "posts": posts}
    )


# Contact API
@app.post("/api/contact")
async def submit_contact_form(form_data: ContactForm):
    try:
        # Send email
        await send_contact_email(form_data)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Thank you for your message! We will get back to you soon."
            }
        )
    except Exception as e:
        logger.exception("Contact form send error")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending message: {str(e)}"
        )


# Health check (DB-aware)
@app.get("/api/health")
async def health_check():
    db_ok = False
    try:
        db_ok = await ping_db()
    except Exception:
        db_ok = False

    status = "healthy" if db_ok else "degraded"
    return {"status": status, "service": "Manosay API", "db_connected": db_ok}


# Run local server (for `python main.py`)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
