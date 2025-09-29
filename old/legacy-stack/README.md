# Transcriber System

A private, multi-user transcriber system that provides one-tap "record → send → read transcript" functionality on phones and desktop, with privacy-first design and decoupled architecture.

## 🎯 Overview

**Privacy-first transcription system** that keeps recording and transcription decoupled for reliability. Phones use native capture for screen-off recording, then upload to a web app which orchestrates transcription on your home server. No third-party cloud services - all audio stays on your infrastructure.

### Key Features

- **🔒 Privacy-first**: No third-party clouds; audio stored on Sol workstation
- **📱 Multi-platform**: Native recording on iOS/Android, web interface for all platforms
- **👤👥 Dual modes**: Single-speaker (highest accuracy) and multi-speaker (with diarization)
- **🔄 Reliable**: Resumable uploads, background-safe recording, idempotent jobs
- **👥 Multi-user**: Simple auth via Cloudflare Access, per-user storage and history

## 🏗 Architecture

### Client Applications
- **Web PWA**: Main interface at `transcriber.solfamily.group`
- **iOS**: Native recording via Shortcuts app integration
- **Android**: Custom "Recorder Bridge" app with deep linking
- **Desktop**: File upload with optional local recording

### Server Infrastructure
- **Authentication**: Development mode with query parameter fallback (Cloudflare Access planned)
- **Reverse Proxy**: Caddy with security headers and routing
- **Orchestration**: n8n workflows for ingest and processing
- **Transcription**: Faster-Whisper (GPU) + WhisperX for diarization
- **Storage**: Postgres for metadata, local filesystem for audio/transcripts
- **Uploads**: Optional Tus resumable upload server

## 🛠 Technical Stack

- **Frontend**: TypeScript + React/Vite (implemented)
- **Mobile**: Kotlin (Android), iOS Shortcuts (planned)
- **Backend**: n8n, Faster-Whisper, WhisperX
- **Database**: PostgreSQL
- **Infrastructure**: Docker Compose, Caddy, Cloudflared
- **GPU**: RTX 4090 for real-time transcription

## ⚙️ Runtime Modes

- The Flask preview app automatically falls back to CPU inference when CUDA or cuDNN is unavailable. The startup diagnostics are surfaced in the web UI so operators immediately see why GPU execution was disabled.
- `CT2_USE_CUDNN` defaults to `0` during development to prevent crashes on hosts without cuDNN. Set it to `1` once the matching CUDA/cuDNN runtime is installed.
- When GPU acceleration becomes available, re-enable it via the UI toggle or by exporting `WHISPER_DEFAULT_USE_GPU=1`. The toggle is disabled when diagnostics detect missing GPU prerequisites.
- Metadata responses always report which device/compute type handled the request, making it easy to confirm whether jobs are running on GPU or CPU.

## 📁 Project Structure

```text
/transcriber-system
  /web                 # PWA frontend
  /android-bridge      # Android recording app
  /n8n                 # Workflow exports and configs
  /asr-gateway         # Faster-Whisper server setup
  /whisperx            # WhisperX worker setup
  /infra               # Docker Compose, Caddy configs
  /db                  # Database schema and migrations
  /docs                # API documentation and flows
  /data                # Local data directories (audio/transcripts)
    /audio             # Per-user audio files
    /transcripts       # Generated transcripts and metadata
```

## 🚀 Quick Start

### Prerequisites

- **Hardware**: GPU-enabled system (RTX 4090 recommended)
- **Software**: Docker, Docker Compose
- **Infrastructure**: Caddy reverse proxy configured
- **Domain**: `transcriber.solfamily.group` pointing to your infrastructure
- **Note**: Cloudflare Access not yet configured (using dev auth)

### Development Setup

1. **Clone repository**:

   ```bash
   git clone https://github.com/tfp24601/transcriber-system.git
   cd transcriber-system
   ```

2. **Sync latest changes**:

   ```bash
   ./sync_online_repos_to_local.sh
   ```

