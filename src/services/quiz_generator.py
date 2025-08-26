import time
import logging
import requests
from typing import Dict, Any
from ..models.quiz import Quiz
from ..models.requests import QuizGenerationRequest, QuizGenerationResponse
from .ai_client import ai_service
from .database import db_service
from ..config import settings

logger = logging.getLogger(__name__)

class QuizGeneratorService:
    def __init__(self):
        pass

    async def _fetch_document_content(self, document_id: str) -> str:
        """Fetch document content from content-processor API"""
        try:
            url = f"{settings.content_processor_api_url}{document_id}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            document_data = response.json()
            content = document_data.get("content")
            
            if not content:
                raise ValueError(f"Document {document_id} has no content")
            
            logger.info(f"Successfully fetched content for document {document_id}")
            return content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch document {document_id} from content-processor: {e}")
            raise ValueError(f"Failed to retrieve document content: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing document content for {document_id}: {e}")
            raise ValueError(f"Error processing document content: {str(e)}")

    async def generate_quiz(self, request: QuizGenerationRequest) -> QuizGenerationResponse:
        start_time = time.time()
        
        try:
            logger.info(f"Starting quiz generation for book_id: {request.book_id}")
            
            # Get content - either from request or fetch from content-processor API
            content = request.content
            if not content:
                logger.info(f"Content not provided, fetching from content-processor for document: {request.book_id}")
                content = await self._fetch_document_content(request.book_id)
            
            # Validate content length
            if len(content) < 100:
                raise ValueError("Content must be at least 100 characters long")
            
            # Generate questions using AI
            questions = await ai_service.generate_quiz_questions(
                content=content,
                options=request.options
            )
            
            # Create quiz object
            quiz = Quiz(
                book_id=request.book_id,
                questions=questions,
                ai_model=settings.default_ai_model,
                generation_prompt="Quiz generated from book content",
                metadata=request.metadata
            )
            
            # Convert to dict for database storage
            quiz_dict = quiz.model_dump()
            
            # Save to database
            quiz_id = await db_service.create_quiz(quiz_dict)
            
            generation_time = time.time() - start_time
            
            logger.info(f"Quiz generation completed. Quiz ID: {quiz_id}, Time: {generation_time:.2f}s")
            
            return QuizGenerationResponse(
                quiz_id=quiz_id,
                questions_count=len(questions),
                generation_time_seconds=round(generation_time, 2),
                ai_model_used=settings.default_ai_model
            )
            
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            raise

    async def get_quiz(self, quiz_id: str) -> Dict[str, Any]:
        try:
            quiz_data = await db_service.get_quiz(quiz_id)
            if not quiz_data:
                raise ValueError(f"Quiz with ID {quiz_id} not found")
            return quiz_data
        except Exception as e:
            logger.error(f"Error retrieving quiz {quiz_id}: {e}")
            raise

    async def list_quizzes(
        self, 
        book_id: str = None, 
        limit: int = 10, 
        offset: int = 0
    ) -> Dict[str, Any]:
        try:
            quizzes = await db_service.get_quizzes(book_id, limit, offset)
            return {
                "quizzes": quizzes,
                "count": len(quizzes),
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            logger.error(f"Error listing quizzes: {e}")
            raise

    async def delete_quiz(self, quiz_id: str) -> bool:
        try:
            success = await db_service.delete_quiz(quiz_id)
            if success:
                logger.info(f"Quiz {quiz_id} deleted successfully")
            else:
                logger.warning(f"Quiz {quiz_id} not found for deletion")
            return success
        except Exception as e:
            logger.error(f"Error deleting quiz {quiz_id}: {e}")
            raise

# Global quiz generator service instance
quiz_service = QuizGeneratorService()