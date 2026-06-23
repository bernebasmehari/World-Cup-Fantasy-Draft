from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .models.team import Team
from .models.user import User
from .models.draftteam import DraftTeam
from .models.account import Account
from contextlib import asynccontextmanager
from .routes import teamsroute
from .routes import usersroute
from .routes import authroute
from .routes import syncroute


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
import os
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authroute.router)
app.include_router(teamsroute.router)
app.include_router(usersroute.router)
app.include_router(syncroute.router)

@app.get("/health")
def health_check():
    return {"status": "WorldDraft backend is running!"}