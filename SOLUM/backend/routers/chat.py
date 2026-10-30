from fastapi import APIRouter
from backend.models import ChatRequest, ChatResponse
from backend.services.chat_service import generate_chat_response

router = APIRouter(prefix="/api/chat", tags=["SOLUM AI Grounded Advisor"])

@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    return await generate_chat_response(request)
