import os
import sys
import uuid
import io
import json
import time
import traceback
import subprocess
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from imageio_ffmpeg import get_ffmpeg_exe

_FFMPEG = None
def get_ffmpeg():
    global _FFMPEG
    if _FFMPEG is None:
        _FFMPEG = get_ffmpeg_exe()
    return _FFMPEG

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.stt_engine import transcribe, get_stt_model
from backend.tts_engine import generate_speech, get_tts_model
from backend.quiz_engine import evaluate_pronunciation
from backend.flashcard_engine import init_db as init_flashcard_db, create_set, list_sets, delete_set, create_card, list_cards, get_card, delete_card, update_card_audio
STORAGE_DIR = BASE_DIR / "storage"
VOICE_SAMPLES_DIR = STORAGE_DIR / "voice_samples"
GENERATED_DIR = STORAGE_DIR / "generated"
FRONTEND_DIR = BASE_DIR / "frontend"

for d in [VOICE_SAMPLES_DIR, GENERATED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

_models_loaded = {"stt": False, "tts": False, "tts_error": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print("Server starting — preloading models...")
    print("=" * 50)
    try:
        print("[Startup] Loading STT model...")
        t0 = time.time()
        get_stt_model()
        _models_loaded["stt"] = True
        print(f"[Startup] STT model ready in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"[Startup] STT model failed: {e}")
        _models_loaded["stt_error"] = str(e)
    try:
        print("[Startup] Loading TTS model...")
        t0 = time.time()
        get_tts_model()
        _models_loaded["tts"] = True
        print(f"[Startup] TTS model ready in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"[Startup] TTS model failed: {e}")
        _models_loaded["tts_error"] = str(e)
        traceback.print_exc()
    init_flashcard_db(STORAGE_DIR)
    print("=" * 50)
    yield
    print("[Shutdown] Server stopping.")


app = FastAPI(title="Smart Learning - STT & TTS with Voice Cloning", lifespan=lifespan)

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


def _convert_to_wav(src_path: Path) -> Path:
    if src_path.suffix.lower() == ".wav":
        return src_path
    wav_path = src_path.with_suffix(".wav")
    ffmpeg = get_ffmpeg()
    subprocess.run(
        [ffmpeg, "-y", "-i", str(src_path), "-ac", "1", "-ar", "22050", "-sample_fmt", "s16", str(wav_path)],
        capture_output=True, check=True,
    )
    src_path.unlink(missing_ok=True)
    return wav_path


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

    final_path = _convert_to_wav(save_path)

    return {
        "status": "ok",
        "file_id": file_id,
        "filename": final_path.name,
        "path": f"/storage/voice_samples/{final_path.name}",
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
        traceback.print_exc()
        raise HTTPException(500, f"Transkripsi gagal: {str(e)}")
    finally:
        if audio_path.exists():
            audio_path.unlink()

    return {"status": "ok", "text": text, "language": language}


@app.post("/api/tts/generate")
async def text_to_speech(text: str = Form(...), voice_sample: str = Form(...), language: str = Form("en")):
    if not text or not text.strip():
        raise HTTPException(400, "Text cannot be empty")

    voice_path = VOICE_SAMPLES_DIR / voice_sample
    if not voice_path.exists():
        raise HTTPException(404, "Voice sample not found. Please upload/record a voice sample first.")

    if voice_path.suffix.lower() != ".wav":
        wav_path = voice_path.with_suffix(".wav")
        if not wav_path.exists():
            ffmpeg = get_ffmpeg()
            subprocess.run(
                [ffmpeg, "-y", "-i", str(voice_path), "-ac", "1", "-ar", "22050", "-sample_fmt", "s16", str(wav_path)],
                capture_output=True, check=True,
            )
        voice_path = wav_path

    file_id = str(uuid.uuid4())
    output_filename = f"tts_{file_id}.wav"
    output_path = GENERATED_DIR / output_filename

    try:
        generate_speech(text.strip(), str(voice_path), str(output_path), language=language)
    except Exception as e:
        if output_path.exists():
            output_path.unlink()
        traceback.print_exc()
        raise HTTPException(500, f"Generate suara gagal: {str(e)}")

    return {
        "status": "ok",
        "audio_url": f"/storage/generated/{output_filename}",
        "filename": output_filename,
        "message": "Speech generated successfully",
    }


@app.post("/api/quiz/evaluate")
async def quiz_evaluate(file: UploadFile = File(...), target_text: str = Form(...), language: str = Form("id")):
    if not file.filename:
        raise HTTPException(400, "No audio file provided")
    if not target_text or not target_text.strip():
        raise HTTPException(400, "Target text cannot be empty")

    ext = Path(file.filename).suffix.lower()
    if not ext:
        ext = ".wav"

    file_id = str(uuid.uuid4())
    audio_path = GENERATED_DIR / f"quiz_input_{file_id}{ext}"

    content = await file.read()
    audio_path.write_bytes(content)

    try:
        transcribed = transcribe(str(audio_path), language=language)
        if not transcribed:
            raise HTTPException(400, "Tidak dapat mendeteksi ucapan. Silakan coba lagi.")
        result = evaluate_pronunciation(target_text, transcribed)
        result["transcribed_text"] = transcribed
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Evaluasi gagal: {str(e)}")
    finally:
        if audio_path.exists():
            audio_path.unlink()

    return {"status": "ok", "result": result}


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


# ─── Flashcard Routes ──────────────────────────────────────────────


@app.post("/api/flashcard/sets")
async def api_create_set(name: str = Form(...)):
    if not name.strip():
        raise HTTPException(400, "Nama set tidak boleh kosong")
    new_set = create_set(name.strip())
    return {"status": "ok", "set": new_set}


@app.get("/api/flashcard/sets")
async def api_list_sets():
    return {"status": "ok", "sets": list_sets()}


@app.delete("/api/flashcard/sets/{set_id}")
async def api_delete_set(set_id: str):
    if not delete_set(set_id):
        raise HTTPException(404, "Set tidak ditemukan")
    return {"status": "ok", "message": "Set berhasil dihapus"}


@app.post("/api/flashcard/cards")
async def api_create_card(set_id: str = Form(...), term: str = Form(...), definition: str = Form(...), language: str = Form("en")):
    if not term.strip() or not definition.strip():
        raise HTTPException(400, "Term dan definition tidak boleh kosong")
    card = create_card(set_id, term.strip(), definition.strip(), language)
    return {"status": "ok", "card": card}


@app.get("/api/flashcard/cards")
async def api_list_cards(set_id: str = None):
    return {"status": "ok", "cards": list_cards(set_id)}


@app.delete("/api/flashcard/cards/{card_id}")
async def api_delete_card(card_id: str):
    if not delete_card(card_id):
        raise HTTPException(404, "Kartu tidak ditemukan")
    return {"status": "ok", "message": "Kartu berhasil dihapus"}


@app.post("/api/flashcard/cards/{card_id}/generate-audio")
async def api_generate_card_audio(card_id: str, voice_sample: str = Form(...), language: str = Form("en")):
    card = get_card(card_id)
    if not card:
        raise HTTPException(404, "Kartu tidak ditemukan")
    if not card["term"].strip():
        raise HTTPException(400, "Term kartu kosong")

    voice_path = VOICE_SAMPLES_DIR / voice_sample
    if not voice_path.exists():
        raise HTTPException(404, "Voice sample tidak ditemukan")

    if voice_path.suffix.lower() != ".wav":
        wav_path = voice_path.with_suffix(".wav")
        if not wav_path.exists():
            ffmpeg = get_ffmpeg()
            subprocess.run(
                [ffmpeg, "-y", "-i", str(voice_path), "-ac", "1", "-ar", "22050", "-sample_fmt", "s16", str(wav_path)],
                capture_output=True, check=True,
            )
        voice_path = wav_path

    file_id = str(uuid.uuid4())
    output_filename = f"flashcard_{file_id}.wav"
    output_path = GENERATED_DIR / output_filename

    try:
        generate_speech(card["term"], str(voice_path), str(output_path), language=language)
        update_card_audio(card_id, output_filename)
    except Exception as e:
        if output_path.exists():
            output_path.unlink()
        traceback.print_exc()
        raise HTTPException(500, f"Generate audio gagal: {str(e)}")

    return {
        "status": "ok",
        "audio_url": f"/storage/generated/{output_filename}",
        "filename": output_filename,
    }


@app.get("/api/status")
async def status():
    import torch
    return {
        "status": "ok",
        "cuda_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "models": {
            "stt": "ready" if _models_loaded["stt"] else ("error" if _models_loaded.get("stt_error") else "loading"),
            "tts": "ready" if _models_loaded["tts"] else ("error" if _models_loaded.get("tts_error") else "loading"),
        },
    }


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
