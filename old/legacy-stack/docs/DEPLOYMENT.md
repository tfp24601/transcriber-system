# Transcriber System Deployment Guide

This guide walks you through deploying the complete transcriber system on your infrastructure.

## Prerequisites

### Hardware Requirements
- **GPU**: NVIDIA GPU with 8GB+ VRAM (RTX 4090 recommended)
- **RAM**: 16GB minimum, 32GB+ recommended
- **Storage**: 100GB+ available space for audio files
- **Network**: Stable internet connection for uploads

### Software Requirements
- Docker & Docker Compose
- NVIDIA Container Toolkit (for GPU support)
- Caddy reverse proxy
- Cloudflare Access (optional, for production)

## Step 1: Prepare Infrastructure

### 1.1 Clone Repository
```bash
cd /home/ben/SolWorkingFolder/CustomSoftware/
# Repository should already be cloned at transcriber/
```

### 1.2 Set Environment Variables
```bash
cd transcriber/infra
cp .env.example .env
```

Edit `.env` and add:
```bash
# Required: Get from https://huggingface.co/settings/tokens
HUGGINGFACE_TOKEN=your_hf_token_here

# Match your main docker-compose.yml
POSTGRES_PASSWORD=your_postgres_password
```

## Step 2: Database Setup

### 2.1 Initialize Database Schema
```bash
# Copy schema files to your postgres init directory
sudo cp db/init.sql /home/ben/SolWorkingFolder/docker-stack/postgres-init/
sudo cp db/schema.sql /home/ben/SolWorkingFolder/docker-stack/postgres-init/
```

### 2.2 Restart PostgreSQL (if needed)
```bash
cd /home/ben/SolWorkingFolder/docker-stack
docker-compose restart postgres
```

## Step 3: Add Services to Docker Compose

### 3.1 Update Main Docker Compose
Add these services to `/home/ben/SolWorkingFolder/docker-stack/docker-compose.yml`:

```yaml
  # TRANSCRIBER SYSTEM SERVICES
  transcriber-web:
    build: /home/ben/SolWorkingFolder/CustomSoftware/transcriber/web
    container_name: transcriber-web
    restart: unless-stopped
    ports:
      - "3010:80"
    networks:
      - sol_default_network
    environment:
      - NODE_ENV=production

  transcriber-asr-gateway:
    image: fedirz/faster-whisper-server:latest
    container_name: transcriber-asr-gateway
    restart: unless-stopped
    ports:
      - "8000:8000"
    networks:
      - sol_default_network
    environment:
      - MODEL_NAME=large-v3
      - DEVICE=cuda
      - COMPUTE_TYPE=float16
      - HOST=0.0.0.0
      - PORT=8000
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - transcriber_asr_models:/app/models
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  transcriber-whisperx-worker:
    image: jimapp/whisperx:latest
    container_name: transcriber-whisperx-worker
    restart: unless-stopped
    ports:
      - "8001:8000"
    networks:
      - sol_default_network
    environment:
      - WHISPERX_MODEL=large-v3
      - DEVICE=cuda
      - COMPUTE_TYPE=float16
      - HF_TOKEN=${HUGGINGFACE_TOKEN:-}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - transcriber_whisperx_models:/root/.cache/huggingface
      - /home/ben/SolWorkingFolder/CustomSoftware/transcriber/data:/data
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s

  transcriber-tusd:
    image: tusproject/tusd:latest
    container_name: transcriber-tusd
    restart: unless-stopped
    ports:
      - "1080:1080"
    networks:
      - sol_default_network
    command: >
      -host=0.0.0.0
      -port=1080
      -upload-dir=/data/uploads
      -hooks-dir=/hooks
      -hooks-http=http://n8n:5678/webhook/tus-upload-complete
      -hooks-http-forward-headers=Authorization,CF-Access-Jwt-Assertion
      -max-size=10737418240
      -timeout=3600000
    volumes:
      - /home/ben/SolWorkingFolder/CustomSoftware/transcriber/data/uploads:/data/uploads
      - /home/ben/SolWorkingFolder/CustomSoftware/transcriber/infra/tusd-hooks:/hooks:ro
    depends_on:
      - n8n
```

Add these volumes at the bottom:
```yaml
volumes:
  # ... existing volumes ...
  transcriber_asr_models:
  transcriber_whisperx_models:
```

### 3.2 Start Services
```bash
cd /home/ben/SolWorkingFolder/docker-stack
docker-compose up -d transcriber-web transcriber-asr-gateway transcriber-whisperx-worker transcriber-tusd
```

## Step 4: Configure n8n Workflows

### 4.1 Access n8n Interface
Open: `https://n8n.solfamily.group`

### 4.2 Import Workflows
Import each workflow file from `n8n/workflows/`:

1. **File Ingest Workflow**
   - Import: `01-file-ingest.json`
   - Webhook URL: `/webhook/ingest`

2. **Transcribe Job Workflow**
   - Import: `02-transcribe-job.json`
   - Webhook URL: `/webhook/transcribe-job`

3. **API Recordings Workflow**
   - Import: `03-api-recordings.json`
   - Webhook URL: `/webhook/api/recordings`

4. **API Recording Detail Workflow**
   - Import: `04-api-recording-detail.json`
   - Webhook URL: `/webhook/api/recordings/:id`

5. **API Job Status Workflow**
   - Import: `05-api-job-status.json`
   - Webhook URL: `/webhook/api/jobs/:id`

### 4.3 Configure Database Connection
In n8n, create a PostgreSQL credential:
- Name: "PostgreSQL Main DB"
- Host: `postgres`
- Port: `5432`
- Database: `main_sol_db`
- Username: `ben`
- Password: `[your_postgres_password]`

## Step 5: Configure Caddy Routes

