import os
import time
import torch
from TTS.api import TTS

_model = None
_device = "cuda" if torch.cuda.is_available() else "cpu"


def get_tts_model():
    global _model
    if _model is None:
        print(f"[TTS] Loading Coqui XTTS v2 (device={_device})...")
        t0 = time.time()
        _model = TTS("tts_models/multilingual/multi-dataset/xtts_v2", device=_device)
        print(f"[TTS] Model loaded in {time.time() - t0:.2f}s")
    return _model


def generate_speech(text: str, speaker_wav: str, output_path: str, language: str = "id"):
    model = get_tts_model()
    print(f"[TTS] Generating speech for {len(text)} chars (lang={language})...")
    t0 = time.time()

    model.tts_to_file(
        text=text,
        speaker_wav=speaker_wav,
        language=language,
        file_path=output_path,
    )

    duration = time.time() - t0
    size_kb = os.path.getsize(output_path) / 1024
    print(f"[TTS] Done in {duration:.2f}s | {size_kb:.1f} KB → {output_path}")
    return output_path
