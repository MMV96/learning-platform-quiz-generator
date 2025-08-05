from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .quiz import DifficultyLevel, QuestionType

class QuizGenerationRequest(BaseModel):
    content: str = Field(..., min_length=100, description="Text content to generate quiz from")
    book_id: str = Field(..., description="Book ID reference")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    options: Optional["QuizOptions"] = Field(default_factory=lambda: QuizOptions())

class QuizOptions(BaseModel):
    num_questions: int = Field(default=10, ge=1, le=20, description="Number of questions")
    difficulty_distribution: Optional[Dict[DifficultyLevel, float]] = Field(
        default={"easy": 0.3, "medium": 0.5, "hard": 0.2}
    )
    question_types: List[QuestionType] = Field(
        default=[QuestionType.MULTIPLE_CHOICE, QuestionType.BOOLEAN]
    )
    language: str = Field(default="it", description="Language for questions")

class QuizGenerationResponse(BaseModel):
    quiz_id: str = Field(..., description="Generated quiz ID")
    questions_count: int = Field(..., description="Number of questions generated")
    status: str = Field(default="success")
    generation_time_seconds: float = Field(..., description="Time taken to generate")
    ai_model_used: str = Field(..., description="AI model used")

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None