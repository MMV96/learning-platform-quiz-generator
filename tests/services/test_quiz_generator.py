import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time

from src.services.quiz_generator import QuizGeneratorService
from src.models.quiz import Question, QuestionType, DifficultyLevel
from src.models.requests import QuizGenerationRequest, QuizOptions


class TestQuizGeneratorService:
    @pytest.fixture
    def quiz_service(self):
        return QuizGeneratorService()

    @pytest.fixture
    def sample_questions(self):
        return [
            Question(
                question="What is the capital of Italy?",
                type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="Rome",
                options=["Rome", "Milan", "Naples", "Venice"],
                explanation="Rome is the capital and largest city of Italy.",
                difficulty=DifficultyLevel.EASY,
                topic="Geography",
                concepts_tested=["Italian cities", "European capitals"]
            ),
            Question(
                question="Is Rome located in northern Italy?",
                type=QuestionType.BOOLEAN,
                correct_answer=False,
                explanation="Rome is located in central Italy, not northern Italy.",
                difficulty=DifficultyLevel.MEDIUM,
                topic="Geography",
                concepts_tested=["Italian geography"]
            )
        ]

    @pytest.fixture
    def sample_request(self):
        return QuizGenerationRequest(
            content="Rome is the capital of Italy and its largest city. It is located in the central-western portion of the Italian Peninsula.",
            book_id="test-book-123",
            metadata={"chapter": "1"},
            options=QuizOptions(num_questions=2)
        )

    @pytest.mark.asyncio
    async def test_generate_quiz_success(self, quiz_service, sample_request, sample_questions):
        # Mock dependencies
        with patch('src.services.quiz_generator.ai_service') as mock_ai_service, \
             patch('src.services.quiz_generator.db_service') as mock_db_service, \
             patch('src.services.quiz_generator.settings') as mock_settings:
            
            # Setup mocks
            mock_ai_service.generate_quiz_questions = AsyncMock(return_value=sample_questions)
            mock_db_service.create_quiz = AsyncMock(return_value="quiz-12345")
            mock_settings.default_ai_model = "claude-3-sonnet-20240229"
            
            # Execute
            response = await quiz_service.generate_quiz(sample_request)
            
            # Assertions
            assert response.quiz_id == "quiz-12345"
            assert response.questions_count == 2
            assert response.ai_model_used == "claude-3-sonnet-20240229"
            assert response.generation_time_seconds >= 0
            
            # Verify service calls
            mock_ai_service.generate_quiz_questions.assert_called_once_with(
                content=sample_request.content,
                options=sample_request.options
            )
            mock_db_service.create_quiz.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_quiz_ai_service_failure(self, quiz_service, sample_request):
        with patch('src.services.quiz_generator.ai_service') as mock_ai_service:
            mock_ai_service.generate_quiz_questions = AsyncMock(side_effect=Exception("AI service error"))
            
            with pytest.raises(Exception, match="AI service error"):
                await quiz_service.generate_quiz(sample_request)

    @pytest.mark.asyncio
    async def test_generate_quiz_database_failure(self, quiz_service, sample_request, sample_questions):
        with patch('src.services.quiz_generator.ai_service') as mock_ai_service, \
             patch('src.services.quiz_generator.db_service') as mock_db_service:
            
            mock_ai_service.generate_quiz_questions = AsyncMock(return_value=sample_questions)
            mock_db_service.create_quiz = AsyncMock(side_effect=Exception("Database error"))
            
            with pytest.raises(Exception, match="Database error"):
                await quiz_service.generate_quiz(sample_request)

    @pytest.mark.asyncio
    async def test_get_quiz_success(self, quiz_service, sample_quiz_data):
        with patch('src.services.quiz_generator.db_service') as mock_db_service:
            mock_db_service.get_quiz = AsyncMock(return_value=sample_quiz_data)
            
            result = await quiz_service.get_quiz("quiz-12345")
            
            assert result == sample_quiz_data
            mock_db_service.get_quiz.assert_called_once_with("quiz-12345")

    @pytest.mark.asyncio
    async def test_get_quiz_not_found(self, quiz_service):
        with patch('src.services.quiz_generator.db_service') as mock_db_service:
            mock_db_service.get_quiz = AsyncMock(return_value=None)
            
            with pytest.raises(ValueError, match="Quiz with ID quiz-12345 not found"):
                await quiz_service.get_quiz("quiz-12345")

    @pytest.mark.asyncio
    async def test_get_quiz_database_error(self, quiz_service):
        with patch('src.services.quiz_generator.db_service') as mock_db_service:
            mock_db_service.get_quiz = AsyncMock(side_effect=Exception("Database connection error"))
            
            with pytest.raises(Exception, match="Database connection error"):
                await quiz_service.get_quiz("quiz-12345")

    @pytest.mark.asyncio
    async def test_list_quizzes_success(self, quiz_service, sample_quiz_data):
        quizzes_list = [sample_quiz_data]
        
        with patch('src.services.quiz_generator.db_service') as mock_db_service:
            mock_db_service.get_quizzes = AsyncMock(return_value=quizzes_list)
            
            result = await quiz_service.list_quizzes(
                book_id="test-book-123", 
                limit=10, 
                offset=0
            )
            
            assert result["quizzes"] == quizzes_list
            assert result["count"] == 1
            assert result["limit"] == 10
            assert result["offset"] == 0
            
            mock_db_service.get_quizzes.assert_called_once_with(
                "test-book-123", 10, 0
            )

    @pytest.mark.asyncio
    async def test_list_quizzes_no_book_filter(self, quiz_service):
        with patch('src.services.quiz_generator.db_service') as mock_db_service:
            mock_db_service.get_quizzes = AsyncMock(return_value=[])
            
            result = await quiz_service.list_quizzes()
            
            assert result["quizzes"] == []
            assert result["count"] == 0
            assert result["limit"] == 10  # Default
            assert result["offset"] == 0   # Default
            
            mock_db_service.get_quizzes.assert_called_once_with(
                None, 10, 0
            )

    @pytest.mark.asyncio
    async def test_list_quizzes_database_error(self, quiz_service):
        with patch('src.services.quiz_generator.db_service') as mock_db_service:
            mock_db_service.get_quizzes = AsyncMock(side_effect=Exception("Database query error"))
            
            with pytest.raises(Exception, match="Database query error"):
                await quiz_service.list_quizzes()

    @pytest.mark.asyncio
    async def test_delete_quiz_success(self, quiz_service):
        with patch('src.services.quiz_generator.db_service') as mock_db_service:
            mock_db_service.delete_quiz = AsyncMock(return_value=True)
            
            result = await quiz_service.delete_quiz("quiz-12345")
            
            assert result is True
            mock_db_service.delete_quiz.assert_called_once_with("quiz-12345")

    @pytest.mark.asyncio
    async def test_delete_quiz_not_found(self, quiz_service):
        with patch('src.services.quiz_generator.db_service') as mock_db_service:
            mock_db_service.delete_quiz = AsyncMock(return_value=False)
            
            result = await quiz_service.delete_quiz("nonexistent-quiz")
            
            assert result is False
            mock_db_service.delete_quiz.assert_called_once_with("nonexistent-quiz")

    @pytest.mark.asyncio
    async def test_delete_quiz_database_error(self, quiz_service):
        with patch('src.services.quiz_generator.db_service') as mock_db_service:
            mock_db_service.delete_quiz = AsyncMock(side_effect=Exception("Database deletion error"))
            
            with pytest.raises(Exception, match="Database deletion error"):
                await quiz_service.delete_quiz("quiz-12345")

    @pytest.mark.asyncio
    async def test_generate_quiz_timing(self, quiz_service, sample_request, sample_questions):
        with patch('src.services.quiz_generator.ai_service') as mock_ai_service, \
             patch('src.services.quiz_generator.db_service') as mock_db_service, \
             patch('src.services.quiz_generator.settings') as mock_settings:
            
            # Add artificial delay to test timing
            async def slow_ai_service(*args, **kwargs):
                import asyncio
                await asyncio.sleep(0.1)  # 100ms delay
                return sample_questions
            
            mock_ai_service.generate_quiz_questions = AsyncMock(side_effect=slow_ai_service)
            mock_db_service.create_quiz = AsyncMock(return_value="quiz-12345")
            mock_settings.default_ai_model = "claude-3-sonnet-20240229"
            
            response = await quiz_service.generate_quiz(sample_request)
            
            # Should be at least 0.1 seconds due to artificial delay
            assert response.generation_time_seconds >= 0.1

    @pytest.mark.asyncio
    async def test_generate_quiz_creates_correct_quiz_object(self, quiz_service, sample_request, sample_questions):
        with patch('src.services.quiz_generator.ai_service') as mock_ai_service, \
             patch('src.services.quiz_generator.db_service') as mock_db_service, \
             patch('src.services.quiz_generator.settings') as mock_settings:
            
            mock_ai_service.generate_quiz_questions = AsyncMock(return_value=sample_questions)
            mock_db_service.create_quiz = AsyncMock(return_value="quiz-12345")
            mock_settings.default_ai_model = "claude-3-sonnet-20240229"
            
            await quiz_service.generate_quiz(sample_request)
            
            # Check that create_quiz was called with correct data structure
            call_args = mock_db_service.create_quiz.call_args[0][0]
            
            assert call_args["book_id"] == "test-book-123"
            assert len(call_args["questions"]) == 2
            assert call_args["ai_model"] == "claude-3-sonnet-20240229"
            assert call_args["generation_prompt"] == "Quiz generated from book content"
            assert call_args["metadata"] == {"chapter": "1"}
            assert "created_at" in call_args