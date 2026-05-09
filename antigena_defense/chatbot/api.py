"""
FastAPI endpoints for the Antigena Chatbot Service
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

from .chatbot_service import AntigenaChatbot, ChatbotResponse

logger = logging.getLogger(__name__)

# Create router for chatbot endpoints
chatbot_router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Global chatbot instance
chatbot_instance: Optional[AntigenaChatbot] = None

class ChatMessage(BaseModel):
    message: str
    user_context: Optional[Dict[str, Any]] = None

class ChatbotActionRequest(BaseModel):
    action: str
    params: Optional[Dict[str, Any]] = None

class ChatbotActionResponse(BaseModel):
    success: bool
    result: Dict[str, Any]
    message: str

def get_chatbot() -> AntigenaChatbot:
    """Get or create chatbot instance"""
    global chatbot_instance
    if chatbot_instance is None:
        chatbot_instance = AntigenaChatbot()
    return chatbot_instance

@chatbot_router.post("/chat", response_model=ChatbotResponse)
async def chat_with_bot(
    chat_message: ChatMessage,
    chatbot: AntigenaChatbot = Depends(get_chatbot)
):
    """
    Send a message to the chatbot and get a response
    """
    try:
        response = await chatbot.process_message(
            message=chat_message.message,
            user_context=chat_message.user_context
        )
        return response
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.post("/action", response_model=ChatbotActionResponse)
async def execute_chatbot_action(
    action_request: ChatbotActionRequest,
    chatbot: AntigenaChatbot = Depends(get_chatbot)
):
    """
    Execute an automated action through the chatbot
    """
    try:
        result = await chatbot.execute_action(
            action=action_request.action,
            params=action_request.params
        )
        
        return ChatbotActionResponse(
            success=True,
            result=result,
            message=f"Action '{action_request.action}' executed successfully"
        )
    except Exception as e:
        logger.error(f"Error executing action {action_request.action}: {e}")
        return ChatbotActionResponse(
            success=False,
            result={"error": str(e)},
            message=f"Failed to execute action '{action_request.action}'"
        )

@chatbot_router.get("/history")
async def get_conversation_history(
    limit: int = 50,
    chatbot: AntigenaChatbot = Depends(get_chatbot)
):
    """
    Get conversation history
    """
    try:
        history = chatbot.get_conversation_history(limit=limit)
        return {
            "history": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in history
            ]
        }
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.delete("/history")
async def clear_conversation_history(
    chatbot: AntigenaChatbot = Depends(get_chatbot)
):
    """
    Clear conversation history
    """
    try:
        chatbot.clear_conversation()
        return {"message": "Conversation history cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.get("/status")
async def get_chatbot_status(
    chatbot: AntigenaChatbot = Depends(get_chatbot)
):
    """
    Get chatbot status and capabilities
    """
    try:
        return {
            "status": "active",
            "ai_enabled": chatbot.client is not None,
            "capabilities": [
                "system_guidance",
                "threat_analysis",
                "automation_assistance",
                "conversation_history"
            ],
            "conversation_length": len(chatbot.conversation_history)
        }
    except Exception as e:
        logger.error(f"Error getting chatbot status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
