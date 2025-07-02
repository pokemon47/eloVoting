from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.routes.poll import router as poll_router
from app.routes.vote import router as vote_router
from app.routes.auth import router as auth_router

# App metadata
app = FastAPI(
    title="EloVote API",
    description="API for Elo-based fair voting system.",
    version="1.0.0"
)

# CORS setup (restrict to specific domains, but leave empty for now)
origins = []  # TODO: Add allowed origins here when frontend is ready
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging setup
logger = logging.getLogger("elovote")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("EloVote API is starting up...")
    yield
    logger.info("EloVote API is shutting down...")

app.router.lifespan_context = lifespan

# Include routers
app.include_router(poll_router)
app.include_router(vote_router)
app.include_router(auth_router) 