# Web Frontend

PWA frontend for the transcriber system.

## Tech Stack

- ✅ **TypeScript + React (Vite)** - Fully implemented
- ✅ **PWA capabilities** - Service worker and manifest configured
- ✅ **Responsive design** - Works on mobile and desktop

## Implemented Features

- ✅ **Two main buttons**: 👤 Single / 👥 Meeting mode selection
- ✅ **History panel** - View past recordings with status
- ✅ **File upload** - Drag & drop and click to upload
- ✅ **Status polling** - Real-time transcription job status updates
- ✅ **Download capabilities** - Audio and transcript downloads
- ✅ **Recording detail view** - Click recordings to view transcripts

## API Integration

- Uses query parameter authentication: `?user_email=ben@solfamily.group`
- Fallback for development mode (no Cloudflare Access yet)
- Connects to n8n workflows for backend processing

## Development

```bash
cd web
npm install
npm run dev  # Development server
npm run build  # Production build
```

## Deployment

Served via Docker container `transcriber-web` in the main docker stack at:
`/home/ben/SolWorkingFolder/docker-stack/docker-compose.yml`
