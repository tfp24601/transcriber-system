# Flask Whisper Transcriber

Welcome! This repository centers on the **GPU-accelerated Flask transcription app** located in `flask-app/`. All prior implementations (PWA, n8n workflows, Docker stack, etc.) have been archived under `old/legacy-stack/` and are kept for historical reference only. New contributors and AI agents should focus exclusively on the Flask code unless instructed otherwise.

> 🔎 **First step for any new agent:** Review `.github/copilot-instructions.md`. It contains up-to-date guardrails, workflow expectations, and deployment goals tailored to this Flask app.

## Repository layout

| Path | Purpose |
| --- | --- |
| `flask-app/` | Active Flask project (app code, templates, static assets, virtualenv). |
| `docs/gpu-acceleration-milestone.md` | Milestone notes describing the September 2025 GPU enablement work and validation steps. |
| `old/legacy-stack/` | Archived monorepo with the deprecated PWA/n8n/Docker implementation—treat as read-only unless explicitly revived. |
| `docs/` (other files) | Additional documentation supporting the Flask app. |

If you need a refresher on the legacy architecture, browse `old/legacy-stack/`, but do not modify it.

A lightweight Flask application that lets you upload or record audio directly in the browser and obtain a transcript using [faster-whisper](https://github.com/guillaumekln/faster-whisper).

The server exposes a minimal web UI (served from `/`) and a JSON transcription endpoint at `/transcribe`. Transcripts and SRT caption files are stored locally so you can download them later.

## Onboarding checklist for fresh agents

1. Read `.github/copilot-instructions.md` for project guardrails and daily workflow.
2. Skim `docs/gpu-acceleration-milestone.md` to understand the current environment (cuDNN 9, CUDA 12.4, RTX 4090).
3. Confirm you can run the local server using the virtual environment inside `flask-app/` (instructions below).
4. Verify GPU operation by calling `/transcribe` with `use_gpu=true` and checking for `"gpu_used": true` in the response.
5. Avoid legacy sync scripts unless a task explicitly reintroduces them; use standard git workflows instead.

## Features

- Upload existing audio files (`.mp3`, `.wav`, etc.)
- Record audio in the browser via the MediaRecorder API (Chrome, Edge, Firefox)
- Configure Whisper options (language, translation toggle, beam size, temperature, GPU toggle)
- Switch Whisper models on the fly from the UI (tiny → large)
- Download generated `.txt` and `.srt` files
- Real-time VRAM usage monitor for GPU inference tracking
- CPU-friendly defaults with optional GPU / custom model configuration via environment variables

## Prerequisites

- Python 3.10+
- `ffmpeg` available on your system (required by faster-whisper for certain formats)
- Optional: NVIDIA GPU with the appropriate drivers and CUDA libraries if you want GPU inference

## Quick start

```bash
cd flask-app
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

The server listens on <http://0.0.0.0:5000> by default. Open <http://localhost:5000> in your browser, record or upload audio, tweak the options, and click **Transcribe**.

## Configuration

All configuration is handled through environment variables so you can tweak behaviour without editing the code:

| Variable | Description | Default |
| --- | --- | --- |
| `WHISPER_MODEL` | Default faster-whisper model (`tiny`, `base`, `small`, `medium`, `large-v3`, custom path). | `small` |
| `WHISPER_AVAILABLE_MODELS` | Comma-separated list of models exposed in the UI dropdown. | `tiny,base,small,medium,large-v2` |
| `WHISPER_DEVICE` | Legacy default inference device (`cpu`, `cuda`, `auto`). | `cpu` |
| `WHISPER_COMPUTE_TYPE` | Legacy compute precision (`float32`, `float16`, etc.). | `float32` |
| `WHISPER_DEFAULT_USE_GPU` | Set `true`/`false`/`auto` for the UI checkbox default. | `auto` (true if GPU configured) |
| `WHISPER_GPU_DEVICE` | Device string used when GPU is enabled. | `cuda` |
| `WHISPER_GPU_COMPUTE_TYPE` | Compute precision when GPU is enabled. | `float16` |
| `WHISPER_CPU_DEVICE` | Device string used when GPU toggle is off. | `cpu` |
| `WHISPER_CPU_COMPUTE_TYPE` | Compute precision when GPU toggle is off. | `float32` |
| `WHISPER_VAD` | Whether to enable the built-in VAD filter (`true`/`false`). | `true` |
| `WHISPER_BEAM_SIZE` | Default beam size shown in the UI. | `5` |
| `WHISPER_TEMPERATURE` | Default temperature shown in the UI. | `0.0` |
| `WHISPER_DEFAULT_LANGUAGE` | Preselected language option in the UI (`auto`, `en`, `es`, …). | `auto` |
| `TRANSCRIPTION_OUTPUT_DIR` | Directory where transcripts/SRTs are stored. | `./transcriptions` |
| `FLASK_HOST` | Host interface for the server. | `0.0.0.0` |
| `FLASK_PORT` | Port for the server. | `5000` |
| `FLASK_DEBUG` | Enable Flask debug reloading (`true`/`false`). | `false` |

Export the variables before launching the app, e.g.:

```bash
export WHISPER_MODEL=large-v2
export WHISPER_DEFAULT_USE_GPU=true
export WHISPER_GPU_DEVICE=cuda
export WHISPER_GPU_COMPUTE_TYPE=float16
export WHISPER_CPU_COMPUTE_TYPE=float32
python app.py
```

## API usage

You can also use the `/transcribe` endpoint programmatically by POSTing `multipart/form-data`:

- `audio` (file): Audio binary
- `model` (string): Model name to load (`tiny`, `base`, etc.)
- `language` (string): Language code or `auto`
- `translate` (bool / string): `true` to translate to English
- `temperature` (float)
- `beam_size` (int)
- `use_gpu` (bool / string): `true` to run on the GPU (falls back to CPU if unavailable)

The response includes:

```json
{
  "transcript": "...",
  "metadata": {
    "model": "small",
  "device": "cuda",
  "compute_type": "float16",
  "gpu_requested": true,
  "gpu_used": true,
    "detected_language": "en",
    "language_probability": 0.98,
    "duration": 4.23,
    "temperature": 0,
    "beam_size": 5,
    "task": "transcribe"
  },
  "downloads": {
    "text": "http://localhost:5000/download/20250924-123456_sample.txt",
    "srt": "http://localhost:5000/download/20250924-123456_sample.srt"
  }
}
```

## Notes

- The first transcription request will download and load the Whisper model, which can take a few minutes depending on model size and hardware.
- Populate `TRANSCRIPTION_OUTPUT_DIR` with persistent storage (e.g., a mounted volume) if you are running inside Docker.
- The browser recording feature relies on HTTPS in some browsers; when testing locally over HTTP, Chrome/Edge allow access on `localhost` only.
- To free GPU/CPU memory between requests, restart the server—the model stays cached in memory for speed.
- For faster CPU inference, try `WHISPER_COMPUTE_TYPE=int8_float16` or `int8` (at some accuracy cost). For higher accuracy, switch to `medium` or `large-v2` using the dropdown or `WHISPER_MODEL` default.