### 5.1 Update Caddyfile on Lunanode4

Add to your Caddyfile:
```
# Transcriber System
transcriber.solfamily.group {
    # Security headers
    header {
        X-Frame-Options DENY
        X-Content-Type-Options nosniff
        X-XSS-Protection "1; mode=block"
        Referrer-Policy strict-origin-when-cross-origin
        X-Robots-Tag "noindex, nofollow"
        Permissions-Policy "microphone=(), camera=(), geolocation=()"
        
        Access-Control-Allow-Origin "https://transcriber.solfamily.group"
        Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"
        Access-Control-Allow-Headers "Authorization, Content-Type, CF-Access-Jwt-Assertion"
    }

    @cors_preflight method OPTIONS
    respond @cors_preflight 200

    # API routes to n8n
    handle /api/* {
        reverse_proxy your_sol_ip:5678 {
            header_up Host {host}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # File ingest to n8n
    handle /ingest {
        reverse_proxy your_sol_ip:5678 {
            header_up Host {host}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # Resumable uploads to tusd
    handle /uploads/* {
        reverse_proxy your_sol_ip:1080 {
            header_up Host {host}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # File downloads via n8n (for auth)
    handle /downloads/* {
        reverse_proxy your_sol_ip:5678 {
            header_up Host {host}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # Main web app
    handle {
        reverse_proxy your_sol_ip:3010 {
            header_up Host {host}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    log {
        output file /var/log/caddy/transcriber.log
        format json
    }
}
```

### 5.2 Reload Caddy
```bash
# On Lunanode4
sudo systemctl reload caddy
```

## Step 6: Create Data Directories

```bash
cd /home/ben/SolWorkingFolder/CustomSoftware/transcriber
mkdir -p data/{audio,transcripts,uploads}
sudo chown -R ben:ben data/
chmod -R 755 data/
```

## Step 7: Test Basic Functionality

### 7.1 Check Service Health
```bash
# Check if services are running
docker ps | grep transcriber

# Check ASR gateway
curl http://localhost:8000/health

# Check web interface
curl http://localhost:3010
```

### 7.2 Test Web Interface
1. Open: `https://transcriber.solfamily.group`
2. Try uploading a test audio file
3. Check if it appears in history

### 7.3 Test API Endpoints
```bash
# List recordings
curl https://transcriber.solfamily.group/api/recordings

# Upload test file
curl -X POST https://transcriber.solfamily.group/ingest \
  -F "file=@test.wav" \
  -F "mode=single" \
  -F "name=test_recording"
```

## Step 8: Mobile App Setup

### 8.1 Android Bridge App
1. Build the Android app from `android-bridge/`
2. Install on Android device
3. Test deep links: `ssrec://single` and `ssrec://multi`

### 8.2 iOS Shortcuts
1. Follow `docs/iOS-Shortcuts-Setup.md`
2. Create "Quick Dictate" and "Quick Meeting" shortcuts
3. Test from web app buttons

## Step 9: Production Hardening

### 9.1 Enable Cloudflare Access
1. Configure Cloudflare Access for `transcriber.solfamily.group`
2. Add email allowlist
3. Update n8n workflows to use JWT headers

### 9.2 Security Settings
```bash
# Set proper file permissions
chmod 600 /home/ben/SolWorkingFolder/CustomSoftware/transcriber/infra/.env
chmod +x /home/ben/SolWorkingFolder/CustomSoftware/transcriber/infra/tusd-hooks/*
```

### 9.3 Monitoring
- Monitor Docker container health
- Check GPU usage: `nvidia-smi`
- Monitor disk space: `df -h`
- Check logs: `docker-compose logs transcriber-asr-gateway`

## Step 10: Backup & Maintenance

### 10.1 Database Backups
```bash
# Create backup script
cat > /home/ben/backup-transcriber.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec postgres_db pg_dump -U ben -d main_sol_db --schema=transcriber > /home/ben/backups/transcriber_$DATE.sql
EOF
chmod +x /home/ben/backup-transcriber.sh
```

### 10.2 File Cleanup
Create cleanup script for old recordings:
```bash
# Keep recordings for 90 days
find /home/ben/SolWorkingFolder/CustomSoftware/transcriber/data -type f -mtime +90 -delete
```

### 10.3 Model Updates
Update AI models periodically:
```bash
docker-compose pull transcriber-asr-gateway transcriber-whisperx-worker
docker-compose up -d transcriber-asr-gateway transcriber-whisperx-worker
```

## Troubleshooting

### Common Issues:

1. **GPU not detected**
   - Check: `nvidia-smi`
   - Verify: NVIDIA Container Toolkit installed
   - Restart: Docker daemon

2. **Upload fails**
   - Check: File permissions on data directory
   - Verify: n8n workflows active
   - Test: Direct curl upload

3. **Transcription hangs**
   - Check: GPU memory usage
   - Verify: ASR service health endpoint
   - Restart: ASR containers

4. **Mobile apps can't connect**
   - Check: Caddy routing configuration
   - Verify: DNS resolution
   - Test: Direct IP access

### Log Files:
- Web app: `docker logs transcriber-web`
- ASR Gateway: `docker logs transcriber-asr-gateway`
- WhisperX: `docker logs transcriber-whisperx-worker`
- n8n workflows: n8n interface → Executions
- Caddy: `/var/log/caddy/transcriber.log` (on Lunanode4)

## Performance Tuning

### GPU Settings:
- Monitor VRAM usage
- Adjust model sizes if needed
- Consider using `medium.en` for faster processing

### Network Optimization:
- Enable gzip compression in Caddy
- Use CDN for static assets
- Implement chunked uploads

### Storage Management:
- Compress old audio files
- Archive transcripts to cold storage
- Implement automatic cleanup policies

Your transcriber system is now fully deployed and ready for use!