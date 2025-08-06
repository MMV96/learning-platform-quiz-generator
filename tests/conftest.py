import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.main import app
from src.services.database import db_service
from src.services.ai_client import ai_service
from src.services.quiz_generator import quiz_service


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db_service():
    mock_service = AsyncMock()
    mock_service.client = MagicMock()
    mock_service.database = MagicMock()
    mock_service.quizzes_collection = MagicMock()
    return mock_service


@pytest.fixture
def mock_ai_service():
    mock_service = AsyncMock()
    mock_service.client = MagicMock()
    return mock_service


@pytest.fixture
def sample_quiz_data():
    return {
        "_id": "507f1f77bcf86cd799439011",
        "book_id": "test-book-123",
        "questions": [
            {
                "question": "What is the capital of Italy?",
                "type": "multiple_choice",
                "correct_answer": "Rome",
                "options": ["Rome", "Milan", "Naples", "Venice"],
                "explanation": "Rome is the capital and largest city of Italy.",
                "difficulty": "easy",
                "topic": "Geography",
                "concepts_tested": ["Italian cities", "European capitals"]
            }
        ],
        "created_at": "2024-01-01T00:00:00.000Z",
        "ai_model": "claude-3-sonnet-20240229",
        "generation_prompt": "Quiz generated from book content",
        "metadata": {"chapter": "1"}
    }


@pytest.fixture
def sample_quiz_request():
    return {
        "content": "Rome is the capital of Italy and its largest city by inhabitants. It is located in the central-western portion of the Italian Peninsula.",
        "book_id": "test-book-123",
        "metadata": {"chapter": "1"},
        "options": {
            "num_questions": 1,
            "difficulty_distribution": {"easy": 1.0},
            "question_types": ["multiple_choice"],
            "language": "en"
        }
    }