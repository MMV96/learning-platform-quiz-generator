import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.ai_client import AIClientService
from src.models.quiz import Question, QuestionType, DifficultyLevel
from src.models.requests import QuizOptions


class TestAIClientService:
    @pytest.fixture
    def ai_service(self):
        return AIClientService()

    @pytest.fixture
    def quiz_options(self):
        return QuizOptions(
            num_questions=2,
            difficulty_distribution={"easy": 0.5, "medium": 0.3, "hard": 0.2},
            question_types=[QuestionType.MULTIPLE_CHOICE, QuestionType.BOOLEAN],
            language="en"
        )

    @pytest.fixture
    def mock_ai_response(self):
        return {
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
                },
                {
                    "question": "Is Rome located in northern Italy?",
                    "type": "boolean",
                    "correct_answer": "false",
                    "explanation": "Rome is located in central Italy, not northern Italy.",
                    "difficulty": "medium",
                    "topic": "Geography",
                    "concepts_tested": ["Italian geography"]
                }
            ]
        }

    def test_get_client_creates_client(self, ai_service):
        with patch('src.services.ai_client.AsyncAnthropic') as mock_anthropic, \
             patch('src.services.ai_client.settings') as mock_settings:
            
            mock_settings.anthropic_api_key = "test-api-key"
            mock_client_instance = MagicMock()
            mock_anthropic.return_value = mock_client_instance
            
            client = ai_service._get_client()
            
            assert client == mock_client_instance
            mock_anthropic.assert_called_once_with(api_key="test-api-key")

    def test_get_client_reuses_existing_client(self, ai_service):
        with patch('src.services.ai_client.AsyncAnthropic') as mock_anthropic:
            mock_client_instance = MagicMock()
            ai_service.client = mock_client_instance
            
            client = ai_service._get_client()
            
            assert client == mock_client_instance
            mock_anthropic.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_quiz_questions_success(self, ai_service, quiz_options, mock_ai_response):
        with patch.object(ai_service, '_get_client') as mock_get_client, \
             patch('src.services.ai_client.settings') as mock_settings:
            
            # Setup mocks
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_settings.default_ai_model = "claude-3-sonnet-20240229"
            
            # Mock the API response
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = json.dumps(mock_ai_response)
            mock_client.messages.create.return_value = mock_response
            
            # Execute
            questions = await ai_service.generate_quiz_questions(
                content="Rome is the capital of Italy.",
                options=quiz_options
            )
            
            # Assertions
            assert len(questions) == 2
            assert isinstance(questions[0], Question)
            assert questions[0].question == "What is the capital of Italy?"
            assert questions[0].type == QuestionType.MULTIPLE_CHOICE
            assert questions[1].type == QuestionType.BOOLEAN

    @pytest.mark.asyncio
    async def test_generate_quiz_questions_formats_prompt_correctly(self, ai_service, quiz_options):
        with patch.object(ai_service, '_get_client') as mock_get_client, \
             patch('src.services.ai_client.settings') as mock_settings:
            
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_settings.default_ai_model = "claude-3-sonnet-20240229"
            
            # Mock simple response to avoid JSON parsing
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = '{"questions": []}'
            mock_client.messages.create.return_value = mock_response
            
            await ai_service.generate_quiz_questions(
                content="Test content for quiz generation",
                options=quiz_options
            )
            
            # Check that the client was called with correct parameters
            call_args = mock_client.messages.create.call_args
            assert call_args[1]["model"] == "claude-3-sonnet-20240229"
            assert call_args[1]["max_tokens"] == 4000
            assert call_args[1]["temperature"] == 0.7
            
            # Check prompt formatting
            prompt = call_args[1]["messages"][0]["content"]
            assert "Test content for quiz generation" in prompt
            assert "2" in prompt  # num_questions
            assert "50%" in prompt  # difficulty distribution percentage
            assert "multiple_choice, boolean" in prompt  # question types
            assert "en" in prompt  # language

    @pytest.mark.asyncio
    async def test_generate_quiz_questions_invalid_json_response(self, ai_service, quiz_options):
        with patch.object(ai_service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            # Mock invalid JSON response
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = "This is not valid JSON"
            mock_client.messages.create.return_value = mock_response
            
            with pytest.raises(ValueError, match="No JSON found in response"):
                await ai_service.generate_quiz_questions(
                    content="Test content",
                    options=quiz_options
                )

    @pytest.mark.asyncio
    async def test_generate_quiz_questions_malformed_json(self, ai_service, quiz_options):
        with patch.object(ai_service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            # Mock malformed JSON response
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = '{"questions": [invalid json}'
            mock_client.messages.create.return_value = mock_response
            
            with pytest.raises(ValueError, match="Invalid JSON response from AI"):
                await ai_service.generate_quiz_questions(
                    content="Test content",
                    options=quiz_options
                )

    @pytest.mark.asyncio
    async def test_generate_quiz_questions_missing_questions_key(self, ai_service, quiz_options):
        with patch.object(ai_service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            # Mock response without questions key
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = '{"data": []}'
            mock_client.messages.create.return_value = mock_response
            
            with pytest.raises(ValueError, match="No 'questions' key in response"):
                await ai_service.generate_quiz_questions(
                    content="Test content",
                    options=quiz_options
                )

    @pytest.mark.asyncio
    async def test_generate_quiz_questions_invalid_question_data(self, ai_service, quiz_options):
        with patch.object(ai_service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            # Mock response with invalid question data
            invalid_response = {
                "questions": [
                    {
                        "question": "Short?",  # Too short, should fail validation
                        "type": "multiple_choice",
                        "correct_answer": "Answer",
                        "explanation": "Short",  # Too short
                        "difficulty": "easy",
                        "topic": "Test",
                        "concepts_tested": ["test"]
                    }
                ]
            }
            
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = json.dumps(invalid_response)
            mock_client.messages.create.return_value = mock_response
            
            with pytest.raises(Exception):  # Pydantic validation error
                await ai_service.generate_quiz_questions(
                    content="Test content",
                    options=quiz_options
                )

    @pytest.mark.asyncio
    async def test_generate_quiz_questions_anthropic_api_error(self, ai_service, quiz_options):
        with patch.object(ai_service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.messages.create.side_effect = Exception("API rate limit exceeded")
            
            with pytest.raises(Exception, match="API rate limit exceeded"):
                await ai_service.generate_quiz_questions(
                    content="Test content",
                    options=quiz_options
                )

    @pytest.mark.asyncio
    async def test_generate_quiz_questions_extracts_json_from_text(self, ai_service, quiz_options, mock_ai_response):
        with patch.object(ai_service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            # Mock response with extra text around JSON
            json_str = json.dumps(mock_ai_response)
            response_with_extra_text = f"Here is the quiz: {json_str} Hope this helps!"
            
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = response_with_extra_text
            mock_client.messages.create.return_value = mock_response
            
            questions = await ai_service.generate_quiz_questions(
                content="Test content",
                options=quiz_options
            )
            
            assert len(questions) == 2
            assert questions[0].question == "What is the capital of Italy?"

    @pytest.mark.asyncio
    async def test_difficulty_distribution_formatting(self, ai_service):
        # Test the difficulty distribution string formatting
        options = QuizOptions(
            difficulty_distribution={"easy": 0.3, "medium": 0.5, "hard": 0.2}
        )
        
        # This tests the internal formatting logic indirectly
        # by checking the expected format when the method is called
        with patch.object(ai_service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = '{"questions": []}'
            mock_client.messages.create.return_value = mock_response
            
            # Run the method to trigger formatting
            await ai_service.generate_quiz_questions("test", options)
            
            # Check the prompt contains correctly formatted percentages
            call_args = mock_client.messages.create.call_args
            prompt = call_args[1]["messages"][0]["content"]
            assert "30%" in prompt
            assert "50%" in prompt
            assert "20%" in prompt