class QuizGeneratorException(Exception):
    """Base exception class for quiz generator service"""
    pass

class QuizGenerationError(QuizGeneratorException):
    """Raised when quiz generation fails"""
    pass

class QuizNotFoundError(QuizGeneratorException):
    """Raised when a quiz is not found"""
    pass

class DatabaseConnectionError(QuizGeneratorException):
    """Raised when database connection fails"""
    pass

class AIServiceError(QuizGeneratorException):
    """Raised when AI service fails"""
    pass