# Transcriber Issue Resolution

**Date**: October 1, 2025  
**Issue**: Transcription fails when uploading audio files or using dictation on both localhost:5000 and transcriber.solfamily.group

## Root Cause Analysis

After investigating the browser console errors and server configurations, I identified **two critical issues** in the Caddy reverse proxy configuration on lunanode4:

### Issue 1: Microphone Access Blocked

**Location**: `/etc/caddy/Caddyfile` on lunanode4  
**Problem**: The Permissions-Policy header explicitly blocks microphone access:

```caddy
Permissions-Policy "microphone=(), camera=(), geolocation()"
```

The `microphone=()` syntax means "deny microphone access to all origins including self".

**Impact**: 
- Browser recording feature cannot access the microphone
- This prevents the dictation functionality from working
- Users see a silent failure or permission denial

**Solution**: Change to allow microphone access for the same origin:

```caddy
Permissions-Policy "microphone=(self), camera=(), geolocation()"
```

### Issue 2: Incorrect X-Forwarded-Proto Header

**Location**: `/etc/caddy/Caddyfile` on lunanode4  
**Problem**: The X-Forwarded-Proto header is set dynamically based on the request scheme:

```caddy
header_up X-Forwarded-Proto {http.request.scheme}
```

**Why this is wrong**: 
- Cloudflare terminates HTTPS and forwards HTTP to Caddy on port 8000
- Therefore `{http.request.scheme}` evaluates to "http" 
- The Flask app and browser think they're on an insecure HTTP connection
- This causes Subresource Integrity (SRI) failures for CDN resources
- The browser console shows: "Failed to find a valid digest in the 'integrity' attribute"

**Impact**:
- Milligram CSS from Cloudflare CDN fails to load due to SRI mismatch
- Other external resources may be blocked
- Mixed content warnings
- Potential security issues

**Solution**: Hardcode to "https" since Cloudflare always handles SSL:

```caddy
header_up X-Forwarded-Proto https
```

## Browser Console Errors Explained

From the screenshot you provided:

1. **`Failed to find a valid digest in the 'integrity' attribute`** - SRI hash mismatch caused by the protocol confusion (Issue #2)
2. **`Failed to load resource: net::ERR_EMPTY_RESPONSE`** - The CSS file failed to load due to SRI check failure
3. **`TypeError: Failed to fetch`** at `app.js:222` - JavaScript couldn't make API calls, likely due to mixed content or missing CSS causing page render issues

## Resolution Steps

### Step 1: Run the Fix Script

I've created a fix script at `/home/ben/fix_transcriber_caddy.sh`. To apply the fixes:

```bash
# From Sol, run:
ssh ben@192.168.50.56 'bash -s' < /home/ben/fix_transcriber_caddy.sh
```

Or SSH into lunanode4 and run it locally:

```bash
ssh ben@192.168.50.56
bash /home/ben/fix_transcriber_caddy.sh  # You'll need to copy it there first
```

### Step 2: Verify the Changes

After running the script, verify the configuration on lunanode4:

```bash
ssh ben@192.168.50.56 "grep -A 25 'transcriber.solfamily.group' /etc/caddy/Caddyfile"
```

You should see:
- `Permissions-Policy "microphone=(self), camera=(), geolocation()"`
- `header_up X-Forwarded-Proto https`

### Step 3: Test the Transcriber

1. Navigate to https://transcriber.solfamily.group
2. Open browser Developer Tools (F12) and check Console - should be no errors
3. Test file upload: Upload a small audio file and click Transcribe
4. Test dictation: Click "Start recording", speak, then "Stop recording" and Transcribe
5. Both should now work without errors

## Current Infrastructure

### Flask App on Sol
- Running via Gunicorn on 192.168.50.10:5000
- Accessible directly on local network
- Healthcheck: http://192.168.50.10:5000/healthz returns JSON

### Caddy Reverse Proxy on lunanode4
- Listens on port 8000 for HTTP traffic from cloudflared
- Proxies to 192.168.50.10:5000
- Handles security headers and compression

### Cloudflared Tunnel
- Handles HTTPS termination at Cloudflare edge
- Forwards HTTP/2 to localhost:8000 on lunanode4
- Configuration: `/etc/cloudflared/config.yml`

### Traffic Flow
```
User Browser (HTTPS)
  ↓
Cloudflare Edge (SSL termination)
  ↓
Cloudflared Tunnel (HTTP/2)
  ↓
lunanode4:8000 (Caddy, HTTP)
  ↓
Sol:5000 (Flask/Gunicorn, HTTP)
```

## Additional Notes

### UFW Rules
Port 5000 on Sol is correctly configured to allow traffic from lunanode4:
```
5000/tcp    ALLOW    192.168.50.56
```

### Gunicorn Process
The Flask app is running correctly via Gunicorn:
```bash
/home/ben/SolWorkingFolder/CustomSoftware/transcriber/flask-app/.venv/bin/python3
/home/ben/SolWorkingFolder/CustomSoftware/transcriber/flask-app/.venv/bin/gunicorn
--bind 0.0.0.0:5000 app:app
```

### Security Headers (After Fix)
The transcriber will have these security headers:
- ✓ X-Frame-Options: DENY
- ✓ X-Content-Type-Options: nosniff
- ✓ Referrer-Policy: strict-origin-when-cross-origin
- ✓ Permissions-Policy: microphone=(self), camera=(), geolocation=() ← Fixed
- ✓ Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
- ✓ X-Forwarded-Proto: https ← Fixed

## Prevention

For future services that need browser APIs (microphone, camera, etc.):

1. **Check Permissions-Policy**: Make sure to allow the necessary APIs with `(self)` or specific origins
2. **X-Forwarded-Proto**: When behind Cloudflare or another HTTPS terminator, always hardcode to `https`
3. **Test thoroughly**: Check browser console for CSP, SRI, and permissions errors

## References

- Caddy Caddyfile: `/etc/caddy/Caddyfile` on lunanode4
- Cloudflared config: `/etc/cloudflared/config.yml` on lunanode4
- Flask app: `/home/ben/SolWorkingFolder/CustomSoftware/transcriber/flask-app/` on Sol
- GitHub repo: tfp24601/transcriber-system (main branch)