3. **Services are integrated in main Docker stack**:
   All transcriber services are already integrated into the main stack at:

   ```text
   /home/ben/SolWorkingFolder/docker-stack/docker-compose.yml
   ```
   
   To restart transcriber services:

   ```bash
   cd /home/ben/SolWorkingFolder/docker-stack
   docker compose restart transcriber-web transcriber-asr-gateway transcriber-whisperx-worker transcriber-tusd
   ```

4. **Database is integrated with main PostgreSQL instance**:
   Schema is already applied to the main PostgreSQL container.

5. **Access web interface**:
   Navigate to `https://transcriber.solfamily.group`

## 📖 Documentation

- **[Build Specification](BuildSpec.md)**: Complete technical specification
- **[API Documentation](docs/API.md)**: REST API endpoints and contracts
- **[User Flows](docs/FLOWS.md)**: Step-by-step user interaction flows
- **[Infrastructure Setup](docs/INFRASTRUCTURE.md)**: Caddy and Cloudflare configuration

## 🔧 System Context

This project integrates with Ben's broader self-hosting infrastructure. For complete system context:

**Reference Repository**: [tfp24601/SystemsInfoRepo](https://github.com/tfp24601/SystemsInfoRepo)

- Hardware specifications (Sol workstation)
- Network topology and routing
- Existing Docker stack configuration
- Caddy and Cloudflared configurations

## 🤖 AI Agent Development

This project is designed for collaborative development with AI agents:

- **GitHub Copilot**: Repository-specific instructions in `.github/copilot-instructions.md`
- **Claude Code**: Access via GitHub integration
- **Context Source**: Reference SystemsInfoRepo for infrastructure understanding

### Development Workflow

1. **Before starting work**:

   ```bash
   ./sync_online_repos_to_local.sh
   ```

2. **After making changes**:

   ```bash
   ./sync_local_to_online_repos.sh
   ```

## 🔐 Security & Privacy

- **No third-party transcription**: All processing on local GPU
- **Cloudflare Access**: Email-based authentication and authorization
- **Per-user isolation**: Separate storage directories and database records
- **Signed URLs**: Time-limited access to audio downloads
- **No indexing**: `X-Robots-Tag: noindex` on all endpoints

## 📊 System Requirements

### Minimum Hardware

- **GPU**: NVIDIA GPU with 8GB+ VRAM (RTX 3070 or better)
- **RAM**: 16GB system RAM
- **Storage**: 100GB+ available space for audio files
- **Network**: Stable internet for uploads (resumable via Tus)

### Recommended (Current Setup)

- **GPU**: RTX 4090 (24GB VRAM)
- **CPU**: AMD Ryzen 9 7950X
- **RAM**: 128GB DDR5
- **Storage**: NVMe SSD storage

## 🚦 Status

**Current Phase**: 🔧 **DEBUGGING** - Core system working, fixing transcript display
**Completion**: ~85% - Transcription pipeline functional, frontend integration in progress

### ✅ **What's Working**

- **Web Interface**: Deployed at `transcriber.solfamily.group`
- **File Upload**: Multi-format audio upload with resumable transfers
- **GPU Transcription**: RTX 4090 running Faster-Whisper large-v3 model
- **Database Integration**: PostgreSQL with `transcriber` schema
- **n8n Workflows**: File ingest and transcription orchestration active
- **Recording History**: Frontend displays recordings with status

### 🔧 **Currently Debugging**

- **Transcript Display**: "Transcripts not yet available" despite successful processing
- **Database Linking**: Verifying transcript records are properly associated with recordings
- **API Response**: Ensuring transcript content reaches frontend

### � **Next Steps**

- Fix transcript display in frontend recording detail view
- Mobile app integration (iOS Shortcuts, Android Bridge)
- Multi-speaker diarization optimization
- Cloudflare Access authentication setup

---

## 📝 License

Private project - not for public distribution.

## 👨‍💻 Maintainer

**Ben** - [GitHub](https://github.com/tfp24601)

Built with assistance from AI agents (GitHub Copilot, Claude Code).

---

*For technical support and infrastructure questions, reference the SystemsInfoRepo or contact the maintainer.*
