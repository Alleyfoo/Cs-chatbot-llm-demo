from typing import Dict, List, Optional

from pydantic import BaseModel


class EmailRequest(BaseModel):
    email: str
    expected_keys: Optional[List[str]] = None
    customer_email: Optional[str] = None
    subject: Optional[str] = None


class EvaluationResult(BaseModel):
    score: float
    matched: List[str]
    missing: List[str]


class EmailResponse(BaseModel):
    reply: str
    expected_keys: List[str]
    answers: Dict[str, str]
    evaluation: EvaluationResult


