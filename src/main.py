from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import List, Optional

from .config import settings
from .models.requests import QuizGenerationRequest, QuizGenerationResponse, ErrorResponse
from .models.quiz import QuizDocument
from .services.database import db_service
from .services.quiz_generator import quiz_service
from .utils.logger import setup_logging
from .utils.exceptions import QuizGenerationError, QuizNotFoundError

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.service_name} service")
    await db_service.connect()
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.service_name} service")
    await db_service.disconnect()

app = FastAPI(
    title="Learning Platform Quiz Generator",
    description="Microservice for generating quizzes from content using AI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate-quiz", response_model=QuizGenerationResponse)
async def generate_quiz(request: QuizGenerationRequest):
    try:
        logger.info(f"Received quiz generation request for book_id: {request.book_id}")
        response = await quiz_service.generate_quiz(request)
        return response
    except ValueError as e:
        logger.warning(f"Validation error generating quiz: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quizzes/{quiz_id}", response_model=QuizDocument)
async def get_quiz(quiz_id: str):
    try:
        quiz_data = await quiz_service.get_quiz(quiz_id)
        return quiz_data
    except ValueError as e:
        logger.warning(f"Quiz not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quizzes", response_model=dict)
async def list_quizzes(
    book_id: Optional[str] = Query(None, description="Filter by book ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of quizzes to return"),
    offset: int = Query(0, ge=0, description="Number of quizzes to skip")
):
    try:
        result = await quiz_service.list_quizzes(book_id, limit, offset)
        return result
    except Exception as e:
        logger.error(f"Error listing quizzes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/quizzes/{quiz_id}")
async def delete_quiz(quiz_id: str):
    try:
        success = await quiz_service.delete_quiz(quiz_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Quiz with ID {quiz_id} not found")
        return {"message": f"Quiz {quiz_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    try:
        # Test database connection
        await db_service.client.admin.command('ping')
        return {
            "status": "healthy",
            "service": settings.service_name,
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": settings.service_name,
            "version": "1.0.0",
            "database": "disconnected",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)