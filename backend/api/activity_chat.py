"""Activity Chat API routes - Real-time streaming chat for weekly activities."""
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.task_advisor import get_task_recommendation
from config import get_settings
from dependencies import get_storage_client

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str
    content: str
    timestamp: str


class ChatHistoryData(BaseModel):
    """Chat history storage model."""
    task_id: str
    task_description: str
    messages: list[ChatMessage]


class StreamChatRequest(BaseModel):
    """Request for streaming chat."""
    task_id: str
    task_description: str
    message: str
    history: list[ChatMessage]


@router.post("/recommendation")
async def get_recommendation(request: dict[str, str]):
    """Get initial pre-written recommendation for a task."""
    task_description = request.get("task_description", "")
    recommendation = await get_task_recommendation(task_description)

    return {"recommendation": recommendation}


@router.get("/history/{task_id}")
async def get_chat_history(task_id: str):
    """Get chat history for a specific task."""
    storage = get_storage_client()
    path = f"activity_chats/{task_id}.json"

    try:
        data = await storage.read_raw(path)
        return data if data else {"messages": []}
    except Exception as e:
        logger.error(f"Error loading chat history: {e}")
        return {"messages": []}


@router.post("/history/{task_id}")
async def save_chat_history(task_id: str, data: ChatHistoryData):
    """Save chat history for a specific task."""
    storage = get_storage_client()
    path = f"activity_chats/{task_id}.json"

    try:
        await storage.write_raw(path, data.dict())
        return {"status": "saved"}
    except Exception as e:
        logger.error(f"Error saving chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to save chat history")


@router.post("/stream")
async def stream_chat_response(request: StreamChatRequest):
    """Stream AI response for activity chat."""

    async def generate_stream():
        """Generate streaming response."""
        try:
            # Build context from conversation history
            history_context = "\n".join([
                f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
                for msg in request.history[-5:]  # Last 5 messages for context
            ])

            # Import here to avoid circular imports
            from langchain_anthropic import ChatAnthropic
            from langchain_core.messages import SystemMessage, HumanMessage

            settings = get_settings()
            llm = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=settings.anthropic_api_key,
                temperature=0.7,
            )

            system_prompt = f"""You are an expert advisor for TargetAI's Phase 1 launch.

Context: The user is working on this task from the Phase 1 Action Plan:
"{request.task_description}"

Your role:
- Provide practical, actionable advice for executing this specific task
- Give concrete examples, templates, or step-by-step guidance
- Keep responses concise and focused (2-4 paragraphs max)
- Use bullet points for lists
- Reference the Phase 1 strategy: counselor-first, highly personalized, quality over quantity

Recent conversation:
{history_context}

Respond helpfully to the user's question while staying focused on this task."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=request.message)
            ]

            # Get AI response
            response = llm.invoke(messages)
            full_content = response.content

            # Stream response in chunks (3 characters at a time for smooth display)
            for i in range(0, len(full_content), 3):
                chunk = full_content[i:i+3]
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            # Signal completion
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            error_msg = "I apologize, but I encountered an error. Please try rephrasing your question."
            yield f"data: {json.dumps({'chunk': error_msg})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
