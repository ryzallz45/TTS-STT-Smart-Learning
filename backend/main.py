import os
import uuid
import io
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.stt_engine import transcribe
from backend.tts_engine import generate_speech

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
VOICE_SAMPLES_DIR = STORAGE_DIR / "voice_samples"
GENERATED_DIR = STORAGE_DIR / "generated"
FRONTEND_DIR = BASE_DIR / "frontend"

for d in [VOICE_SAMPLES_DIR, GENERATED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Smart Learning - STT & TTS with Voice Cloning")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/storage/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")
app.mount("/storage/voice_samples", StaticFiles(directory=str(VOICE_SAMPLES_DIR)), name="voice_samples")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(404, "Frontend not found")
    return index_path.read_text(encoding="utf-8")


@app.post("/api/voice-sample/upload")
async def upload_voice_sample(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac"):
        raise HTTPException(400, "Unsupported format. Use WAV, MP3, M4A, OGG, WebM, or FLAC.")

    file_id = str(uuid.uuid4())
    save_path = VOICE_SAMPLES_DIR / f"{file_id}{ext}"

    content = await file.read()
    save_path.write_bytes(content)

    return {
        "status": "ok",
        "file_id": file_id,
        "filename": f"{file_id}{ext}",
        "path": f"/storage/voice_samples/{file_id}{ext}",
        "message": "Voice sample uploaded successfully",
    }


@app.post("/api/voice-sample/record")
async def record_voice_sample(file: UploadFile = File(...)):
    return await upload_voice_sample(file)


@app.post("/api/stt/transcribe")
async def speech_to_text(file: UploadFile = File(...), language: str = Form("id")):
    if not file.filename:
        raise HTTPException(400, "No audio file provided")

    ext = Path(file.filename).suffix.lower()
    if not ext:
        ext = ".wav"

    file_id = str(uuid.uuid4())
    audio_path = GENERATED_DIR / f"stt_input_{file_id}{ext}"

    content = await file.read()
    audio_path.write_bytes(content)

    try:
        text = transcribe(str(audio_path), language=language)
    except Exception as e:
        raise HTTPException(500, f"Transcription failed: {str(e)}")
    finally:
        if audio_path.exists():
            audio_path.unlink()

    return {"status": "ok", "text": text, "language": language}


@app.post("/api/tts/generate")
async def text_to_speech(text: str = Form(...), voice_sample: str = Form(...), language: str = Form("id")):
    if not text or not text.strip():
        raise HTTPException(400, "Text cannot be empty")

    voice_path = VOICE_SAMPLES_DIR / voice_sample
    if not voice_path.exists():
        raise HTTPException(404, "Voice sample not found. Please upload/record a voice sample first.")

    file_id = str(uuid.uuid4())
    output_filename = f"tts_{file_id}.wav"
    output_path = GENERATED_DIR / output_filename

    try:
        generate_speech(text.strip(), str(voice_path), str(output_path), language=language)
    except Exception as e:
        if output_path.exists():
            output_path.unlink()
        raise HTTPException(500, f"TTS generation failed: {str(e)}")

    return {
        "status": "ok",
        "audio_url": f"/storage/generated/{output_filename}",
        "filename": output_filename,
        "message": "Speech generated successfully",
    }


@app.get("/api/voice-samples")
async def list_voice_samples():
    files = []
    for f in sorted(VOICE_SAMPLES_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.is_file() and f.suffix.lower() in (".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac"):
            files.append({
                "filename": f.name,
                "path": f"/storage/voice_samples/{f.name}",
                "size_kb": round(f.stat().st_size / 1024, 1),
                "created": f.stat().st_mtime,
            })
    return {"status": "ok", "samples": files}


@app.get("/api/status")
async def status():
    import torch
    return {
        "status": "ok",
        "cuda_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
    }


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
