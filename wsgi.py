from backend_server import app

try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)
except Exception:
    application = app
