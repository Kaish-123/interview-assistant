"""
OpenAI Service - Handles all OpenAI API interactions
"""
import os
import base64
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load .env from parent directory if not found in current
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    # Try loading from parent directories
    parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    load_dotenv(parent_env)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("⚠️ WARNING: OPENAI_API_KEY not found in environment!")
else:
    print(f"✅ OpenAI API Key loaded (ending in ...{api_key[-8:]})")

client = AsyncOpenAI(api_key=api_key)


class OpenAIService:
    """Service class for OpenAI API interactions"""
    
    AVAILABLE_MODELS = {
        "gpt-4o": "GPT-4o (Best quality)",
        "gpt-4o-mini": "GPT-4o-mini (Fast & cheap)",
        "gpt-4-turbo": "GPT-4-Turbo (Balanced)"
    }
    
    ANSWER_MODE_INSTRUCTIONS = {
        "default": "",
        "quick": "\n\n[INSTRUCTION: Provide SHORT, CONCISE answers like a real human expert. Be brief and natural. Maximum 2-3 sentences. Sound like a knowledgeable colleague, avoid AI phrases.]",
        "detailed": "\n\n[INSTRUCTION: Provide COMPREHENSIVE explanations like a senior developer. Sound completely HUMAN - avoid typical AI patterns. Speak naturally, use casual professional tone, include real-world context.]",
        "code": "\n\n[INSTRUCTION: Focus on CODE EXAMPLES. Provide working code snippets with brief explanations. Prioritize practical, copy-paste ready code.]"
    }
    
    def __init__(self):
        self.max_retries = 3
        self.optimization_mode = True
        self.max_rounds_for_model = 4
        self.summary_threshold_rounds = 5
        self.image_detail_level = "low"
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio using Whisper API"""
        try:
            # Create a temporary file-like object
            import io
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.webm"
            
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                prompt=prompt or ""
            )
            
            return {
                "success": True,
                "text": transcription.text,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "error": str(e)
            }
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gpt-4o",
        answer_mode: str = "default",
        max_tokens: int = 1600
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion response"""
        
        # Add answer mode instruction
        instruction = self.ANSWER_MODE_INSTRUCTIONS.get(answer_mode, "")
        if instruction:
            messages = messages.copy()
            messages.append({"role": "system", "content": instruction})
        
        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                max_tokens=max_tokens
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            error_msg = str(e)
            if "invalid_api_key" in error_msg.lower() or "incorrect api key" in error_msg.lower():
                yield f"\n❌ API Key Error: Please check your OPENAI_API_KEY in backend/.env file"
            else:
                yield f"\n❌ Error: {error_msg}"
    
    async def get_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gpt-4o",
        answer_mode: str = "default",
        max_tokens: int = 1600
    ) -> Dict[str, Any]:
        """Get non-streaming chat completion"""
        
        # Add answer mode instruction
        instruction = self.ANSWER_MODE_INSTRUCTIONS.get(answer_mode, "")
        if instruction:
            messages = messages.copy()
            messages.append({"role": "system", "content": instruction})
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens
            )
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens if response.usage else None,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "content": "",
                "tokens_used": None,
                "error": str(e)
            }
    
    async def summarize_conversation(
        self,
        messages: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Generate a summary of the conversation for context optimization"""
        try:
            # Build transcript
            transcript_lines = []
            for m in messages:
                role = m.get("role", "")
                content = m.get("content", "")
                
                if isinstance(content, list):
                    # Multimodal - extract text only
                    text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                    content = " ".join(text_parts)
                
                if role in ("user", "assistant"):
                    label = "User" if role == "user" else "Assistant"
                    transcript_lines.append(f"{label}: {content}")
            
            transcript = "\n".join(transcript_lines)
            
            # Limit transcript length
            if len(transcript) > 15000:
                transcript = transcript[:15000] + "\n... [truncated for summary]"
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are summarizing an ongoing job interview conversation. "
                            "Extract key points discussed: technical topics, candidate responses, "
                            "questions asked, skills mentioned, and any important context. "
                            "Be concise but preserve critical interview details."
                        )
                    },
                    {"role": "user", "content": transcript}
                ],
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Summarization error: {e}")
            return None
    
    def build_optimized_messages(
        self,
        messages: List[Dict[str, Any]],
        summary: Optional[str] = None,
        optimization_mode: bool = True
    ) -> List[Dict[str, Any]]:
        """Build optimized message list for API while preserving context"""
        
        if not optimization_mode:
            return messages
        
        system_msgs = []
        other_msgs = []
        
        for m in messages:
            if m.get("role") == "system":
                system_msgs.append(m)
            elif m.get("role") in ("user", "assistant"):
                other_msgs.append(m)
        
        total_msgs = len(other_msgs)
        
        # Determine optimization level
        if total_msgs > 50:
            keep = 6
            optimization_level = "ULTRA"
        elif total_msgs > 35:
            keep = 8
            optimization_level = "AGGRESSIVE"
        elif total_msgs > 20:
            keep = 10
            optimization_level = "MODERATE"
        else:
            keep = self.max_rounds_for_model * 2
            optimization_level = "NORMAL"
        
        # Keep recent messages
        recent = other_msgs[-keep:] if len(other_msgs) > keep else other_msgs
        
        # Truncate system messages if needed
        MAX_SYSTEM_CHARS = 6000 if total_msgs > 40 else 10000
        optimized_system = []
        
        for sys_msg in system_msgs:
            content = sys_msg.get("content", "")
            if len(content) > MAX_SYSTEM_CHARS:
                truncated = content[:MAX_SYSTEM_CHARS] + "\n... [truncated for performance]"
                optimized_system.append({"role": "system", "content": truncated})
            else:
                optimized_system.append(sys_msg)
        
        # Add summary if available
        if summary:
            optimized_system.append({
                "role": "system",
                "content": f"[Interview Summary - Previous Discussion]\n{summary}"
            })
        
        # Optimize images in recent messages
        optimized_recent = []
        for i, msg in enumerate(recent):
            optimized_msg = self._optimize_message_images(msg)
            
            # Strip images from older messages in batch
            if i < len(recent) - 4 and optimization_level in ("AGGRESSIVE", "ULTRA"):
                optimized_msg = self._strip_images_keep_text(optimized_msg)
            
            # Truncate long messages in ULTRA mode
            if optimization_level == "ULTRA":
                optimized_msg = self._truncate_message(optimized_msg, max_chars=2000)
            
            optimized_recent.append(optimized_msg)
        
        return optimized_system + optimized_recent
    
    def _optimize_message_images(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Add detail:low to images for token optimization"""
        content = msg.get("content")
        if not isinstance(content, list):
            return msg
        
        optimized_content = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "image_url":
                image_url_data = item.get("image_url", {})
                optimized_item = {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url_data.get("url", ""),
                        "detail": self.image_detail_level
                    }
                }
                optimized_content.append(optimized_item)
            else:
                optimized_content.append(item)
        
        return {"role": msg.get("role"), "content": optimized_content}
    
    def _strip_images_keep_text(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Remove images from message, keep only text"""
        content = msg.get("content")
        if not isinstance(content, list):
            return msg
        
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        
        if not text_parts:
            text_parts = ["[Image was here]"]
        
        return {"role": msg.get("role"), "content": " ".join(text_parts)}
    
    def _truncate_message(self, msg: Dict[str, Any], max_chars: int = 2000) -> Dict[str, Any]:
        """Truncate long messages"""
        content = msg.get("content")
        
        if isinstance(content, str) and len(content) > max_chars:
            return {"role": msg.get("role"), "content": content[:max_chars] + "... [truncated]"}
        
        return msg
    
    def estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token count for messages"""
        tokens = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                tokens += len(content) // 4
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            tokens += len(item.get("text", "")) // 4
                        elif item.get("type") == "image_url":
                            tokens += 85 if self.optimization_mode else 765
        return tokens


# Create singleton instance
openai_service = OpenAIService()

