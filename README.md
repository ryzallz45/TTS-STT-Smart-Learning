# 🧠 Smart Learning — STT & TTS dengan Voice Cloningg

Sistem pembelajaran interaktif berbasis web yang mengintegrasikan **Speech-to-Text (STT)** dan **Text-to-Speech (TTS) dengan Voice Cloning**. Cocok untuk pembelajaran bahasa, terapi wicara, dan asistensi komunikasi.

## ✨ Fitur

| Fitur | Detail |
|-------|--------|
| **Rekam Suara** | Rekam langsung dari browser via MediaRecorder API (WebM/Opus) |
| **Upload Audio** | Upload file WAV, MP3, M4A, OGG, WebM, FLAC — otomatis dikonversi ke WAV |
| **Speech-to-Text** | Transkripsi akurat pakai Faster-Whisper (model small) dengan VAD filter |
| **Voice Cloning TTS** | Hasilkan suara dengan karakteristik vokal pengguna via XTTS v2 |
| **17 Bahasa TTS** | en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, hu, ko, ja, hi |
| **Preview & Download** | Putar dan unduh hasil TTS dari browser |

## 🏗️ Arsitektur

```
Frontend (index.html)         Backend (FastAPI)           Model Layer
┌─────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
│ Voice Sample     │───>│ POST /voice-sample  │    │  Faster-Whisper  │
│ STT Section      │───>│ POST /stt/transcribe│───>│  (small model)   │
│ TTS Section      │───>│ POST /tts/generate  │───>│  XTTS v2         │
└─────────────────┘    └─────────────────────┘    └──────────────────┘
                               │
                        ┌──────┴──────┐
                        │   FFmpeg    │← Konversi audio → WAV
                        │  SoundFile  │← Backend audio I/O
                        └─────────────┘
```

## 🚀 Cara Menjalankan

### 1. Clone & setup

```bash
git clone https://github.com/ryzallz45/TTS-STT-Smart-Learning.git
cd TTS-STT-Smart-Learning
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 2. Install dependencies

```bash
pip install -r backend/requirements.txt
pip install imageio-ffmpeg transformers==4.33.0
```

### 3. Jalankan server

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Buka **http://localhost:8000** di browser.

> ⚠️ **Pertama kali jalan**: model Faster-Whisper (~1 GB) dan XTTS v2 (~2 GB) akan diunduh dari Hugging Face. Pastikan koneksi stabil dan RAM minimal 8 GB.

## 📂 Struktur Proyek

```
backend/
  main.py           — Routing API, CORS, konversi audio (FFmpeg)
  stt_engine.py     — Faster-Whisper singleton
  tts_engine.py     — XTTS v2 singleton + monkey-patch kompatibilitas
  __init__.py
  requirements.txt
frontend/
  index.html        — Single-page application (vanilla JS)
storage/
  voice_samples/    — Sampel suara pengguna (WAV)
  generated/        — Hasil TTS (WAV)
```

## 🔧 Penanganan Masalah

| Masalah | Solusi |
|---------|--------|
| `ImportError: BeamSearchScorer` | Downgrade ke `transformers==4.33.0` |
| `weights_only=True` error | Monkey-patch `torch.load` → `weights_only=False` |
| TorchAudio butuh TorchCodec | Monkey-patch `torchaudio.load` pakai SoundFile |
| WebM tidak bisa dibaca | Konversi otomatis via FFmpeg (imageio-ffmpeg) |
| Bahasa "id" tidak didukung TTS | Default diganti ke "en" + validasi 17 bahasa |

## 🛠️ Tech Stack

**Backend**: Python, FastAPI, Uvicorn, Faster-Whisper, Coqui TTS (XTTS v2), PyTorch, SoundFile, FFmpeg

**Frontend**: HTML5, CSS3, JavaScript (vanilla), MediaRecorder API

## 📄 Lisensi

Proyek ini dikembangkan untuk tujuan edukasi.
