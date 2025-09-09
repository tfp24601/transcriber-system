# Transcriber System - AI Agent Instructions

## 🎯 Project Overview

This is a **privacy-first, multi-user transcription system** that provides seamless recording and transcription across devices. The system is designed for AI agent collaboration and follows specific architectural patterns.

## 🚨 CRITICAL: Always Start with Sync

**BEFORE ANY WORK:** Always run this command first:
```bash
cd /home/ben/SolWorkingFolder/CustomSoftware/transcriber
./sync_online_repos_to_local.sh
```

**After completing work:** Always push changes with:
```bash
./sync_local_to_online_repos.sh
```

## 📋 System Context & Architecture

### Infrastructure Context
**ESSENTIAL:** Reference `tfp24601/SystemsInfoRepo` for complete system understanding:
- **Sol workstation**: AMD Ryzen 9 7950X, RTX 4090 (24GB VRAM), 128GB RAM, Ubuntu 24.04.2
- **Network**: Caddy reverse proxy + Cloudflared tunnels via Lunanode4 VPS
- **Domain**: `transcriber.solfamily.group` (requires config updates on Lunanode4)
- **Existing Docker stack**: `/home/ben/SolWorkingFolder/docker-stack/docker-compose.yml`

### Key Architectural Decisions
- **Privacy-first**: All transcription happens on local GPU, no cloud services
- **Decoupled design**: Native recording apps + web orchestration interface
- **Multi-user**: Cloudflare Access auth + per-user PostgreSQL records + file isolation
- **Two modes**: 👤 Single-speaker (accuracy) vs 👥 Multi-speaker (diarization)
- **Reliability**: Resumable uploads, background recording, idempotent processing

## 🔧 Development Guidelines

### Project Structure (monorepo)
```
/transcriber-system
  /web           # PWA frontend (TypeScript + React/Vite or SvelteKit)
  /android-bridge # Kotlin app for deep-link recording
  /n8n           # Workflow exports + configs
  /asr-gateway   # Faster-Whisper Docker setup
  /whisperx      # WhisperX worker setup  
  /infra         # docker-compose.yml, Caddy configs
  /db            # PostgreSQL schema, migrations
  /docs          # API.md, FLOWS.md, etc.
  /data          # Local storage (audio/, transcripts/)
```

### Core Components to Implement

1. **Web PWA (`/web`)**:
   - Two main buttons: 👤 Single / 👥 Meeting
   - Platform detection: iOS → Shortcuts, Android → deep link, Desktop → file upload
   - History panel, transcript viewer, download capabilities
   - Status polling for async transcription jobs

2. **Backend Services** (integrate with existing Docker stack):
   - **asr-gateway**: Faster-Whisper OpenAI-compatible server (GPU)
   - **whisperx-worker**: Diarization and word-level alignment (GPU)
   - **n8n workflows**: Ingest, processing orchestration, API endpoints
   - **tusd**: Optional resumable upload server

3. **Mobile Integration**:
   - **Android Bridge**: Kotlin app with foreground service recording
   - **iOS Shortcuts**: Native recording → upload → return to web

4. **Database Schema**: Users, recordings, transcripts tables (see BuildSpec.md)

### Technical Requirements

#### GPU Utilization
- **RTX 4090 available**: Use for Faster-Whisper large-v3 model
- **CUDA FP16**: Optimize for speed and VRAM efficiency
- **Model switching**: large-v3 for single-speaker, medium.en for multi-speaker

#### Security & Auth
- **Cloudflare Access**: JWT validation on all endpoints
- **Per-user authorization**: Check user_id on every API call
- **Signed URLs**: Time-limited download links
- **No indexing**: `X-Robots-Tag: noindex` headers

#### File Storage Patterns
- **Audio**: `/data/audio/<user_id>/<recording_id>.{wav,flac}`
- **Transcripts**: `/data/transcripts/<user_id>/<recording_id>.{txt,srt,vtt,json}`
- **Naming**: Default format `YYYYMMDDHHMMSS` (local timezone)

### Integration with Existing Infrastructure

#### Docker Stack Extension
**Current stack**: Already has n8n, postgres
**Add services**: asr-gateway, whisperx-worker, (optional tusd)
**Volume mounts**: Bind existing `/data/audio` and `/data/transcripts` directories

#### Caddy Configuration (Lunanode4)
Agent cannot directly modify, but should generate config snippets for:
- Route `/` → web app static files
- Route `/api/*` → n8n webhook endpoints  
- Route `/ingest` → upload endpoint
- Route `/uploads/*` → tusd (if enabled)
- Headers: security, no-index, CORS restrictions

#### Cloudflared Setup (Lunanode4)
Reference existing tunnel configuration in SystemsInfoRepo for domain routing patterns.

## 🤖 AI Agent Workflow

### When Building Components

1. **Check BuildSpec.md**: Comprehensive technical specification with API contracts
2. **Reference SystemsInfoRepo**: Infrastructure constraints and patterns
3. **Follow existing patterns**: Match Docker stack, Caddy routing, security headers
4. **GPU considerations**: Leverage RTX 4090 capabilities for real-time transcription
5. **Privacy compliance**: Ensure no data leaves Ben's infrastructure

### When Adding Features

1. **Database changes**: Update schema.sql and provide migration scripts
2. **API endpoints**: Document in `docs/API.md` with request/response examples
3. **n8n workflows**: Export as JSON and provide import instructions
4. **Mobile apps**: Consider both iOS Shortcuts and Android Bridge compatibility
5. **Error handling**: Implement robust retry logic and user feedback

### Testing Considerations

- **Local development**: Use file upload initially before mobile integration
- **GPU testing**: Verify models load and process faster-than-real-time
- **Multi-user**: Test with multiple Cloudflare Access accounts
- **Large files**: Validate resumable uploads work with 60+ minute recordings

## 🔍 Key Files to Reference

1. **BuildSpec.md**: Complete technical specification (ALWAYS READ FIRST)
2. **SystemsInfoRepo**: Infrastructure context and existing configurations
3. **`/home/ben/SolWorkingFolder/docker-stack/docker-compose.yml`**: Current Docker setup
4. **Existing Caddy config**: See SystemsInfoRepo for routing patterns

## ⚡ Performance Targets

- **Transcription speed**: Faster than real-time on RTX 4090
- **Upload handling**: Support multi-GB files via resumable uploads
- **Real-time feedback**: Status updates every 3-5 seconds during processing
- **Mobile UX**: One-tap recording with background safety

## 🔒 Security Checklist

- [ ] All endpoints behind Cloudflare Access
- [ ] Per-user file isolation enforced
- [ ] No direct file system access without auth
- [ ] Signed URLs for downloads with TTL
- [ ] CORS restricted to transcriber domain
- [ ] No indexing meta tags and headers
- [ ] Audit logging for file access

## 🚀 Development Priorities

1. **Phase 1**: Web PWA with file upload transcription
2. **Phase 2**: n8n workflows and GPU transcription services
3. **Phase 3**: iOS Shortcuts integration
4. **Phase 4**: Android Bridge app
5. **Phase 5**: Advanced features (diarization, resumable uploads)

---

**Remember**: This is a privacy-focused system. Every design decision should prioritize keeping data on Ben's infrastructure while maintaining excellent user experience across all platforms.

*For questions about infrastructure integration, always reference SystemsInfoRepo first.*
