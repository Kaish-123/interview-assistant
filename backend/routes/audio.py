"""
Audio Routes - Handle audio transcription
"""
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from models.schemas import TranscriptionRequest, TranscriptionResponse
from services.audio_service import audio_service

router = APIRouter(prefix="/audio", tags=["Audio"])


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(request: TranscriptionRequest):
    """Transcribe audio from base64 data"""
    
    # Validate format
    if not audio_service.validate_audio_format(request.format):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported audio format: {request.format}"
        )
    
    # Transcribe
    success, text, error = await audio_service.transcribe_audio(
        request.audio_data,
        audio_format=request.format,
        prompt=request.prompt
    )
    
    return TranscriptionResponse(
        text=text,
        success=success,
        error=error
    )


@router.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for live transcription.
    Receives audio chunks and returns transcriptions.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive audio data
            data = await websocket.receive_text()
            request = json.loads(data)
            
            action = request.get("action", "transcribe")
            
            if action == "transcribe":
                audio_data = request.get("audio_data", "")
                audio_format = request.get("format", "webm")
                prompt = request.get("prompt", "")
                
                if audio_data:
                    success, text, error = await audio_service.transcribe_audio(
                        audio_data,
                        audio_format=audio_format,
                        prompt=prompt
                    )
                    
                    await websocket.send_json({
                        "type": "transcription",
                        "text": text,
                        "success": success,
                        "error": error
                    })
            
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        print("Audio WebSocket disconnected")
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass




