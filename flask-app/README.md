# 🎙️ Transcriber - Unified AI Transcription System

A professional-grade audio transcription system with multiple backends, speaker diarization, and a beautiful modern UI.

## ✨ Features

### 🎯 Core Capabilities
- **Multi-Backend Support**
  - Self-hosted Whisper (GPU-accelerated with faster-whisper)
  - OpenAI Whisper API (cloud-based)
  - AssemblyAI (cloud with built-in diarization)

- **Smart Speaker Diarization**
  - Local pyannote (loads on-demand, auto-unloads VRAM)
  - AssemblyAI API (cloud-based, no VRAM usage)
  - Configurable min/max speakers

- **Modern UI**
  - Clean, custom HTML/CSS design
  - Dark theme with smooth animations
  - Tab-based organization
  - Real-time status updates
  - Mobile-responsive

- **Output Formats**
  - Plain text (.txt)
  - Markdown (.md) with speaker labels
  - Subtitles (.srt) for video editing
  - One-click copy to clipboard

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd flask-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

Add your API keys (all optional):
```bash
OPENAI_API_KEY=sk-...          # For OpenAI backend
ASSEMBLYAI_API_KEY=...         # For AssemblyAI backend
HF_TOKEN=hf_...                # For local diarization
```

### 3. Run

**Development:**
```bash
python app.py
```

**Production:**
```bash
sudo cp transcriber.service /etc/systemd/system/
sudo systemctl enable --now transcriber
```

Visit: http://localhost:5000

## 📖 Documentation

- **[SETUP.md](SETUP.md)** - Complete installation guide
- **[WHATS_NEW.md](WHATS_NEW.md)** - New features overview
- **[.env.example](.env.example)** - Configuration reference

## 🎯 Usage

### Via Web UI

1. **Upload or Record** - Choose audio file or record via microphone
2. **Select Backend**
   - Local: Fast, free, private (GPU required)
   - OpenAI: Cloud, requires API key
   - AssemblyAI: Cloud with diarization
3. **Configure Options**
   - Model size (tiny to large-v3)
   - Language (auto-detect or specify)
   - Diarization (local VRAM or API)
   - Speaker count
4. **Transcribe** - Get results in Markdown format
5. **Copy/Download** - One-click copy or download files

### Via API

```bash
# Transcribe with local backend
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@recording.mp3" \
  -F "backend=local" \
  -F "model=small" \
  -F "use_gpu=true"

# Transcribe with diarization
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@meeting.wav" \
  -F "backend=local" \
  -F "diarization=local" \
  -F "min_speakers=2" \
  -F "max_speakers=5"

# Health check
curl http://localhost:5000/healthz
```

## 🔧 Architecture

```
flask-app/
├── app.py                 # Main Flask application
├── utils/
│   ├── diarization.py     # On-demand pyannote with VRAM mgmt
│   ├── api_backends.py    # OpenAI & AssemblyAI integrations
│   └── formatters.py      # Markdown, TXT, SRT formatters
├── templates/
│   └── index.html         # Modern UI
├── .env                   # Configuration (create from .env.example)
├── requirements.txt       # Python dependencies
└── transcriber.service    # Systemd service file
```

## 🎨 UI Features

- **Dark Theme** - Easy on the eyes
- **Tab Organization** - Backend / Diarization / Advanced
- **Real-time Feedback** - Progress spinner, status messages
- **One-Click Copy** - Copy Markdown to clipboard instantly
- **Responsive Design** - Works on mobile and desktop
- **GPU Status** - Shows GPU availability and usage

## ⚡ Performance

| Backend | Speed | Quality | Privacy | Cost | Diarization |
|---------|-------|---------|---------|------|-------------|
| **Local** | ⚡⚡⚡ | Excellent | 100% | Free | On-demand |
| **OpenAI** | ⚡⚡ | Excellent | Cloud | ~$0.006/min | ❌ |
| **AssemblyAI** | ⚡⚡ | Excellent | Cloud | ~$0.025/min | ✅ Built-in |

## 🧪 Testing

Run the installation test:

```bash
./test_install.sh
```

## 🐛 Troubleshooting

**GPU not detected?**
- Check: `nvidia-smi`
- Verify cuDNN 9.x installed
- Set `CT2_USE_CUDNN=1` in `.env`

**Diarization using VRAM?**
- Local diarization auto-unloads after processing
- Manually unload: `curl -X POST http://localhost:5000/diarization/unload`
- Or use AssemblyAI backend (no VRAM)

**Dependencies won't install?**
- Ensure Python 3.10+
- Update pip: `pip install --upgrade pip`
- Install PyTorch first: `pip install torch`

**Service won't start?**
- Check logs: `sudo journalctl -u transcriber -n 50`
- Verify `.env` exists and is readable
- Ensure paths in `transcriber.service` are correct

## 📊 System Requirements

**Minimum:**
- Python 3.10+
- 4GB RAM
- CPU transcription

**Recommended:**
- Python 3.12
- 16GB RAM
- NVIDIA GPU with 8GB+ VRAM
- CUDA 12.0+
- cuDNN 9.x

## 🔐 Privacy

- **Local backend**: 100% private, nothing leaves your machine
- **OpenAI API**: Audio sent to OpenAI servers
- **AssemblyAI**: Audio sent to AssemblyAI servers

Choose local backend for sensitive content!

## 📝 License

Private project - all rights reserved.

## 🙏 Credits

Built with:
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Local transcription
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) - Speaker diarization
- [OpenAI API](https://platform.openai.com/) - Cloud transcription
- [AssemblyAI](https://www.assemblyai.com/) - Cloud diarization

---

**Built for Sol Family Group - Your personal transcription powerhouse!** 🚀
