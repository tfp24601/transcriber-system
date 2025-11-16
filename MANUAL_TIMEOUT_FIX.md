# Manual Fix for Transcriber Timeouts

If the automated script doesn't work, follow these manual steps:

## Step 1: Fix Caddy on lunanode4

SSH into lunanode4:
```bash
ssh ben@192.168.50.56
```

Backup the Caddyfile:
```bash
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.backup-$(date +%Y%m%d-%H%M%S)
```

Edit the Caddyfile:
```bash
sudo nano /etc/caddy/Caddyfile
```

Find the transcriber section (around line 290-320) and add `write_timeout 300s` after `read_timeout 60s`:

**Before:**
```caddy
    reverse_proxy http://192.168.50.10:5000 {
        header_up Host {http.request.host}
        header_up X-Real-IP {http.request.remote}
        header_up X-Forwarded-For {http.request.remote}
        header_up X-Forwarded-Proto {http.request.scheme}
        header_up CF-Connecting-IP {http.request.remote}
        header_up CF-Access-Jwt-Assertion {http.request.header.CF-Access-Jwt-Assertion}
        
        transport http {
            dial_timeout 30s
            response_header_timeout 60s
            read_timeout 60s
        }
    }
```

**After:**
```caddy
    reverse_proxy http://192.168.50.10:5000 {
        header_up Host {http.request.host}
        header_up X-Real-IP {http.request.remote}
        header_up X-Forwarded-For {http.request.remote}
        header_up X-Forwarded-Proto {http.request.scheme}
        header_up CF-Connecting-IP {http.request.remote}
        header_up CF-Access-Jwt-Assertion {http.request.header.CF-Access-Jwt-Assertion}
        
        transport http {
            dial_timeout 30s
            response_header_timeout 60s
            read_timeout 60s
            write_timeout 300s
        }
    }
```

Save (Ctrl+O, Enter) and exit (Ctrl+X).

Reload Caddy:
```bash
sudo systemctl reload caddy
```

Verify it worked:
```bash
sudo systemctl status caddy
```

Exit lunanode4:
```bash
exit
```

## Step 2: Restart Gunicorn on Sol

Stop the current Gunicorn process:
```bash
pkill -f "gunicorn.*transcriber.*app:app"
```

Or kill by PID:
```bash
kill 1870034 2850119
```

Navigate to the Flask app directory:
```bash
cd /home/ben/SolWorkingFolder/CustomSoftware/transcriber/flask-app
```

Activate the virtual environment:
```bash
source .venv/bin/activate
```

Start Gunicorn with the new timeout settings:
```bash
nohup gunicorn \
    --bind 0.0.0.0:5000 \
    --timeout 300 \
    --graceful-timeout 30 \
    --workers 2 \
    app:app > /tmp/transcriber-gunicorn.log 2>&1 &
```

Verify it's running:
```bash
ps aux | grep "gunicorn.*app:app" | grep -v grep
```

You should see 3 processes (1 master + 2 workers).

## Step 3: Test

1. Go to https://transcriber.solfamily.group
2. Upload a test audio file
3. Click Transcribe
4. Should work without timing out!

## Monitoring

Check Gunicorn logs:
```bash
tail -f /tmp/transcriber-gunicorn.log
```

Check Caddy logs on lunanode4:
```bash
ssh ben@192.168.50.56 "sudo journalctl -u caddy -f"
```
