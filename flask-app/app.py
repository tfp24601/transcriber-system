import os
import tempfile
import time
from glob import glob
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import site
except Exception:  # pragma: no cover - extremely unlikely
    site = None

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename, safe_join

# Disable cuDNN by default to avoid missing library errors on GPU-first runs.
_ct2_use_cudnn_default = os.getenv("CT2_USE_CUDNN", "0")
os.environ.setdefault("CT2_USE_CUDNN", _ct2_use_cudnn_default)

_diagnostic_notes: List[str] = []

try:
    from faster_whisper import WhisperModel
except ImportError as exc:  # pragma: no cover - handled during setup
    raise SystemExit(
        "faster-whisper is required. Install dependencies with `pip install -r requirements.txt`."
    ) from exc


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


def _detect_cuda_device_count() -> int:
    try:
        import ctranslate2  # pylint: disable=import-error

        return int(ctranslate2.get_cuda_device_count())
    except Exception as exc:  # pragma: no cover - diagnostic only
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
        except Exception:  # pragma: no cover - diagnostic only
            pass
        try:
            user_site = site.getusersitepackages()
            if isinstance(user_site, str):
                site_dirs.append(user_site)
            else:
                site_dirs.extend(user_site)
        except Exception:  # pragma: no cover - diagnostic only
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

app = Flask(__name__)

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


def _format_timestamp(seconds: float) -> str:
    millis = int(seconds * 1000)
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _build_srt(segments: Iterable) -> str:
    blocks: List[str] = []
    for idx, segment in enumerate(segments, start=1):
        blocks.append(
            f"{idx}\n{_format_timestamp(segment.start)} --> {_format_timestamp(segment.end)}\n{segment.text.strip()}\n"
        )
    return "\n".join(blocks)


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
    )


@app.post("/transcribe")
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided."}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    filename = secure_filename(audio_file.filename) or "recording.wav"
    suffix = Path(filename).suffix or ".wav"

    requested_model = request.form.get("model", MODEL_NAME).strip() or MODEL_NAME
    if requested_model not in AVAILABLE_MODELS:
        return (
            jsonify(
                {
                    "error": "Unsupported model requested.",
                    "allowed_models": AVAILABLE_MODELS,
                }
            ),
            400,
        )

    translate = request.form.get("translate", "false").lower() == "true"
    language = request.form.get("language", DEFAULT_LANGUAGE)
    temperature = float(request.form.get("temperature", DEFAULT_TEMPERATURE))
    beam_size = int(request.form.get("beam_size", DEFAULT_BEAM_SIZE))
    use_gpu_requested = _str_to_bool(
        request.form.get("use_gpu"), default=DEFAULT_USE_GPU
    )

    desired_device, desired_compute = _resolve_device_choice(use_gpu_requested)
    actual_device = desired_device
    actual_compute = desired_compute
    actual_use_gpu = desired_device.lower() != CPU_DEVICE.lower()

    tmp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            audio_file.save(tmp)
            tmp_path = Path(tmp.name)

        task_mode = "translate" if translate else "transcribe"
        picked_language = None if language in {"", "auto", "Automatic"} else language

        try:
            model = _get_model(requested_model, desired_device, desired_compute)
        except (RuntimeError, ValueError) as exc:
            if use_gpu_requested:
                app.logger.warning(
                    "GPU load failed for model '%s'. Falling back to CPU. Error: %s",
                    requested_model,
                    exc,
                )
                actual_use_gpu = False
                actual_device, actual_compute = _resolve_device_choice(False)
                model = _get_model(requested_model, actual_device, actual_compute)
            else:
                raise

        segments, info = model.transcribe(
            str(tmp_path),
            temperature=temperature,
            beam_size=beam_size,
            vad_filter=VAD_ENABLED,
            task=task_mode,
            language=picked_language,
            compression_ratio_threshold=2.4,
            no_speech_threshold=0.6,
        )

        segments_list = list(segments)
        transcript_text = "".join(segment.text for segment in segments_list).strip()

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        base_name = f"{timestamp}_{Path(filename).stem or 'audio'}"
        txt_path = OUTPUT_DIR / f"{base_name}.txt"
        srt_path = OUTPUT_DIR / f"{base_name}.srt"

        txt_path.write_text(transcript_text + "\n", encoding="utf-8")
        srt_path.write_text(_build_srt(segments_list), encoding="utf-8")

        detected_language = info.language or picked_language or "unknown"
        response = {
            "transcript": transcript_text,
            "metadata": {
                "model": requested_model,
                "device": actual_device,
                "compute_type": actual_compute,
                "gpu_requested": use_gpu_requested,
                "gpu_used": actual_use_gpu,
                "detected_language": detected_language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "temperature": temperature,
                "beam_size": beam_size,
                "task": task_mode,
            },
            "downloads": {
                "text": request.host_url.rstrip("/")
                + app.url_for("download_file", filename=txt_path.name),
                "srt": request.host_url.rstrip("/")
                + app.url_for("download_file", filename=srt_path.name),
            },
        }
        return jsonify(response)
    except Exception as exc:  # pragma: no cover - defensive catch-all
        app.logger.exception("Transcription failed")
        return jsonify({"error": f"Transcription failed: {exc}"}), 500
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


@app.get("/download/<path:filename>")
def download_file(filename: str):
    safe_path = safe_join(OUTPUT_DIR, filename)
    if safe_path is None or not Path(safe_path).exists():
        return jsonify({"error": "File not found."}), 404
    return send_file(safe_path, as_attachment=True)


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"},
    )
