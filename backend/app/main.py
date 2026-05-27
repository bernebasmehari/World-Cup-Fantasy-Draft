from fastapi import FastAPI
from .database import Base, engine
from .models.player import Player
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
	return {"status": "WorldDraft backend is running!"}