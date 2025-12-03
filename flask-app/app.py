import os
import re
import tempfile
import time
from glob import glob
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import logging

try:
    import site
except Exception:
    site = None

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename, safe_join
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Disable cuDNN by default to avoid missing library errors on GPU-first runs
_ct2_use_cudnn_default = os.getenv("CT2_USE_CUDNN", "0")
os.environ.setdefault("CT2_USE_CUDNN", _ct2_use_cudnn_default)

_diagnostic_notes: List[str] = []
_app_start_time = time.time()

try:
    from faster_whisper import WhisperModel
except ImportError as exc:
    raise SystemExit(
        "faster-whisper is required. Install dependencies with `pip install -r requirements.txt`."
    ) from exc

# Import our utility modules
from utils.diarization import (
    diarize_audio,
    assign_speakers_to_segments,
    unload_diarization_model,
    get_vram_usage,
    is_model_loaded as is_diarization_loaded
)
from utils.api_backends import transcribe_with_openai, diarize_with_assemblyai
from utils.formatters import (
    segments_to_markdown,
    segments_to_plain_text,
    segments_to_srt
)
from utils.gpu_monitor import get_full_gpu_status, get_gpu_processes

# Configuration
DEFAULT_LANGUAGES: List[tuple[str, str]] = [
    ("auto", "Automatic"),
    ("en", "English"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("it", "Italian"),
    ("pt", "Portuguese"),
    ("ru", "Russian"),
    ("zh", "Chinese"),
    ("ja", "Japanese"),
]

MODEL_NAME = os.getenv("WHISPER_MODEL", "small")
DEFAULT_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
DEFAULT_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float32")
GPU_DEVICE = os.getenv("WHISPER_GPU_DEVICE", "cuda")
GPU_COMPUTE_TYPE = os.getenv("WHISPER_GPU_COMPUTE_TYPE", "float16")
CPU_DEVICE = os.getenv("WHISPER_CPU_DEVICE", "cpu")
CPU_COMPUTE_TYPE = os.getenv("WHISPER_CPU_COMPUTE_TYPE", DEFAULT_COMPUTE_TYPE)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# Diarization settings
ENABLE_ONDEMAND_DIARIZATION = os.getenv("ENABLE_ONDEMAND_DIARIZATION", "true").lower() in {"1", "true", "yes"}
MIN_SPEAKERS = int(os.getenv("MIN_SPEAKERS", "1"))
MAX_SPEAKERS = int(os.getenv("MAX_SPEAKERS", "10"))


def _detect_cuda_device_count() -> int:
    try:
        import ctranslate2
        return int(ctranslate2.get_cuda_device_count())
    except Exception as exc:
        _diagnostic_notes.append(f"CUDA device probe failed: {exc}")
        return 0


def _unique_dirs(paths: Sequence[str]) -> List[str]:
    seen: List[str] = []
    for path in paths:
        if path and path not in seen:
            seen.append(path)
    return seen


def _cudnn_libraries_present() -> bool:
    candidate_dirs: List[str] = [
        "/lib/x86_64-linux-gnu",
        "/usr/lib/x86_64-linux-gnu",
        "/usr/lib64",
        "/usr/local/cuda/lib64",
    ]

    ld_library_path = os.getenv("LD_LIBRARY_PATH")
    if ld_library_path:
        candidate_dirs.extend(part for part in ld_library_path.split(":"))

    conda_prefix = os.getenv("CONDA_PREFIX")
    if conda_prefix:
        candidate_dirs.append(os.path.join(conda_prefix, "lib"))

    if site is not None:
        site_dirs: List[str] = []
        try:
            site_dirs.extend(site.getsitepackages())
        except Exception:
            pass
        try:
            user_site = site.getusersitepackages()
            if isinstance(user_site, str):
                site_dirs.append(user_site)
            else:
                site_dirs.extend(user_site)
        except Exception:
            pass

        candidate_dirs.extend(
            os.path.join(base, "nvidia", "cudnn", "lib") for base in site_dirs
        )

    extra_dirs = os.getenv("CUDNN_EXTRA_LIB_DIRS")
    if extra_dirs:
        candidate_dirs.extend(part.strip() for part in extra_dirs.split(":") if part.strip())

    patterns = ("libcudnn.so*", "libcudnn_ops_infer.so*", "libcudnn_ops_train.so*")
    search_patterns: List[str] = []
    for directory in _unique_dirs(candidate_dirs):
        if not directory or not os.path.isdir(directory):
            continue
        search_patterns.extend(os.path.join(directory, pattern) for pattern in patterns)

    return any(glob(pattern) for pattern in search_patterns)


_cuda_device_count = _detect_cuda_device_count()
_cudnn_available = _cudnn_libraries_present()
_gpu_supported = _cuda_device_count > 0 and _cudnn_available

if not _gpu_supported and GPU_DEVICE.lower() != "cpu":
    _diagnostic_notes.append(
        "GPU execution disabled (missing CUDA device or cuDNN); defaulting to CPU mode."
    )
    DEFAULT_DEVICE = CPU_DEVICE = "cpu"

if not _gpu_supported:
    GPU_DEVICE = "cpu"

if not _cudnn_available and "float16" in GPU_COMPUTE_TYPE.lower():
    fallback_compute = os.getenv("WHISPER_GPU_FALLBACK_COMPUTE_TYPE", "int8_float32")
    if "float16" in fallback_compute.lower():
        fallback_compute = "float32"
    _diagnostic_notes.append(
        "cuDNN libraries missing; forcing GPU compute_type to %s" % fallback_compute
    )
    GPU_COMPUTE_TYPE = fallback_compute

VAD_ENABLED = os.getenv("WHISPER_VAD", "true").lower() in {"1", "true", "yes"}
DEFAULT_BEAM_SIZE = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
DEFAULT_TEMPERATURE = float(os.getenv("WHISPER_TEMPERATURE", "0.0"))
DEFAULT_LANGUAGE = os.getenv("WHISPER_DEFAULT_LANGUAGE", "auto")
ASSET_VERSION = os.getenv("FLASK_ASSET_VERSION") or str(int(time.time()))
_USE_GPU_FLAG = os.getenv(
    "WHISPER_DEFAULT_USE_GPU",
    os.getenv("WHISPER_USE_GPU_DEFAULT", "auto"),
)


def _str_to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


DEFAULT_USE_GPU = _str_to_bool(
    _USE_GPU_FLAG,
    default=_gpu_supported and (DEFAULT_DEVICE.lower() != "cpu" or GPU_DEVICE.lower() != "cpu"),
)

AVAILABLE_MODELS = [
    model.strip()
    for model in os.getenv(
        "WHISPER_AVAILABLE_MODELS",
        "tiny,base,small,medium,large-v2",
    ).split(",")
    if model.strip()
]

if MODEL_NAME not in AVAILABLE_MODELS:
    AVAILABLE_MODELS.insert(0, MODEL_NAME)

OUTPUT_DIR = Path(os.getenv("TRANSCRIPTION_OUTPUT_DIR", "./transcriptions")).resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

USER_IDENTITY_HEADER = os.getenv(
    "TRANSCRIBER_USER_HEADER",
    os.getenv("CF_ACCESS_USER_HEADER", "CF-Access-Authenticated-User-Email"),
)
ALT_USER_HEADER = os.getenv("TRANSCRIBER_ALT_USER_HEADER", "X-Transcriber-User")
REQUIRE_USER_HEADER = _str_to_bool(os.getenv("TRANSCRIBER_REQUIRE_AUTH", "false"), default=False)
DEFAULT_USER_IDENTIFIER = os.getenv("TRANSCRIBER_DEFAULT_USER", "shared") or "shared"

_USER_SLUG_PATTERN = re.compile(r"[^a-z0-9._-]+")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

if _diagnostic_notes:
    for note in _diagnostic_notes:
        app.logger.warning("[startup] %s", note)

_MODEL_CACHE: Dict[Tuple[str, str, str], WhisperModel] = {}


def _resolve_device_choice(use_gpu: bool) -> Tuple[str, str]:
    if use_gpu and _gpu_supported and GPU_DEVICE.lower() != "cpu":
        return GPU_DEVICE, GPU_COMPUTE_TYPE
    return CPU_DEVICE, CPU_COMPUTE_TYPE


def _get_model(model_name: str, device: str, compute_type: str) -> WhisperModel:
    """Initialise Whisper model lazily and cache per (model, device, compute)."""
    cache_key = (model_name, device, compute_type)
    model = _MODEL_CACHE.get(cache_key)
    if model is None:
        app.logger.info(
            "Loading faster-whisper model '%s' on device=%s (compute_type=%s)",
            model_name,
            device,
            compute_type,
        )
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
        _MODEL_CACHE[cache_key] = model
    return model


@app.route("/favicon.ico")
def favicon():
    return send_file("static/favicon.ico", mimetype="image/vnd.microsoft.icon")


@app.route("/")
def index():
    return render_template(
        "index.html",
        model_name=MODEL_NAME,
        available_models=AVAILABLE_MODELS,
        default_language=DEFAULT_LANGUAGE,
        beam_size=DEFAULT_BEAM_SIZE,
        temperature=DEFAULT_TEMPERATURE,
        languages=DEFAULT_LANGUAGES,
        asset_version=ASSET_VERSION,
        default_use_gpu=DEFAULT_USE_GPU,
        diagnostic_notes=_diagnostic_notes,
        gpu_supported=_gpu_supported,
        openai_enabled=bool(OPENAI_API_KEY),
        assemblyai_enabled=bool(ASSEMBLYAI_API_KEY),
        local_diarization_enabled=ENABLE_ONDEMAND_DIARIZATION and bool(HF_TOKEN),
        min_speakers=MIN_SPEAKERS,
        max_speakers=MAX_SPEAKERS,
    )


@app.post("/transcribe")
def transcribe():
    try:
        user_identifier, user_output_dir = _resolve_current_user_dir(create=True)
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 401

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided."}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    filename = secure_filename(audio_file.filename) or "recording.wav"
    suffix = Path(filename).suffix or ".wav"

    # Get transcription backend
    backend = request.form.get("backend", "local").strip()
    
    # Get diarization settings
    diarization_mode = request.form.get("diarization", "off").strip()
    min_speakers = int(request.form.get("min_speakers", MIN_SPEAKERS))
    max_speakers = int(request.form.get("max_speakers", MAX_SPEAKERS))
    
    # Get other settings
    requested_model = request.form.get("model", MODEL_NAME).strip() or MODEL_NAME
    translate = request.form.get("translate", "false").lower() == "true"
    language = request.form.get("language", DEFAULT_LANGUAGE)
    temperature = float(request.form.get("temperature", DEFAULT_TEMPERATURE))
    beam_size = int(request.form.get("beam_size", DEFAULT_BEAM_SIZE))
    use_gpu_requested = _str_to_bool(
        request.form.get("use_gpu"), default=DEFAULT_USE_GPU
    )

    tmp_path: Optional[Path] = None
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            audio_file.save(tmp)
            tmp_path = Path(tmp.name)

        # Process based on backend and diarization
        if backend == "openai":
            result = _transcribe_openai(tmp_path, language, temperature)
        elif diarization_mode == "assemblyai":
            # Use AssemblyAI for both transcription and diarization
            result = _transcribe_assemblyai(tmp_path, min_speakers, max_speakers)
        else:  # local
            result = _transcribe_local(
                tmp_path,
                requested_model,
                language,
                temperature,
                beam_size,
                translate,
                use_gpu_requested,
                diarization_mode,
                min_speakers,
                max_speakers
            )

        # Save outputs in multiple formats
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        base_name = f"{timestamp}_{Path(filename).stem or 'audio'}"
        
        # Generate all formats
        txt_path = user_output_dir / f"{base_name}.txt"
        md_path = user_output_dir / f"{base_name}.md"
        srt_path = user_output_dir / f"{base_name}.srt"
        
        segments = result.get("segments", [])
        has_speakers = any("speaker" in seg for seg in segments)
        
        # Plain text - NO timestamps for non-diarized
        txt_content = segments_to_plain_text(segments, include_timestamps=False, include_speakers=has_speakers)
        txt_path.write_text(txt_content + "\n", encoding="utf-8")
        
        # Markdown - timestamps only for diarized
        md_content = segments_to_markdown(segments, include_timestamps=has_speakers, include_speakers=has_speakers)
        md_path.write_text(md_content + "\n", encoding="utf-8")
        
        # SRT subtitles
        srt_content = segments_to_srt(segments)
        srt_path.write_text(srt_content, encoding="utf-8")

        response = {
            "transcript": result.get("text", ""),
            "markdown": md_content,
            "metadata": result.get("metadata", {}),
            "downloads": {
                "text": request.host_url.rstrip("/") + app.url_for("download_file", filename=txt_path.name),
                "markdown": request.host_url.rstrip("/") + app.url_for("download_file", filename=md_path.name),
                "srt": request.host_url.rstrip("/") + app.url_for("download_file", filename=srt_path.name),
            },
        }
        return jsonify(response)
        
    except Exception as exc:
        app.logger.exception("Transcription failed")
        return jsonify({"error": f"Transcription failed: {exc}"}), 500
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _transcribe_local(
    audio_path: Path,
    model_name: str,
    language: str,
    temperature: float,
    beam_size: int,
    translate: bool,
    use_gpu: bool,
    diarization_mode: str,
    min_speakers: int,
    max_speakers: int
) -> Dict:
    """Transcribe using local faster-whisper"""
    
    if model_name not in AVAILABLE_MODELS:
        raise ValueError(f"Unsupported model: {model_name}")
    
    desired_device, desired_compute = _resolve_device_choice(use_gpu)
    actual_device = desired_device
    actual_compute = desired_compute
    actual_use_gpu = desired_device.lower() != CPU_DEVICE.lower()

    task_mode = "translate" if translate else "transcribe"
    picked_language = None if language in {"", "auto", "Automatic"} else language

    try:
        model = _get_model(model_name, desired_device, desired_compute)
    except (RuntimeError, ValueError) as exc:
        if use_gpu:
            app.logger.warning(
                "GPU load failed for model '%s'. Falling back to CPU. Error: %s",
                model_name,
                exc,
            )
            actual_use_gpu = False
            actual_device, actual_compute = _resolve_device_choice(False)
            model = _get_model(model_name, actual_device, actual_compute)
        else:
            raise

    segments_iter, info = model.transcribe(
        str(audio_path),
        temperature=temperature,
        beam_size=beam_size,
        vad_filter=VAD_ENABLED,
        task=task_mode,
        language=picked_language,
        compression_ratio_threshold=2.4,
        no_speech_threshold=0.6,
    )

    segments_list = list(segments_iter)
    
    # Convert to dict format
    segments = [
        {
            "start": seg.start,
            "end": seg.end,
            "text": seg.text
        }
        for seg in segments_list
    ]
    
    transcript_text = "".join(seg["text"] for seg in segments).strip()

    # Handle diarization if requested
    if diarization_mode == "local" and HF_TOKEN:
        try:
            app.logger.info("Starting local diarization...")
            diar_segments = diarize_audio(
                str(audio_path),
                HF_TOKEN,
                min_speakers=min_speakers if min_speakers > 0 else None,
                max_speakers=max_speakers if max_speakers > 0 else None,
                device="cuda" if actual_use_gpu else "cpu",
                auto_unload=True
            )
            segments = assign_speakers_to_segments(segments, diar_segments)
            app.logger.info("Local diarization complete")
        except Exception as e:
            error_msg = str(e)
            app.logger.error(f"Local diarization failed: {error_msg}")
            
            # Check if it's an access/authentication error
            if "403" in error_msg or "authorized" in error_msg.lower() or "gated" in error_msg.lower():
                raise Exception(
                    "Access denied to diarization model. Please:\n"
                    "1. Visit https://huggingface.co/pyannote/speaker-diarization-3.1\n"
                    "2. Accept the model terms\n"
                    "3. Verify your HF_TOKEN has access"
                )
            else:
                raise Exception(f"Diarization failed: {error_msg}")

    detected_language = info.language or picked_language or "unknown"
    
    return {
        "text": transcript_text,
        "segments": segments,
        "metadata": {
            "user": request.headers.get(USER_IDENTITY_HEADER, DEFAULT_USER_IDENTIFIER),
            "backend": "local",
            "model": model_name,
            "device": actual_device,
            "compute_type": actual_compute,
            "gpu_requested": use_gpu,
            "gpu_used": actual_use_gpu,
            "detected_language": detected_language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "temperature": temperature,
            "beam_size": beam_size,
            "task": task_mode,
            "diarization": diarization_mode,
        }
    }


def _transcribe_openai(audio_path: Path, language: str, temperature: float) -> Dict:
    """Transcribe using OpenAI API"""
    
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    result = transcribe_with_openai(
        str(audio_path),
        OPENAI_API_KEY,
        language=language if language not in {"", "auto"} else None,
        temperature=temperature
    )
    
    return {
        "text": result.get("text", ""),
        "segments": result.get("segments", []),
        "metadata": {
            "backend": "openai",
            "model": "whisper-1",
            "detected_language": result.get("language", "unknown"),
            "duration": result.get("duration", 0),
        }
    }


def _transcribe_assemblyai(audio_path: Path, min_speakers: int, max_speakers: int) -> Dict:
    """Transcribe and diarize using AssemblyAI"""
    
    if not ASSEMBLYAI_API_KEY:
        raise ValueError("AssemblyAI API key not configured")
    
    result = diarize_with_assemblyai(
        str(audio_path),
        ASSEMBLYAI_API_KEY,
        min_speakers=min_speakers if min_speakers > 0 else None,
        max_speakers=max_speakers if max_speakers > 0 else None
    )
    
    return {
        "text": result.get("text", ""),
        "segments": result.get("segments", []),
        "metadata": {
            "backend": "assemblyai",
            "speakers_detected": result.get("speakers_detected", 0),
        }
    }


@app.get("/download/<path:filename>")
def download_file(filename: str):
    try:
        _, user_output_dir = _resolve_current_user_dir(create=False)
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 401

    safe_path = safe_join(user_output_dir, filename)
    if safe_path is None or not Path(safe_path).exists():
        return jsonify({"error": "File not found."}), 404
    return send_file(safe_path, as_attachment=True)


@app.get("/healthz")
def healthcheck():
    vram = get_vram_usage()
    
    payload = {
        "status": "ok",
        "model": MODEL_NAME,
        "default_device": DEFAULT_DEVICE,
        "gpu_supported": _gpu_supported,
        "diagnostic_notes": _diagnostic_notes,
        "uptime_seconds": max(time.time() - _app_start_time, 0.0),
        "requires_auth": REQUIRE_USER_HEADER,
        "backends": {
            "local": True,
            "openai": bool(OPENAI_API_KEY),
            "assemblyai": bool(ASSEMBLYAI_API_KEY),
        },
        "diarization": {
            "local": ENABLE_ONDEMAND_DIARIZATION and bool(HF_TOKEN),
            "model_loaded": is_diarization_loaded(),
            "vram": vram,
        }
    }
    return jsonify(payload), 200


@app.post("/diarization/unload")
def unload_diarization():
    """Manually unload diarization model to free VRAM"""
    try:
        unload_diarization_model()
        vram = get_vram_usage()
        return jsonify({
            "status": "success",
            "message": "Diarization model unloaded",
            "vram": vram
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/whisper/unload")
def unload_whisper():
    """Manually unload Whisper models to free VRAM
    
    NOTE: This only affects the current worker process.
    With multiple Gunicorn workers, use /restart endpoint for full cleanup.
    """
    global _MODEL_CACHE
    
    try:
        import gc
        import torch
        import os
        
        models_unloaded = len(_MODEL_CACHE)
        
        # Clear all cached models in THIS worker
        _MODEL_CACHE.clear()
        
        # Force garbage collection
        gc.collect()
        
        # Clear CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        app.logger.info(f"Worker {os.getpid()}: Unloaded {models_unloaded} Whisper model(s)")
        
        # Get updated VRAM status
        from utils.gpu_monitor import get_full_gpu_status
        gpu_status = get_full_gpu_status()
        
        return jsonify({
            "status": "success",
            "message": f"Unloaded from worker {os.getpid()}. Use 'Restart Service' for full cleanup.",
            "models_unloaded": models_unloaded,
            "worker_pid": os.getpid(),
            "gpu_status": gpu_status
        })
    except Exception as e:
        app.logger.error(f"Failed to unload Whisper models: {e}")
        return jsonify({"error": str(e)}), 500


@app.post("/service/restart")
def restart_service():
    """Restart the Gunicorn service to fully clear all models from VRAM
    
    This triggers a graceful restart of all workers.
    """
    try:
        import os
        import signal
        import subprocess
        
        # Get the master Gunicorn PID
        result = subprocess.run(
            ['pgrep', '-f', 'gunicorn.*app:app'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]
        
        if not pids:
            return jsonify({"error": "Could not find Gunicorn processes"}), 500
        
        # Find the master process (parent of workers)
        master_pid = min(pids)  # Usually the lowest PID is the master
        
        app.logger.info(f"Sending HUP signal to Gunicorn master: {master_pid}")
        
        # Send HUP signal for graceful restart
        os.kill(master_pid, signal.SIGHUP)
        
        return jsonify({
            "status": "success",
            "message": "Service restart initiated. Workers will reload gracefully.",
            "master_pid": master_pid
        })
        
    except Exception as e:
        app.logger.error(f"Failed to restart service: {e}")
        return jsonify({"error": str(e)}), 500


@app.get("/gpu/status")
def gpu_status():
    """Get current GPU status including VRAM usage and processes"""
    try:
        from utils.gpu_monitor import get_full_gpu_status
        
        status = get_full_gpu_status()
        status['whisper_models_loaded'] = len(_MODEL_CACHE)
        status['diarization_loaded'] = is_diarization_loaded()
        
        return jsonify(status)
    except Exception as e:
        app.logger.error(f"Failed to get GPU status: {e}")
        return jsonify({"error": str(e), "available": False}), 500


def _resolve_current_user_dir(create: bool = False) -> Tuple[str, Path]:
    """Resolve the authenticated user's storage directory."""
    
    header_value = (request.headers.get(USER_IDENTITY_HEADER) or "").strip()
    if not header_value and ALT_USER_HEADER:
        header_value = (request.headers.get(ALT_USER_HEADER) or "").strip()

    if not header_value:
        if REQUIRE_USER_HEADER:
            raise PermissionError(
                "Missing authenticated user header. Access requires Cloudflare Access or a trusted proxy."
            )
        header_value = DEFAULT_USER_IDENTIFIER

    normalized = header_value.strip().lower()
    if not normalized:
        normalized = DEFAULT_USER_IDENTIFIER

    slug = _USER_SLUG_PATTERN.sub("-", normalized)
    slug = slug.strip("-._") or "user"

    user_dir = OUTPUT_DIR / slug
    if create:
        user_dir.mkdir(parents=True, exist_ok=True)

    return header_value, user_dir


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"},
    )
