# Transcriber System API Documentation

Base URL: `https://transcriber.solfamily.group`

n8n API key for agent access:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyNDM3NzBiZi1mNTlkLTRiMjctODlkZS04NjU1YjdhNjM0ZmQiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU3NDMyNTQ1fQ.rCiMjVSfNvjSjUKRB_5OJ5JG5DT9nzgbzsd0rf4xF58

## Authentication

All endpoints require authentication via Cloudflare Access. The system extracts user information from the `CF-Access-Authenticated-User-Email` header.

For development/testing, a default test user (`test@solfamily.group`) is used when the header is not present.

## Endpoints

### 1. File Upload - POST /ingest

Upload an audio file for transcription.

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `file` (required): Audio file (WAV, MP3, M4A, FLAC, OGG, OPUS)
- `mode` (required): `single` or `multi`
- `name` (optional): Recording name (defaults to timestamp)
- `source` (optional): Source identifier (`web-desktop`, `android-bridge`, `ios-shortcut`)

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "File uploaded and processing started"
}
```

**Example cURL:**
```bash
curl -X POST https://transcriber.solfamily.group/ingest \
  -F "file=@recording.wav" \
  -F "mode=single" \
  -F "name=my_recording" \
  -F "source=api"
```

---

### 2. Get Recordings - GET /api/recordings

List user's recordings.

**Query Parameters:**
- `limit` (optional): Maximum number of recordings to return (default: 50)

**Response:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "meeting_20250909120000",
      "mode": "multi",
      "created_at": "2025-09-09T12:00:00Z",
      "duration_seconds": 3600,
      "status": "done"
    }
  ]
}
```

**Status Values:**
- `queued`: Waiting to be processed
- `processing`: Currently being transcribed
- `done`: Transcription completed
- `failed`: Transcription failed

---

### 3. Get Recording Detail - GET /api/recordings/:id

Get detailed information about a specific recording including transcript.

**Path Parameters:**
- `id`: Recording UUID

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "meeting_20250909120000",
  "mode": "multi",
  "created_at": "2025-09-09T12:00:00Z",
  "duration_seconds": 3600,
  "status": "done",
  "transcript_text": "Speaker A: Welcome everyone to today's meeting...",
  "download_audio_url": "https://transcriber.solfamily.group/downloads/audio/550e8400-e29b-41d4-a716-446655440000",
  "download_txt_url": "https://transcriber.solfamily.group/downloads/txt/550e8400-e29b-41d4-a716-446655440000",
  "download_srt_url": "https://transcriber.solfamily.group/downloads/srt/550e8400-e29b-41d4-a716-446655440000",
  "download_vtt_url": "https://transcriber.solfamily.group/downloads/vtt/550e8400-e29b-41d4-a716-446655440000",
  "diarization_json": {
    "segments": [
      {
        "speaker": "SPEAKER_00",
        "start": 0.0,
        "end": 5.2,
        "text": "Welcome everyone to today's meeting"
      }
    ],
    "num_speakers": 3
  },
  "language_detected": "en",
  "speaker_count": 3
}
```

**Error Response (404):**
```json
{
  "error": "Recording not found"
}
```

---

### 4. Get Job Status - GET /api/jobs/:id

Check the processing status of a recording job.

**Path Parameters:**
- `id`: Job ID (same as recording ID)

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 0.65,
  "created_at": "2025-09-09T12:00:00Z",
  "started_at": "2025-09-09T12:00:05Z",
  "completed_at": null,
  "error_message": null
}
```

**Progress Values:**
- `0.0`: Just started
- `0.1-0.8`: Processing (estimated based on elapsed time)
- `1.0`: Completed

---

### 5. TUS Resumable Uploads (Optional)

**Endpoint:** `/uploads/*`

The system supports TUS resumable uploads for large files. Use a TUS client library to upload to:
- Creation URL: `https://transcriber.solfamily.group/uploads`
- Chunk size: Recommended 1MB
- Metadata: Include `mode`, `name`, `source` in TUS metadata

**TUS Metadata Example:**
```
mode: single
name: my_large_recording
source: android-bridge
```

---

## File Download Endpoints

### Audio Download - GET /downloads/audio/:id
### Text Download - GET /downloads/txt/:id  
### SRT Download - GET /downloads/srt/:id
### VTT Download - GET /downloads/vtt/:id

All download endpoints require authentication and will return signed URLs or proxy the file download after verifying user access.

---

## Error Responses

All endpoints may return these error responses:

**400 Bad Request:**
```json
{
  "error": "Invalid request parameters",
  "details": "Missing required field: mode"
}
```

**401 Unauthorized:**
```json
{
  "error": "Authentication required"
}
```

**403 Forbidden:**
```json
{
  "error": "Access denied"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error",
  "message": "Transcription service unavailable"
}
```

---

## Rate Limits

- Upload: 10 files per hour per user
- API calls: 1000 requests per hour per user
- File size limit: 10GB per upload
- Duration limit: 3 hours per recording

---

## Supported Audio Formats

**Primary formats:**
- WAV (PCM, 16kHz recommended)
- FLAC (lossless compression)

**Secondary formats:**
- MP3 (will be converted)
- M4A (will be converted)  
- OGG (will be converted)
- OPUS (will be converted)

**Recommendations:**
- Sample rate: 16kHz or 44.1kHz
- Channels: Mono preferred for single speaker, stereo acceptable for multi
- Bit depth: 16-bit minimum, 24-bit acceptable

---

## Webhooks (Future)

The system will support webhooks for job completion notifications:

```json
{
  "event": "transcription.completed",
  "recording_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "done",
  "timestamp": "2025-09-09T12:30:00Z"
}
```

---

## SDK Examples

### JavaScript/TypeScript
```typescript
class TranscriberClient {
  async uploadFile(file: File, mode: 'single' | 'multi', name?: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode);
    if (name) formData.append('name', name);
    formData.append('source', 'web-api');
    
    const response = await fetch('/ingest', {
      method: 'POST',
      body: formData
    });
    
    return response.json();
  }
}
```

### Python
```python
import requests

def upload_file(file_path, mode='single', name=None):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'mode': mode,
            'name': name or f'recording_{int(time.time())}',
            'source': 'python-api'
        }
        
        response = requests.post(
            'https://transcriber.solfamily.group/ingest',
            files=files,
            data=data
        )
        
        return response.json()
```

### cURL Examples

**Upload with custom name:**
```bash
curl -X POST https://transcriber.solfamily.group/ingest \
  -F "file=@meeting.wav" \
  -F "mode=multi" \
  -F "name=weekly_standup_20250909"
```

**Get recordings:**
```bash
curl https://transcriber.solfamily.group/api/recordings?limit=10
```

**Check job status:**
```bash
curl https://transcriber.solfamily.group/api/jobs/550e8400-e29b-41d4-a716-446655440000
```