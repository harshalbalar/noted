"""
Meeting Transcriber — Web Edition
Groq Whisper for transcription (accurate, no hallucination)
Gemini for structured summarization
"""

import os
import io
import logging
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from groq import Groq
from google import genai
from google.genai import types

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("transcriber")


# ── Schemas ──

class DialogueTurn(BaseModel):
    speaker: str = Field(description="Inferred speaker name or 'Speaker 1', 'Speaker 2', etc.")
    message: str = Field(description="Cleaned-up text of what they said.")

class MeetingMinutes(BaseModel):
    executive_summary: str = Field(description="2-3 sentence overview of the meeting.")
    key_takeaways: list[str] = Field(description="Most critical points discussed.")
    action_items: list[str] = Field(description="Assigned tasks and next steps.")
    reconstructed_script: list[DialogueTurn] = Field(description="Chronological script with speakers.")

class SummarizeRequest(BaseModel):
    transcript: str
    gemini_key: str = ""


# ── App ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Meeting Transcriber started")
    if not GROQ_API_KEY:
        log.warning("GROQ_API_KEY not set — transcription won't work")
    if not GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY not set — summarization won't work")
    yield

app = FastAPI(title="Meeting Transcriber", lifespan=lifespan)

BASE_DIR = Path(__file__).parent
(BASE_DIR / "static").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ── Routes ──

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
    request=request,
    name="index.html",
    context={
        "has_groq_key": bool(GROQ_API_KEY),
        "has_gemini_key": bool(GEMINI_API_KEY),
    }
)


@app.websocket("/ws/transcribe")
async def websocket_transcribe(ws: WebSocket):
    await ws.accept()
    log.info("WebSocket connected")

    if not GROQ_API_KEY:
        await ws.send_json({"type": "error", "text": "GROQ_API_KEY not set on server."})
        await ws.close()
        return

    client = Groq(api_key=GROQ_API_KEY)

    try:
        while True:
            audio_bytes = await ws.receive_bytes()

            if len(audio_bytes) < 1000:
                continue

            log.info(f"Audio chunk: {len(audio_bytes)} bytes")

            try:
                result = client.audio.transcriptions.create(
                    file=("chunk.webm", io.BytesIO(audio_bytes)),
                    model="whisper-large-v3-turbo",
                    language="en",
                    response_format="text",
                )

                text = result.strip() if isinstance(result, str) else str(result).strip()

                # Whisper sometimes returns junk on silence
                junk = {"", ".", "...", "you", "thank you.", "thanks for watching!", "bye."}
                if text and text.lower() not in junk and len(text) > 1:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    await ws.send_json({
                        "type": "transcript",
                        "text": text,
                        "timestamp": timestamp,
                    })
                    log.info(f"Transcribed: {text[:80]}")

            except Exception as e:
                err = str(e)
                log.error(f"Groq error: {err}")
                if "rate" in err.lower() or "429" in err:
                    await ws.send_json({"type": "error", "text": "Rate limited — pausing briefly."})
                    import asyncio
                    await asyncio.sleep(2)
                else:
                    await ws.send_json({"type": "error", "text": f"Error: {err[:100]}"})

    except WebSocketDisconnect:
        log.info("WebSocket disconnected")
    except Exception as e:
        log.error(f"WebSocket error: {e}")


@app.post("/api/summarize")
async def summarize(req: SummarizeRequest):
    api_key = req.gemini_key or GEMINI_API_KEY
    if not api_key:
        return {"error": "No Gemini API key configured."}

    if not req.transcript or len(req.transcript.strip()) < 50:
        return {"error": "Not enough transcript to summarize."}

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
                "You are a highly efficient executive assistant. "
                "Review the following meeting transcript and extract structured minutes.\n\n"
                f"Transcript:\n{req.transcript}"
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MeetingMinutes,
                temperature=0.2,
            ),
        )
        minutes = response.parsed

        return {
            "executive_summary": minutes.executive_summary,
            "key_takeaways": minutes.key_takeaways,
            "action_items": minutes.action_items,
            "script": [{"speaker": t.speaker, "message": t.message} for t in minutes.reconstructed_script],
        }

    except Exception as e:
        log.error(f"Gemini error: {e}")
        return {"error": str(e)}


@app.get("/api/health")
async def health():
    return {"status": "ok", "groq": bool(GROQ_API_KEY), "gemini": bool(GEMINI_API_KEY)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
