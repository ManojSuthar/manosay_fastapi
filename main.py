import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

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

# Pydantic model for contact form


class ContactForm(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str


# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "manojmottyar@gmail.com")


load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "manojmottyar@gmail.com")

logger = logging.getLogger(__name__)

# Sample blog data
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


async def send_contact_email(form_data):
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


# Home route
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
        "recent_posts": BLOG_POSTS[:3],  # Show 3 recent posts on homepage
        "page_title": "Home - Manosay",
        "active_page": "home"
    }

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
        ]
    }

    return templates.TemplateResponse("index.html", context)


# Blog page - List all posts
@app.get("/blog", response_class=HTMLResponse)
async def blog_list(request: Request):
    context = {
        "request": request,
        "posts": BLOG_POSTS,
        "page_title": "Blog - Manosay",
        "active_page": "blog"
    }
    return templates.TemplateResponse("blog.html", context)


# Individual blog post
# @app.get("/blog/{slug}", response_class=HTMLResponse)
# async def blog_post(request: Request, slug: str):
#     post = next((p for p in BLOG_POSTS if p["slug"] == slug), None)
#     if not post:
#         return RedirectResponse("/blog")

#     context = {
#         "request": request,
#         "post": post,
#         "page_title": f"{post['title']} - Manosay Blog"
#     }
#     return templates.TemplateResponse("blog-post.html", context)

@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_post(request: Request, slug: str):
    post = next((p for p in BLOG_POSTS if p["slug"] == slug), None)
    if not post:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/blog")
    context = {"request": request, "post": post,
               "page_title": f"{post['title']} - Manosay", "active_page": "blog"}
    return templates.TemplateResponse("blog-post.html", context)

# Privacy Policy page


@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    context = {"request": request,
               "page_title": "Privacy Policy - Manosay", "active_page": ""}
    return templates.TemplateResponse("privacy-policy.html", context)


# API endpoint for contact form
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
        raise HTTPException(
            status_code=500,
            detail=f"Error sending message: {str(e)}"
        )

# Health check endpoint


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Manosay API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
