# Transcriber Workflow Configuration

## File Ingest Workflow (WORKING ✅)

**Endpoint**: `POST /ingest`  
**File**: `01 Transcriber - File Ingest.json`

### Flow Summary
1. **File Upload Webhook** - Receives multipart form data
2. **Process Upload Data** - Extracts headers, preserves binary data  
3. **Get or Create User** - Database user lookup/creation
4. **Create Recording Record** - Inserts recording with UUID
5. **Prepare File Paths** - Generates file paths, preserves binary
6. **Create Audio Directory** - Makes user directory
7. **Merge** - Combines workflow paths for binary preservation
8. **Save Audio File** - Writes file to `/files/user_id/recording_id.ext`
9. **Edit Fields** - Sets update fields (id, status, started_at)
10. **Update Status to Processing** - Updates database status
11. **Trigger Transcribe Job** - Calls transcription workflow
12. **Respond Success** - Returns JSON response

### Key Configurations
- **Binary Data Preservation**: Merge node ensures file data flows through
- **Volume Mount**: `local-files:/files` for file storage
- **Database**: Uses UUID generation and proper column matching
- **File Extensions**: Preserves original extensions (MP3, WAV, etc.)

### Input Format
```json
{
  "filename": "audio.mp3",
  "mode": "single|multi", 
  "name": "optional-recording-name",
  "source": "web-desktop"
}
```

### Output Format
```json
{
  "job_id": "uuid",
  "status": "queued", 
  "message": "File uploaded and processing started"
}
```

## Transcribe Job Workflow (FIXED - READY FOR TESTING)

**Endpoint**: `POST /webhook/transcribe-job`  
**File**: `02 Transcriber - Transcribe Job.json`

### Flow Summary
1. **Transcribe Job Webhook** - Receives job data
2. **Parse Job Data** - Extracts recordingId, mode, audioPath (FIXED)
3. **Check Mode** - Routes based on single/multi speaker
4. **Read Audio File** - Reads binary file data for transcription (FIXED)
5. **Transcribe** - Calls appropriate transcription service
6. **Process Results** - Formats output files
7. **Write Files** - Saves transcription outputs
8. **Update Database** - Records completion

### Key Issues Fixed
- **Parse Job Data**: Changed from `$input.first().body` to `$json` for proper webhook data access
- **Read Audio File**: Changed from `executeCommand` with `cat` to `readWriteFile` for proper binary data handling
- **Data Structure**: Properly handles `{recordingId, mode, audioPath}` in webhook body

### Input Format
```json
{
  "recordingId": "uuid",
  "mode": "single|multi",
  "audioPath": "/files/user_id/recording_id.ext"
}
```

### Services Used
- **faster-whisper**: Single speaker transcription  
- **WhisperX**: Multi-speaker with diarization

### Outputs Generated
- `.txt` - Plain text transcript
- `.vtt` - WebVTT subtitle format
- `.srt` - SubRip subtitle format  
- `.json` - Full transcription data

## API Recordings Workflow

**File**: `03-api-recordings-live.json`  
**Status**: Needs verification

Provides REST API for retrieving recordings and transcripts.

## Volume Mounts Required

```yaml
volumes:
  - ./local-files:/files              # File upload storage
  - ./data:/data                      # Transcription outputs
  - ./postgres-dbs:/var/lib/postgresql/data  # Database
```

## Database Tables Used

- `transcriber.users` - User management
- `transcriber.recordings` - Audio file metadata  
- `transcriber.transcripts` - Transcription results

## Environment Variables

- Cloudflare Access headers for authentication
- PostgreSQL connection details
- n8n webhook URLs
