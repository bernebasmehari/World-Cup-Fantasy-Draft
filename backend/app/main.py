from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .models.player import Player
from .models.user import User
from .models.draftplayers import DraftPlayer
from contextlib import asynccontextmanager
from .routes import playersroute
from .routes import usersroute




@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts up
    # Creates all database tables that don't exist yet
    Base.metadata.create_all(bind=engine)
    yield  # everything after yield runs on shutdown


app = FastAPI(lifespan=lifespan)

# Middleware sits between the browser and your routes
# It intercepts every request before it hits your code
# CORSMiddleware specifically handles the browser's cross-origin security check
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # only allow requests from your React app
    allow_methods=["*"],   # allow all HTTP methods (GET, POST, PUT, DELETE...)
    allow_headers=["*"],   # allow all headers in the request
)

# Register the players& users routers — all routes defined in playersroute.py and usersroute.py are now active
app.include_router(playersroute.router)
app.include_router(usersroute.router)

@app.get("/health")
def health_check():
    return {"status": "WorldDraft backend is running!"}