from fastapi import APIRouter
from app.api.v1.endpoints import health, analyze, analyses, interview, tracker

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(analyze.router, tags=["Analysis"])
api_router.include_router(analyses.router, tags=["Database Analyses"])
api_router.include_router(interview.router, tags=["Interview Mode"])
api_router.include_router(tracker.router, tags=["Progress Tracker"])


