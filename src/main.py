from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .schemas import AnalyzeRequest, AnalyzeResponse
from .predictor import get_detector, InjectionDetector
from .config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_detector()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    # This header prevents the browser from "MIME-sniffing" the content-type
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@app.get("/")
def health_check():
    return {"status": "running", "model": settings.MODEL_ID}

@app.get("/health/live")
def health_live():
    """Liveness probe - indicates if the service is running"""
    return {
        "status": "alive",
        "details": {
            "self": "up"
        }
    }

@app.get("/health/ready")
def health_ready():
    """Readiness probe - indicates if the service is ready to handle requests"""
    try:
        detector = get_detector()
        if detector is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        return {
            "status": "ready",
            "details": {
                "self": "up",
                "model_loaded": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_text(
    request: AnalyzeRequest, 
    detector: InjectionDetector = Depends(get_detector)
):
    try:
        result = detector.predict(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))