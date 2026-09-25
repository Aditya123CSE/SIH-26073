import uvicorn
from backend_server import app

application = app
app = app

if __name__ == "__main__":
    uvicorn.run("backend_server:app", host="0.0.0.0", port=8080)
