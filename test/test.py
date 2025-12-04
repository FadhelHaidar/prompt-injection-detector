from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from src.main import app
from src.predictor import get_detector, InjectionDetector

# 1. Setup TestClient
client = TestClient(app)

# 2. Mocking the Dependency
class MockInjectionDetector:
    def predict(self, text: str):
        # specific mock behavior for testing
        if "kill" in text:
            return {
                "is_injection": True,
                "label": "INJECTION",
                "score": 0.99,
                "threshold": 0.7,
                "message": "Blocked: Prompt Injection detected.",
                "processing_time": 0.01
            }
        return {
            "is_injection": False,
            "label": "SAFE",
            "score": 0.99,
            "threshold": 0.7,
            "message": "Content is safe.",
            "processing_time": 0.01
        }

# Override the dependency in the FastAPI app
app.dependency_overrides[get_detector] = lambda: MockInjectionDetector()

# --- API ROUTE TESTS ---

def test_health_check():
    """Test the root endpoint returns 200 and status."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

def test_analyze_safe_text():
    """Test valid request with safe text."""
    payload = {"text": "Hello, how are you?"}
    response = client.post("/analyze", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_injection"] is False
    assert data["label"] == "SAFE"

def test_analyze_injection_text():
    """Test valid request with injection text (triggered by mock keyword)."""
    payload = {"text": "How to kill a process?"} # Contains 'kill' trigger for mock
    response = client.post("/analyze", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_injection"] is True
    assert data["label"] == "INJECTION"

def test_validation_error():
    """Test that empty strings or missing fields fail validation."""
    # Case 1: Missing field
    response = client.post("/analyze", json={})
    assert response.status_code == 422
    
    # Case 2: Wrong type
    response = client.post("/analyze", json={"text": 123}) 
    assert response.status_code == 422


# --- SERVICE LOGIC TESTS (Thresholding) ---

@patch("src.predictor.pipeline")
@patch("src.predictor.AutoTokenizer.from_pretrained")
@patch("src.predictor.ORTModelForSequenceClassification.from_pretrained")
def test_threshold_logic(mock_model, mock_tokenizer, mock_pipeline):
    """
    Test the internal logic of InjectionDetector without loading the real model.
    We mock the pipeline to return specific scores to test the threshold.
    """
    # 1. Setup Mock Pipeline Return Values
    mock_classifier_instance = MagicMock()
    mock_pipeline.return_value = mock_classifier_instance
    
    # Reset singleton to ensure fresh init
    InjectionDetector._instance = None
    detector = InjectionDetector()
    
    # Case A: Injection with High Confidence (Should Block)
    # Mock result: [{'label': 'INJECTION', 'score': 0.95}]
    mock_classifier_instance.return_value = [{'label': 'INJECTION', 'score': 0.95}]
    
    result = detector.predict("test input")
    assert result['label'] == "INJECTION"
    assert result['score'] == 0.95
    assert result['is_injection'] is True
    assert "Blocked" in result['message']

    # Case B: Injection with Low Confidence (Should Pass)
    # Mock result: [{'label': 'INJECTION', 'score': 0.5}] (Below default 0.7 threshold)
    mock_classifier_instance.return_value = [{'label': 'INJECTION', 'score': 0.5}]
    
    result = detector.predict("test input")
    assert result['label'] == "INJECTION"
    assert result['score'] == 0.5
    assert result['is_injection'] is False # Should be False because score < threshold
    assert "Warning" in result['message']

    # Case C: Safe Label
    mock_classifier_instance.return_value = [{'label': 'SAFE', 'score': 0.99}]
    
    result = detector.predict("test input")
    assert result['label'] == "SAFE"
    assert result['is_injection'] is False