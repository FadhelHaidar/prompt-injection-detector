from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="The prompt text to analyze for injection attacks", min_length=1)

class AnalyzeResponse(BaseModel):
    is_injection: bool = Field(..., description="Whether the text is considered a prompt injection")
    label: str = Field(..., description="Raw label from the model (SAFE or INJECTION)")
    score: float = Field(..., description="Confidence score of the model")
    threshold: float = Field(..., description="The threshold used for this decision")
    message: str = Field(..., description="Human readable result message")
    processing_time: float = Field(..., description="Time taken to process in seconds")