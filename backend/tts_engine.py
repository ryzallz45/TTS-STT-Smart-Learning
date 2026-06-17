import os
import traceback
import time
import torch
# PyTorch >=2.6 defaults weights_only=True in torch.load, but TTS 0.22.0
# uses custom pickle classes (XttsConfig etc.) that break with that setting.
# Monkey-patch torch.load to force weights_only=False.
_orig_torch_load = torch.load
def _patched_torch_load(*a, **kw):
    kw.setdefault('weights_only', False)
    return _orig_torch_load(*a, **kw)
torch.load = _patched_torch_load

# torchaudio >=2.9 only supports torchcodec backend (needs FFmpeg DLLs).
# Patch to use soundfile instead since it's available.
import torchaudio
_orig_torchaudio_load = torchaudio.load
from pathlib import Path
def _patched_audio_load(uri, frame_offset=0, num_frames=-1, normalize=True, channels_first=True, format=None, buffer_size=4096, backend=None):
    import soundfile as sf
    if isinstance(uri, (str, Path)):
        path = str(uri)
        if num_frames > 0:
            data, sr = sf.read(path, start=frame_offset, frames=num_frames, dtype='float32' if normalize else 'int16')
        else:
            data, sr = sf.read(path, start=frame_offset, dtype='float32' if normalize else 'int16')
    else:
        data, sr = sf.read(uri, dtype='float32' if normalize else 'int16')
    if len(data.shape) == 1:
        data = data.reshape(1, -1)
    else:
        data = data.T
    if not channels_first:
        data = data.T
    return torch.from_numpy(data), sr
torchaudio.load = _patched_audio_load
# Force deep import of transformers submodules before TTS loads.
# TTS 0.22.0 imports these at module level; with transformers >=4.33's
# lazy submodules the timing can cause ImportError race conditions.
import transformers.generation.beam_constraints  # DisjunctiveConstraint, PhrasalConstraint
import transformers.generation.configuration_utils  # GenerationConfig
import transformers.generation.logits_process  # LogitsProcessorList
import transformers.generation.stopping_criteria  # StoppingCriteriaList
import transformers.generation.beam_search  # BeamSearchScorer, ConstrainedBeamSearchScorer
import transformers.generation.utils  # GenerationMixin
import transformers.modeling_utils  # PreTrainedModel
from TTS.api import TTS

_model = None
_is_cuda = torch.cuda.is_available()
_LOAD_ERROR = None


def get_tts_model():
    global _model, _LOAD_ERROR
    if _model is None:
        if _LOAD_ERROR:
            raise RuntimeError(
                f"TTS model previously failed to load: {_LOAD_ERROR}"
            )
        print(f"[TTS] Loading Coqui XTTS v2 (cuda={_is_cuda})...")
        print(f"[TTS] This may take a while (~2-5 mins on CPU)...")
        t0 = time.time()
        try:
            _model = TTS(
                "tts_models/multilingual/multi-dataset/xtts_v2",
                gpu=_is_cuda,
            )
            print(f"[TTS] Model loaded in {time.time() - t0:.2f}s")
        except Exception as e:
            _LOAD_ERROR = str(e)
            print(f"[TTS] FAILED to load model after {time.time() - t0:.2f}s")
            print(f"[TTS] Error: {e}")
            traceback.print_exc()
            raise RuntimeError(
                f"Gagal memuat model TTS: {e}. "
                f"Pastikan koneksi internet stabil (model diunduh dari Hugging Face) "
                f"dan RAM cukup (min 8GB)."
            )
    return _model


_TTS_SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn', 'hu', 'ko', 'ja', 'hi']

def generate_speech(text: str, speaker_wav: str, output_path: str, language: str = "en"):
    if language not in _TTS_SUPPORTED_LANGUAGES:
        raise ValueError(f"Language '{language}' is not supported. Supported: {_TTS_SUPPORTED_LANGUAGES}")
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
    print(f"[TTS] Done in {duration:.2f}s | {size_kb:.1f} KB -> {output_path}")
    return output_path
