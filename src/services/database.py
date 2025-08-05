from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Optional, List, Dict, Any
from ..config import settings
from ..models.quiz import QuizDocument
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.quizzes_collection: Optional[AsyncIOMotorCollection] = None

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.database = self.client.learning_platform
            self.quizzes_collection = self.database.quizzes
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def create_quiz(self, quiz_data: dict) -> str:
        result = await self.quizzes_collection.insert_one(quiz_data)
        return str(result.inserted_id)

    async def get_quiz(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        try:
            quiz = await self.quizzes_collection.find_one({"_id": ObjectId(quiz_id)})
            if quiz:
                quiz["_id"] = str(quiz["_id"])
            return quiz
        except Exception as e:
            logger.error(f"Error fetching quiz {quiz_id}: {e}")
            return None

    async def get_quizzes(
        self, 
        book_id: Optional[str] = None, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        filter_criteria = {}
        if book_id:
            filter_criteria["book_id"] = book_id

        cursor = self.quizzes_collection.find(filter_criteria).skip(offset).limit(limit)
        quizzes = []
        async for quiz in cursor:
            quiz["_id"] = str(quiz["_id"])
            quizzes.append(quiz)
        return quizzes

    async def delete_quiz(self, quiz_id: str) -> bool:
        from bson import ObjectId
        try:
            result = await self.quizzes_collection.delete_one({"_id": ObjectId(quiz_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting quiz {quiz_id}: {e}")
            return False

# Global database service instance
db_service = DatabaseService()