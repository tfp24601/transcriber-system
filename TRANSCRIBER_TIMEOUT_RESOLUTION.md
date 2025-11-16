# Transcriber Timeout Issue - Resolution

**Date**: October 1, 2025  
**Issue**: Transcription fails with "TypeError: Failed to fetch" after uploading large audio files
**Root Cause**: Timeout issues with large file uploads

## What Happened

The transcriber was working fine until you uploaded a large audio file today. After that, all transcription attempts failed with network errors.

### Evidence from Logs

Caddy logs from today show two failed `/transcribe` POST requests:

1. **19:39:37** - EOF error, 502 Bad Gateway, Content-Length: 72,560 bytes
2. **19:43:49** - EOF error, 502 Bad Gateway, Content-Length: 108,302 bytes

Both requests failed with:
```json
{"level":"error","msg":"EOF","uri":"/transcribe","status":502}
```

The connection was being closed (EOF = End of File) before the upload/transcription could complete.

## Root Cause

**Gunicorn's default worker timeout is 30 seconds**. When you upload a large audio file:

1. Upload time: 5-10 seconds (depending on file size and connection)
2. Transcription time: 20-60 seconds (depending on audio length and model)
3. **Total time > 30 seconds = Timeout!**

Additionally, Caddy's `transport` block for transcriber was missing `write_timeout`, which meant it could also timeout on slow uploads.

## The Fix

### 1. Updated Gunicorn Configuration

Modified `/home/ben/SolWorkingFolder/CustomSoftware/transcriber/flask-app/run_gunicorn.sh`:

```bash
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --timeout 300 \           # 5 minutes for large files
    --graceful-timeout 30 \   # Clean shutdown window
    --workers 2 \             # Handle concurrent requests
    app:app
```

### 2. Updated Caddy Configuration (on lunanode4)

Need to add `write_timeout` to the transcriber transport block in `/etc/caddy/Caddyfile`:

```caddy
transport http {
    dial_timeout 30s
    response_header_timeout 60s
    read_timeout 60s
    write_timeout 300s       # NEW: Allow 5 min for uploads
}
```

## Resolution Steps

Run the fix script:

```bash
bash /home/ben/fix_transcriber_timeouts.sh
```

This script will:
1. Backup and update Caddy config on lunanode4
2. Reload Caddy
3. Restart Gunicorn on Sol with new timeout settings

## Why This Wasn't an Issue Before

You likely hadn't uploaded files large enough to exceed the 30-second timeout. Today's large file upload exceeded the threshold, causing the timeout and subsequent failures for all requests.

## Testing After Fix

1. Go to https://transcriber.solfamily.group
2. Upload a large audio file (> 1MB)
3. Click Transcribe
4. Wait for completion (may take 1-2 minutes for large files)
5. Should see successful transcription

## About the Earlier Analysis

My initial analysis focused on:
- **Microphone permissions**: Actually not the issue - browser was successfully recording
- **X-Forwarded-Proto**: Also not the issue - other services use the same config and work fine

You were correct to question those findings! The real issue was revealed in the Caddy error logs showing EOF/502 errors specifically on `/transcribe` POST requests.

## Prevention

For future services that handle large uploads or long-running operations:

1. Set appropriate Gunicorn timeouts (`--timeout`)
2. Add `write_timeout` to Caddy transport blocks
3. Consider using async workers for long operations
4. Monitor logs for EOF and 502 errors

## References

- Gunicorn docs: https://docs.gunicorn.org/en/stable/settings.html#timeout
- Caddy reverse proxy: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy#the-transport-subdirective
- Error logs: `ssh ben@192.168.50.56 "journalctl -u caddy --since '2025-10-01'"`
