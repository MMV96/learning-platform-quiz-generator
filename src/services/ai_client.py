import json
import logging
from typing import List, Dict, Any
from anthropic import AsyncAnthropic
from ..config import settings
from ..models.quiz import Question, DifficultyLevel, QuestionType
from ..models.requests import QuizOptions

logger = logging.getLogger(__name__)

QUIZ_GENERATION_PROMPT_TEMPLATE = """
Generate an educational quiz based on the provided content. Respond ONLY with valid JSON, no other text.

CONTENT: {content}

PARAMETERS:
- Number of questions: {num_questions}
- Difficulty distribution: {difficulty_distribution}  
- Question types: {question_types}
- Language: {language}

INSTRUCTIONS:
1. Create questions that test understanding, not just memorization
2. Ensure questions are clear, unambiguous, and well-structured
3. For multiple choice questions, provide 4 plausible options with only one correct answer
4. Include detailed explanations that help learners understand the concept
5. Vary the difficulty according to the specified distribution
6. Cover different aspects and topics from the provided content
7. Make sure all questions are in the specified language

Required JSON format:
{{
  "questions": [
    {{
      "question": "Question text?",
      "type": "multiple_choice",
      "correct_answer": "Correct answer text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "explanation": "Detailed explanation of why this answer is correct and why others are incorrect",
      "difficulty": "easy",
      "topic": "Specific topic or subject area",
      "concepts_tested": ["Concept1", "Concept2"]
    }}
  ]
}}

IMPORTANT: Respond ONLY with the JSON structure above, nothing else. Ensure all text is in the requested language."""

class AIClientService:
    def __init__(self):
        self.client = None
        
    def _get_client(self):
        if self.client is None:
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self.client

    async def generate_quiz_questions(
        self, 
        content: str, 
        options: QuizOptions
    ) -> List[Question]:
        try:
            # Prepare difficulty distribution string
            diff_dist = ", ".join([f"{k}: {v*100:.0f}%" for k, v in options.difficulty_distribution.items()])
            
            # Prepare question types string
            q_types = ", ".join([t.value for t in options.question_types])
            
            prompt = QUIZ_GENERATION_PROMPT_TEMPLATE.format(
                content=content,
                num_questions=options.num_questions,
                difficulty_distribution=diff_dist,
                question_types=q_types,
                language=options.language
            )
            
            logger.info(f"Generating quiz with {options.num_questions} questions using model {settings.default_ai_model}")
            
            client = self._get_client()
            response = await client.messages.create(
                model=settings.default_ai_model,
                max_tokens=4000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse the response
            response_text = response.content[0].text.strip()
            logger.debug(f"AI Response: {response_text}")
            
            # Try to extract JSON from the response
            try:
                # Find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx == -1 or end_idx == 0:
                    raise ValueError("No JSON found in response")
                
                json_str = response_text[start_idx:end_idx]
                response_data = json.loads(json_str)
                
                if "questions" not in response_data:
                    raise ValueError("No 'questions' key in response")
                
                questions = []
                for q_data in response_data["questions"]:
                    # Validate and create Question object
                    question = Question(
                        question=q_data["question"],
                        type=QuestionType(q_data["type"]),
                        correct_answer=q_data["correct_answer"],
                        options=q_data.get("options"),
                        explanation=q_data["explanation"],
                        difficulty=DifficultyLevel(q_data["difficulty"]),
                        topic=q_data["topic"],
                        concepts_tested=q_data["concepts_tested"]
                    )
                    questions.append(question)
                
                logger.info(f"Successfully generated {len(questions)} questions")
                return questions
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"Response text: {response_text}")
                raise ValueError(f"Invalid JSON response from AI: {e}")
            
        except Exception as e:
            logger.error(f"Error generating quiz questions: {e}")
            raise

# Global AI client service instance
ai_service = AIClientService()