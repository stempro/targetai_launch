"""Activity Chat API routes - Real-time streaming chat for weekly activities."""
import json
import logging
import os
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
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
    file_attachments: list[dict] | None = None  # Optional file attachments with name, size, url


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


class SaveTipRequest(BaseModel):
    """Request for saving a tip."""
    content: str
    timestamp: str


@router.post("/save-tip/{task_id}")
async def save_tip(task_id: str, request: SaveTipRequest):
    """Save a tip for a specific task."""
    storage = get_storage_client()
    path = f"activity_tips/{task_id}.json"

    try:
        # Load existing tips
        existing_tips = await storage.read_raw(path)
        if existing_tips and "tips" in existing_tips:
            tips = existing_tips["tips"]
        else:
            tips = []

        # Add new tip
        tips.append({
            "content": request.content,
            "timestamp": request.timestamp,
        })

        # Save updated tips
        await storage.write_raw(path, {"task_id": task_id, "tips": tips})
        return {"status": "saved", "tip_count": len(tips)}
    except Exception as e:
        logger.error(f"Error saving tip: {e}")
        raise HTTPException(status_code=500, detail="Failed to save tip")


@router.get("/tips/{task_id}")
async def get_tips(task_id: str):
    """Get saved tips for a specific task."""
    storage = get_storage_client()
    path = f"activity_tips/{task_id}.json"

    try:
        data = await storage.read_raw(path)
        if data and "tips" in data:
            return {"tips": data["tips"]}
        return {"tips": []}
    except Exception as e:
        logger.error(f"Error loading tips: {e}")
        return {"tips": []}


@router.delete("/tips/{task_id}/{tip_index}")
async def delete_tip(task_id: str, tip_index: int):
    """Delete a specific tip by index."""
    storage = get_storage_client()
    path = f"activity_tips/{task_id}.json"

    try:
        # Load existing tips
        data = await storage.read_raw(path)
        if not data or "tips" not in data:
            raise HTTPException(status_code=404, detail="No tips found")

        tips = data["tips"]

        # Check if index is valid
        if tip_index < 0 or tip_index >= len(tips):
            raise HTTPException(status_code=404, detail="Tip index out of range")

        # Remove the tip at the specified index
        tips.pop(tip_index)

        # Save updated tips
        await storage.write_raw(path, {"task_id": task_id, "tips": tips})
        return {"status": "deleted", "remaining_count": len(tips)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tip: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete tip")


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
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage

            settings = get_settings()
            llm = ChatOpenAI(
                model="gpt-4",
                api_key=settings.openai_api_key,
                temperature=0.7,
            )

            # Build file attachments context if present
            file_context = ""
            if request.file_attachments:
                file_context = "\n\nAttached files:\n"
                for file_info in request.file_attachments:
                    file_context += f"- {file_info.get('name', 'Unknown')} ({file_info.get('size', 'Unknown size')})\n"
                file_context += "\nNote: The user has attached these files for your reference. If they ask you to analyze or review these files, acknowledge them and provide guidance based on the file types and context."

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
{history_context}{file_context}

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


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    task_id: str = Form(...)
):
    """Upload a file attachment for chat."""
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg'}
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )

        # Validate file size (10MB max)
        content = await file.read()
        file_size = len(content)
        max_size = 10 * 1024 * 1024  # 10MB in bytes

        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size {file_size / 1024 / 1024:.2f}MB exceeds maximum of 10MB"
            )

        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = f"{unique_id}_{file.filename}"

        # Store file in Azure Blob Storage
        storage = get_storage_client()
        blob_path = f"chat_attachments/{task_id}/{safe_filename}"

        # Write file to storage
        await storage.write_raw(blob_path, content)

        # Generate download URL (for now, we'll use a simple path)
        # In production, this would be a signed Azure Blob URL
        file_url = f"/api/chat/activity/download/{task_id}/{safe_filename}"

        logger.info(f"Uploaded file {safe_filename} for task {task_id}")

        return {
            "success": True,
            "file_url": file_url,
            "file_name": file.filename,
            "file_size": file_size,
            "blob_path": blob_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/download/{task_id}/{filename}")
async def download_file(task_id: str, filename: str):
    """Download a file attachment."""
    try:
        storage = get_storage_client()
        blob_path = f"chat_attachments/{task_id}/{filename}"

        # Read file from storage
        content = await storage.read_raw(blob_path)

        if not content:
            raise HTTPException(status_code=404, detail="File not found")

        # Determine content type based on extension
        file_ext = os.path.splitext(filename)[1].lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
        }
        content_type = content_types.get(file_ext, 'application/octet-stream')

        from fastapi.responses import Response
        return Response(
            content=content,
            media_type=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")
