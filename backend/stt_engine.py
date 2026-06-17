import os
import time
import torch
from faster_whisper import WhisperModel

_model = None
_device = "cuda" if torch.cuda.is_available() else "cpu"
_compute_type = "float16" if _device == "cuda" else "int8"
_CPU_THREADS = os.cpu_count() or 4


def get_stt_model():
    global _model
    if _model is None:
        print(f"[STT] Loading Faster-Whisper model (device={_device}, compute={_compute_type}, threads={_CPU_THREADS})...")
        t0 = time.time()
        _model = WhisperModel(
            "small",
            device=_device,
            compute_type=_compute_type,
            cpu_threads=_CPU_THREADS,
            num_workers=1,
        )
        print(f"[STT] Model loaded in {time.time() - t0:.2f}s")
    return _model


def transcribe(audio_path: str, language: str = "id") -> str:
    model = get_stt_model()
    print(f"[STT] Transcribing {audio_path} (lang={language}, beam=3, vad=on)...")
    t0 = time.time()
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=3,
        vad_filter=True,
    )
    text = " ".join(segment.text.strip() for segment in segments)
    duration = time.time() - t0
    print(f"[STT] Done in {duration:.2f}s | chars={len(text)} | lang={info.language} ({info.language_probability:.2f})")
    return text.strip()
