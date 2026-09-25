import os

port = os.environ.get("PORT", "8080")
bind = f"0.0.0.0:{port}"
worker_class = "uvicorn.workers.UvicornWorker"
wsgi_app = "backend_server:app"
workers = 1
timeout = 120
keepalive = 5
