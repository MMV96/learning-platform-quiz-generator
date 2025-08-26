import pytest
from pydantic import ValidationError

from src.models.requests import (
    QuizGenerationRequest, QuizOptions, QuizGenerationResponse, ErrorResponse
)
from src.models.quiz import QuestionType, DifficultyLevel


class TestQuizOptions:
    def test_default_quiz_options(self):
        options = QuizOptions()
        
        assert options.num_questions == 10
        assert options.difficulty_distribution == {"easy": 0.3, "medium": 0.5, "hard": 0.2}
        assert QuestionType.MULTIPLE_CHOICE in options.question_types
        assert QuestionType.BOOLEAN in options.question_types
        assert options.language == "it"

    def test_custom_quiz_options(self):
        options = QuizOptions(
            num_questions=5,
            difficulty_distribution={"easy": 0.5, "medium": 0.3, "hard": 0.2},
            question_types=[QuestionType.MULTIPLE_CHOICE],
            language="en"
        )
        
        assert options.num_questions == 5
        assert options.difficulty_distribution["easy"] == 0.5
        assert len(options.question_types) == 1
        assert options.language == "en"

    def test_quiz_options_validation_min_questions(self):
        with pytest.raises(ValidationError):
            QuizOptions(num_questions=0)

    def test_quiz_options_validation_max_questions(self):
        with pytest.raises(ValidationError):
            QuizOptions(num_questions=21)

    def test_quiz_options_valid_range(self):
        options = QuizOptions(num_questions=1)
        assert options.num_questions == 1
        
        options = QuizOptions(num_questions=20)
        assert options.num_questions == 20


class TestQuizGenerationRequest:
    def test_valid_request(self):
        request = QuizGenerationRequest(
            content="This is a sample content that is long enough to be valid for quiz generation. It contains educational material about various topics that can be used to generate meaningful quiz questions.",
            book_id="book-123",
            metadata={"chapter": "1", "title": "Introduction"},
            options=QuizOptions(num_questions=5)
        )
        
        assert len(request.content) >= 100
        assert request.book_id == "book-123"
        assert request.metadata["chapter"] == "1"
        assert request.options.num_questions == 5

    def test_request_with_default_options(self):
        request = QuizGenerationRequest(
            content="This is a sample content that meets the minimum length requirement for quiz generation. It provides sufficient material for creating educational quiz questions.",
            book_id="book-456"
        )
        
        assert request.options.num_questions == 10  # Default value
        assert request.metadata == {}  # Default empty dict

    def test_request_validation_short_content(self):
        with pytest.raises(ValidationError):
            QuizGenerationRequest(
                content="Too short",  # Less than 100 characters
                book_id="book-123"
            )

    def test_request_without_content(self):
        request = QuizGenerationRequest(book_id="book-123")
        assert request.content is None
        assert request.book_id == "book-123"

    def test_request_validation_missing_book_id(self):
        with pytest.raises(ValidationError):
            QuizGenerationRequest(
                content="This is a valid length content for quiz generation that meets all the requirements for minimum character count."
            )

    def test_request_with_complex_options(self):
        custom_options = QuizOptions(
            num_questions=15,
            difficulty_distribution={"easy": 0.2, "medium": 0.6, "hard": 0.2},
            question_types=[QuestionType.MULTIPLE_CHOICE, QuestionType.OPEN],
            language="en"
        )
        
        request = QuizGenerationRequest(
            content="This is comprehensive educational content that covers multiple topics and concepts suitable for generating a variety of quiz questions with different difficulty levels.",
            book_id="advanced-book-789",
            metadata={"section": "advanced", "difficulty": "high"},
            options=custom_options
        )
        
        assert request.options.num_questions == 15
        assert request.options.language == "en"
        assert QuestionType.OPEN in request.options.question_types


class TestQuizGenerationResponse:
    def test_valid_response(self):
        response = QuizGenerationResponse(
            quiz_id="quiz-12345",
            questions_count=10,
            generation_time_seconds=5.67,
            ai_model_used="claude-3-sonnet-20240229"
        )
        
        assert response.quiz_id == "quiz-12345"
        assert response.questions_count == 10
        assert response.status == "success"  # Default value
        assert response.generation_time_seconds == 5.67
        assert response.ai_model_used == "claude-3-sonnet-20240229"

    def test_response_custom_status(self):
        response = QuizGenerationResponse(
            quiz_id="quiz-67890",
            questions_count=5,
            status="completed",
            generation_time_seconds=3.21,
            ai_model_used="claude-3-opus-20240229"
        )
        
        assert response.status == "completed"

    def test_response_validation_required_fields(self):
        with pytest.raises(ValidationError):
            QuizGenerationResponse(
                questions_count=10,
                generation_time_seconds=5.67,
                ai_model_used="claude-3-sonnet-20240229"
                # Missing quiz_id
            )


class TestErrorResponse:
    def test_simple_error_response(self):
        error = ErrorResponse(error="Something went wrong")
        
        assert error.error == "Something went wrong"
        assert error.detail is None
        assert error.code is None

    def test_detailed_error_response(self):
        error = ErrorResponse(
            error="Validation failed",
            detail="The content provided is too short for quiz generation",
            code="CONTENT_TOO_SHORT"
        )
        
        assert error.error == "Validation failed"
        assert error.detail == "The content provided is too short for quiz generation"
        assert error.code == "CONTENT_TOO_SHORT"

    def test_error_response_validation(self):
        with pytest.raises(ValidationError):
            ErrorResponse()  # Missing required 'error' field