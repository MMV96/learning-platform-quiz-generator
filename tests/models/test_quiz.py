import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.quiz import (
    Question, Quiz, QuizDocument, 
    QuestionType, DifficultyLevel
)


class TestQuestion:
    def test_create_valid_multiple_choice_question(self):
        question = Question(
            question="What is the capital of Italy?",
            type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Rome",
            options=["Rome", "Milan", "Naples", "Venice"],
            explanation="Rome is the capital and largest city of Italy.",
            difficulty=DifficultyLevel.EASY,
            topic="Geography",
            concepts_tested=["Italian cities", "European capitals"]
        )
        
        assert question.question == "What is the capital of Italy?"
        assert question.type == QuestionType.MULTIPLE_CHOICE
        assert question.correct_answer == "Rome"
        assert len(question.options) == 4
        assert question.difficulty == DifficultyLevel.EASY

    def test_create_valid_boolean_question(self):
        question = Question(
            question="Is Rome the capital of Italy?",
            type=QuestionType.BOOLEAN,
            correct_answer=True,
            explanation="Yes, Rome is indeed the capital of Italy.",
            difficulty=DifficultyLevel.EASY,
            topic="Geography",
            concepts_tested=["Italian capitals"]
        )
        
        assert question.question == "Is Rome the capital of Italy?"
        assert question.type == QuestionType.BOOLEAN
        assert question.correct_answer == "true"
        assert question.options is None

    def test_create_valid_open_question(self):
        question = Question(
            question="What are the main characteristics of Roman architecture?",
            type=QuestionType.OPEN,
            correct_answer="Roman architecture featured arches, domes, and concrete construction",
            explanation="Roman architecture was characterized by innovative use of arches, development of the dome, and extensive use of concrete.",
            difficulty=DifficultyLevel.HARD,
            topic="Architecture",
            concepts_tested=["Roman architecture", "Ancient construction"]
        )
        
        assert question.type == QuestionType.OPEN
        assert question.difficulty == DifficultyLevel.HARD

    def test_question_validation_short_question(self):
        with pytest.raises(ValidationError):
            Question(
                question="Short?",  # Too short
                type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="Answer",
                explanation="This question is too short to be valid.",
                difficulty=DifficultyLevel.EASY,
                topic="Test",
                concepts_tested=["validation"]
            )

    def test_question_validation_short_explanation(self):
        with pytest.raises(ValidationError):
            Question(
                question="What is a valid question for testing?",
                type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="Answer",
                explanation="Short",  # Too short
                difficulty=DifficultyLevel.EASY,
                topic="Test",
                concepts_tested=["validation"]
            )

    def test_boolean_answer_conversion(self):
        question = Question(
            question="Is this a boolean question test?",
            type=QuestionType.BOOLEAN,
            correct_answer=False,
            explanation="This tests boolean answer conversion to string.",
            difficulty=DifficultyLevel.MEDIUM,
            topic="Testing",
            concepts_tested=["boolean conversion"]
        )
        
        assert question.correct_answer == "false"


class TestQuiz:
    def test_create_valid_quiz(self):
        questions = [
            Question(
                question="What is the capital of Italy?",
                type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="Rome",
                options=["Rome", "Milan", "Naples", "Venice"],
                explanation="Rome is the capital and largest city of Italy.",
                difficulty=DifficultyLevel.EASY,
                topic="Geography",
                concepts_tested=["Italian cities"]
            )
        ]
        
        quiz = Quiz(
            book_id="test-book-123",
            questions=questions,
            ai_model="claude-3-sonnet-20240229",
            generation_prompt="Test quiz generation",
            metadata={"chapter": "1"}
        )
        
        assert quiz.book_id == "test-book-123"
        assert len(quiz.questions) == 1
        assert quiz.ai_model == "claude-3-sonnet-20240229"
        assert isinstance(quiz.created_at, datetime)

    def test_quiz_validation_empty_questions(self):
        with pytest.raises(ValidationError):
            Quiz(
                book_id="test-book-123",
                questions=[],  # Empty list not allowed
                ai_model="claude-3-sonnet-20240229"
            )

    def test_quiz_validation_too_many_questions(self):
        questions = []
        for i in range(21):  # More than max allowed (20)
            questions.append(
                Question(
                    question=f"Question {i+1} for testing limits?",
                    type=QuestionType.MULTIPLE_CHOICE,
                    correct_answer="Answer",
                    options=["A", "B", "C", "D"],
                    explanation="This is a test question to check limits.",
                    difficulty=DifficultyLevel.EASY,
                    topic="Testing",
                    concepts_tested=["limits"]
                )
            )
        
        with pytest.raises(ValidationError):
            Quiz(
                book_id="test-book-123",
                questions=questions,
                ai_model="claude-3-sonnet-20240229"
            )

    def test_quiz_default_metadata(self):
        questions = [
            Question(
                question="What is a test question for metadata?",
                type=QuestionType.BOOLEAN,
                correct_answer=True,
                explanation="This tests default metadata behavior.",
                difficulty=DifficultyLevel.MEDIUM,
                topic="Testing",
                concepts_tested=["metadata"]
            )
        ]
        
        quiz = Quiz(
            book_id="test-book-123",
            questions=questions,
            ai_model="claude-3-sonnet-20240229"
        )
        
        assert quiz.metadata == {}


class TestQuizDocument:
    def test_quiz_document_with_id(self):
        questions = [
            Question(
                question="What is a document test question?",
                type=QuestionType.OPEN,
                correct_answer="A question for testing document models",
                explanation="This question tests the QuizDocument model with ID handling.",
                difficulty=DifficultyLevel.MEDIUM,
                topic="Testing",
                concepts_tested=["document modeling"]
            )
        ]
        
        quiz_doc = QuizDocument(
            id="507f1f77bcf86cd799439011",
            book_id="test-book-123",
            questions=questions,
            ai_model="claude-3-sonnet-20240229"
        )
        
        assert quiz_doc.id == "507f1f77bcf86cd799439011"
        assert quiz_doc.book_id == "test-book-123"

    def test_quiz_document_alias_handling(self):
        questions = [
            Question(
                question="What tests alias handling in documents?",
                type=QuestionType.BOOLEAN,
                correct_answer=True,
                explanation="This question tests how _id aliases work in documents.",
                difficulty=DifficultyLevel.EASY,
                topic="Database",
                concepts_tested=["aliases", "document structure"]
            )
        ]
        
        # Test with _id alias
        quiz_data = {
            "_id": "507f1f77bcf86cd799439011",
            "book_id": "test-book-123",
            "questions": [q.model_dump() for q in questions],
            "ai_model": "claude-3-sonnet-20240229"
        }
        
        quiz_doc = QuizDocument(**quiz_data)
        assert quiz_doc.id == "507f1f77bcf86cd799439011"