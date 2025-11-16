# Transcriber Setup Guide

## Overview
This is a unified transcription system with:
- ✅ Self-hosted Whisper (GPU-accelerated)
- ✅ OpenAI Whisper API integration
- ✅ AssemblyAI diarization API
- ✅ On-demand local diarization (pyannote)
- ✅ Modern, clean UI
- ✅ Markdown output with speaker labels
- ✅ One-click copy to clipboard

## Prerequisites

1. Python 3.10+ with venv
2. NVIDIA GPU with CUDA 12.0+ (for GPU acceleration)
3. cuDNN 9.x libraries
4. API keys (optional):
   - OpenAI API key (for OpenAI Whisper)
   - AssemblyAI API key (for cloud diarization)
   - Hugging Face token (for local pyannote diarization)

## Installation

### 1. Create and activate virtual environment

```bash
cd /home/ben/SolWorkingFolder/CustomSoftware/transcriber/flask-app
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
nano .env
```

**Required settings:**
- Update API keys as needed (OpenAI, AssemblyAI, Hugging Face)
- Verify GPU settings match your hardware

**Key variables:**
```bash
# OpenAI (optional)
OPENAI_API_KEY=sk-...

# AssemblyAI (optional)
ASSEMBLYAI_API_KEY=...

# Hugging Face for pyannote (optional)
HF_TOKEN=hf_...

# GPU settings
WHISPER_DEVICE=cuda
CT2_USE_CUDNN=1
```

### 4. Test the application

```bash
# Development mode
python app.py
```

Visit: http://localhost:5000

### 5. Install as systemd service (production)

```bash
# Create log directory
sudo mkdir -p /var/log/transcriber
sudo chown ben:ben /var/log/transcriber

# Install service
sudo cp transcriber.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable transcriber
sudo systemctl start transcriber

# Check status
sudo systemctl status transcriber

# View logs
sudo journalctl -u transcriber -f
```

## Usage

### Web Interface

1. **Upload or Record Audio**
   - Upload file or use browser microphone
   - Supports WAV, MP3, M4A, WebM, etc.

2. **Choose Backend**
   - **Self-Hosted**: GPU-accelerated, free, private
   - **OpenAI API**: Cloud-based, requires API key
   - **AssemblyAI**: Cloud diarization included

3. **Enable Diarization** (optional)
   - **Local**: Uses VRAM, auto-loads/unloads
   - **AssemblyAI**: Cloud-based, no VRAM usage

4. **Transcribe**
   - Click "Transcribe Audio"
   - Results show in Markdown format
   - One-click copy to clipboard
   - Download in TXT, MD, or SRT format

### API Endpoints

**Health Check:**
```bash
curl http://localhost:5000/healthz
```

**Transcribe:**
```bash
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@recording.mp3" \
  -F "backend=local" \
  -F "model=small" \
  -F "use_gpu=true" \
  -F "diarization=local"
```

**Unload Diarization Model:**
```bash
curl -X POST http://localhost:5000/diarization/unload
```

## Troubleshooting

### GPU not detected
- Verify CUDA installation: `nvidia-smi`
- Check cuDNN libraries: see `docs/cuDNN-upgrade-plan.md`
- Verify environment variable: `CT2_USE_CUDNN=1`

### Diarization VRAM issues
- Use `diarization=off` for transcription only
- Or use `backend=assemblyai_diarize` for cloud diarization
- Monitor VRAM: check `/healthz` endpoint

### Service won't start
- Check logs: `sudo journalctl -u transcriber -n 50`
- Verify .env file exists and is readable
- Ensure virtual environment has all dependencies

## Development

### Run in development mode

```bash
source .venv/bin/activate
export FLASK_DEBUG=true
python app.py
```

### Update dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Add new features

The codebase is modular:
- `app.py` - Main Flask application
- `utils/diarization.py` - Local diarization with VRAM management
- `utils/api_backends.py` - OpenAI and AssemblyAI integrations
- `utils/formatters.py` - Output format converters
- `templates/index.html` - Modern UI

## Production Deployment

Current production setup (from playbook):
- Application: Sol (192.168.50.10:5000)
- Reverse Proxy: lunanode4 (Caddy)
- Public URL: https://transcriber.solfamily.group

Service is managed by systemd and auto-restarts on failure.

## Support

For issues or questions, check:
- `docs/` folder for detailed documentation
- System logs: `/var/log/transcriber/`
- GPU status: `nvidia-smi`
- Service status: `sudo systemctl status transcriber`
