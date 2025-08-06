from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    BOOLEAN = "boolean"  
    OPEN = "open"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Question(BaseModel):
    question: str = Field(..., min_length=10, description="Quiz question text")
    type: QuestionType = Field(..., description="Type of question")
    correct_answer: Union[str, bool] = Field(..., description="Correct answer")
    options: Optional[List[str]] = Field(None, description="Options for multiple choice")
    explanation: str = Field(..., min_length=20, description="Detailed explanation")
    difficulty: DifficultyLevel = Field(..., description="Question difficulty")
    topic: str = Field(..., description="Specific topic/subject")
    concepts_tested: List[str] = Field(..., description="Concepts being tested")
    
    @field_validator('correct_answer')
    @classmethod
    def convert_answer_to_string(cls, v):
        if isinstance(v, bool):
            return str(v).lower()
        return str(v)

class Quiz(BaseModel):
    book_id: str = Field(..., description="Reference to source book")
    questions: List[Question] = Field(..., min_length=1, max_length=20)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ai_model: str = Field(..., description="AI model used for generation")
    generation_prompt: Optional[str] = Field(None, description="Prompt used")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class QuizDocument(Quiz):
    id: Optional[str] = Field(None, alias="_id")
    
    model_config = {"populate_by_name": True}