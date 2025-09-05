# list_routes.py
from main import app
for r in app.router.routes:
    p = getattr(r, "path", None)
    if p and p.startswith("/admin"):
        print(p, list(getattr(r, "methods", [])))
