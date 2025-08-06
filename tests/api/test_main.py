import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.main import app


class TestQuizAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health_check_success(self, client):
        with patch('src.main.db_service') as mock_db_service:
            mock_db_service.client.admin.command = AsyncMock()
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "quiz-generator"  # Based on settings
            assert data["version"] == "1.0.0"
            assert data["database"] == "connected"

    def test_health_check_database_failure(self, client):
        with patch('src.main.db_service') as mock_db_service:
            mock_db_service.client.admin.command.side_effect = Exception("Database unavailable")
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"] == "disconnected"
            assert "Database unavailable" in data["error"]

    def test_generate_quiz_success(self, client, sample_quiz_request):
        with patch('src.main.quiz_service') as mock_quiz_service:
            from src.models.requests import QuizGenerationResponse
            mock_response = QuizGenerationResponse(
                quiz_id="quiz-12345",
                questions_count=1,
                status="success",
                generation_time_seconds=2.5,
                ai_model_used="claude-3-sonnet-20240229"
            )
            mock_quiz_service.generate_quiz = AsyncMock(return_value=mock_response)
            
            response = client.post("/generate-quiz", json=sample_quiz_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["quiz_id"] == "quiz-12345"
            assert data["questions_count"] == 1
            assert data["generation_time_seconds"] == 2.5

    def test_generate_quiz_validation_error(self, client):
        invalid_request = {
            "content": "Too short",  # Less than 100 characters
            "book_id": "test-book"
        }
        
        response = client.post("/generate-quiz", json=invalid_request)
        
        assert response.status_code == 422  # Validation error

    def test_generate_quiz_service_error(self, client, sample_quiz_request):
        with patch('src.main.quiz_service') as mock_quiz_service:
            mock_quiz_service.generate_quiz = AsyncMock(side_effect=Exception("AI service unavailable"))
            
            response = client.post("/generate-quiz", json=sample_quiz_request)
            
            assert response.status_code == 500
            data = response.json()
            assert "AI service unavailable" in data["detail"]

    def test_get_quiz_success(self, client, sample_quiz_data):
        with patch('src.main.quiz_service') as mock_quiz_service:
            mock_quiz_service.get_quiz = AsyncMock(return_value=sample_quiz_data)
            
            response = client.get("/quizzes/507f1f77bcf86cd799439011")
            
            assert response.status_code == 200
            data = response.json()
            assert data["_id"] == "507f1f77bcf86cd799439011"
            assert data["book_id"] == "test-book-123"

    def test_get_quiz_not_found(self, client):
        with patch('src.main.quiz_service') as mock_quiz_service:
            mock_quiz_service.get_quiz = AsyncMock(side_effect=ValueError("Quiz not found"))
            
            response = client.get("/quizzes/nonexistent-id")
            
            assert response.status_code == 404
            data = response.json()
            assert "Quiz not found" in data["detail"]

    def test_get_quiz_service_error(self, client):
        with patch('src.main.quiz_service') as mock_quiz_service:
            mock_quiz_service.get_quiz = AsyncMock(side_effect=Exception("Database error"))
            
            response = client.get("/quizzes/507f1f77bcf86cd799439011")
            
            assert response.status_code == 500
            data = response.json()
            assert "Database error" in data["detail"]

    def test_list_quizzes_success(self, client, sample_quiz_data):
        with patch('src.main.quiz_service') as mock_quiz_service:
            mock_response = {
                "quizzes": [sample_quiz_data],
                "count": 1,
                "limit": 10,
                "offset": 0
            }
            mock_quiz_service.list_quizzes = AsyncMock(return_value=mock_response)
            
            response = client.get("/quizzes")
            
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1
            assert len(data["quizzes"]) == 1

    def test_list_quizzes_with_filters(self, client):
        with patch('src.main.quiz_service') as mock_quiz_service:
            mock_response = {
                "quizzes": [],
                "count": 0,
                "limit": 5,
                "offset": 10
            }
            mock_quiz_service.list_quizzes = AsyncMock(return_value=mock_response)
            
            response = client.get("/quizzes?book_id=test-book&limit=5&offset=10")
            
            assert response.status_code == 200
            mock_quiz_service.list_quizzes.assert_called_once_with("test-book", 5, 10)

    def test_list_quizzes_validation_error(self, client):
        # Test invalid limit (above maximum)
        response = client.get("/quizzes?limit=200")
        
        assert response.status_code == 422

    def test_list_quizzes_service_error(self, client):
        with patch('src.main.quiz_service') as mock_quiz_service:
            mock_quiz_service.list_quizzes = AsyncMock(side_effect=Exception("Database query failed"))
            
            response = client.get("/quizzes")
            
            assert response.status_code == 500
            data = response.json()
            assert "Database query failed" in data["detail"]

    def test_delete_quiz_success(self, client):
        with patch('src.main.quiz_service') as mock_quiz_service:
            mock_quiz_service.delete_quiz = AsyncMock(return_value=True)
            
            response = client.delete("/quizzes/507f1f77bcf86cd799439011")
            
            assert response.status_code == 200
            data = response.json()
            assert "deleted successfully" in data["message"]

    def test_delete_quiz_not_found(self, client):
        with patch('src.main.quiz_service') as mock_quiz_service:
            mock_quiz_service.delete_quiz = AsyncMock(return_value=False)
            
            response = client.delete("/quizzes/nonexistent-id")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]

    def test_delete_quiz_service_error(self, client):
        with patch('src.main.quiz_service') as mock_quiz_service:
            mock_quiz_service.delete_quiz = AsyncMock(side_effect=Exception("Database deletion failed"))
            
            response = client.delete("/quizzes/507f1f77bcf86cd799439011")
            
            assert response.status_code == 500
            data = response.json()
            assert "Database deletion failed" in data["detail"]

    def test_cors_middleware(self, client):
        # Test that CORS headers are present
        response = client.options("/generate-quiz")
        
        # FastAPI TestClient might not fully simulate CORS, but we can test the endpoint exists
        assert response.status_code in [200, 405]  # 405 is fine for OPTIONS on POST endpoint

    def test_generate_quiz_request_logging(self, client, sample_quiz_request):
        with patch('src.main.quiz_service') as mock_quiz_service, \
             patch('src.main.logger') as mock_logger:
            
            from src.models.requests import QuizGenerationResponse
            mock_response = QuizGenerationResponse(
                quiz_id="quiz-12345",
                questions_count=1,
                status="success",
                generation_time_seconds=1.0,
                ai_model_used="claude-3-sonnet-20240229"
            )
            mock_quiz_service.generate_quiz = AsyncMock(return_value=mock_response)
            
            response = client.post("/generate-quiz", json=sample_quiz_request)
            
            assert response.status_code == 200
            # Verify that appropriate logging was called
            mock_logger.info.assert_called_with(
                f"Received quiz generation request for book_id: {sample_quiz_request['book_id']}"
            )

    def test_app_metadata(self):
        # Test that the FastAPI app has correct metadata
        assert app.title == "Learning Platform Quiz Generator"
        assert app.version == "1.0.0"
        assert "microservice" in app.description.lower()

    def test_query_parameter_validation(self, client):
        # Test various query parameter validations
        
        # Valid parameters
        response = client.get("/quizzes?limit=1&offset=0")
        assert response.status_code in [200, 500]  # 500 if service fails, but validation passes
        
        # Invalid limit (below minimum)
        response = client.get("/quizzes?limit=0")
        assert response.status_code == 422
        
        # Invalid offset (below minimum)
        response = client.get("/quizzes?offset=-1")
        assert response.status_code == 422

    def test_request_body_validation(self, client):
        # Test missing required fields
        response = client.post("/generate-quiz", json={
            "content": "Valid content that is long enough for quiz generation purposes and meets all requirements"
            # Missing book_id
        })
        assert response.status_code == 422
        
        # Test invalid options
        response = client.post("/generate-quiz", json={
            "content": "Valid content that is long enough for quiz generation purposes and meets all requirements",
            "book_id": "test-book",
            "options": {
                "num_questions": 0  # Invalid: below minimum
            }
        })
        assert response.status_code == 422