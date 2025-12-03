# Transcriber System: Reverse Proxy Deployment Handoff

Last updated: 2025-09-30

## 0. Quick Summary of Updated Reverse Proxy Plan

- Keep the Flask app running on **Sol** (192.168.50.10) on port `5000` using its existing Python environment.
- Reverse proxy from **lunanode4 Caddy → Sol:5000**, following the same pattern as other services in the stack.
- Cloudflared continues routing `transcriber.solfamily.group` to `http://localhost:8000` (Caddy).
- Switching to an alternate port (e.g., `5151`) is optional; do so only if you want to reserve `5000` for development.

## 1. Snapshot of the Current Project

- **Repository:** `tfp24601/transcriber-system` (branch `main`)
- **Primary service:** Flask-based GPU transcription API and UI in `flask-app/`
- **Model stack:** `faster-whisper` (CTranslate2) with optional CUDA/cuDNN acceleration.
- **Recent commits:**
  - `2898165` (2025-09-29) – Adjusted sync script guard to avoid empty commits; push verified.
  - `9ac8d6a` (2025-09-29) – Added Flask transcription service, refreshed docs, introduced GPU milestone write-up.
  - `1030d31` (2025-09-29) – Archived legacy stack under `old/legacy-stack/` for clarity.
- **Ignore rules:** Root `.gitignore` blocks virtualenvs, caches, and runtime transcription outputs. Do not modify `.gitignore` when deploying.

## 2. Runtime & Dependencies

- **Python:** 3.10+ recommended. GPU path assumes CUDA 12.4 and cuDNN 9; app auto-falls back to CPU if unavailable.
- **Primary packages:** `Flask`, `faster-whisper`, `numpy` (see `flask-app/requirements.txt`).

### Environment variables


- `FLASK_HOST`, `FLASK_PORT` — server binding (defaults `0.0.0.0:5000`).
- `FLASK_DEBUG` — keep `false` in production.
- `WHISPER_*` — model, device, and compute overrides.
- `TRANSCRIPTION_OUTPUT_DIR` — writable directory for generated transcripts (default `./transcriptions`).
- `TRANSCRIBER_REQUIRE_AUTH` — enforce Cloudflare Access headers when `true` (default `false` during rollout).
- `TRANSCRIBER_DEFAULT_USER` — fallback identity used when auth is disabled (`shared` by default).
- `TRANSCRIBER_USER_HEADER` / `TRANSCRIBER_ALT_USER_HEADER` — header names to trust for user identity (`CF-Access-Authenticated-User-Email` and optional secondary header).
- **Assumptions:** CT2 CUDA libraries installed when GPU acceleration is desired. Ensure `/tmp` has capacity for upload temp files.

## 3. Service Topology Today

- Flask app runs under `systemd` (`transcriber.service`) via gunicorn on port `5000`.
- Legacy stack moved to `old/legacy-stack/` and can be ignored for deployment.
- `.github/copilot-instructions.md` outlines expectations; the Flask app is the live path.

## 4. Desired Goal for Next Agent

> "Move the Flask transcription service behind the reverse proxy on lunanode4 using Caddy, fronted by Cloudflare."

### Target Architecture

1. **Host:** `lunanode4` (Ubuntu VM with GPU access).
2. **Application process:** Flask app managed by `systemd`, using an environment file and persistent transcript directory.
3. **Reverse proxy:** Caddy on lunanode4, serving HTTPS (Cloudflared tunnel) and forwarding to the Flask backend.
4. **DNS / CDN:** Cloudflare routes traffic to lunanode4 via the Cloudflared tunnel; confirm DNS and SSL mode.

## 5. Outstanding Tasks

1. **Enable Cloudflare Access (pending rollout)**
   - Turn on the Access application and set `TRANSCRIBER_REQUIRE_AUTH=true` once policies are verified.
   - Confirm the trusted headers (e.g., `CF-Access-Authenticated-User-Email`) arrive in Flask via Caddy.
2. **Finalize monitoring & alerting**
   - Point uptime checks at `https://transcriber.solfamily.group/healthz`.
   - Establish log review cadence on Sol (`journalctl -u transcriber.service`) and lunanode4 (Caddy logs).
3. **Run public smoke tests**
   - Exercise an end-to-end transcription through the Cloudflare hostname.
   - Verify per-user transcript directories populate correctly on Sol.

## 6. Always-on service deployment on Sol

### 6.1 Prepare environment

```bash
cd /path/to/transcriber/flask-app
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt gunicorn
deactivate
mkdir -p /path/to/transcriber/transcriptions
```

Create `flask-app/transcriber.env` with restrictive permissions (e.g., `chmod 640`).

```ini
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false
TRANSCRIPTION_OUTPUT_DIR=/path/to/transcriber/transcriptions
WHISPER_MODEL=small
WHISPER_DEFAULT_USE_GPU=auto
TRANSCRIBER_REQUIRE_AUTH=false
TRANSCRIBER_DEFAULT_USER=shared
TRANSCRIBER_USER_HEADER=CF-Access-Authenticated-User-Email
TRANSCRIBER_ALT_USER_HEADER=
```

> **Status note (2025-09-30):** The systemd unit and environment below are live on Sol; keep this section handy for rebuilds or disaster recovery.

### 6.2 systemd unit on Sol

Save as `/etc/systemd/system/transcriber.service` (or symlink from the repo).

```ini
[Unit]
Description=Transcriber Flask Service
After=network.target

[Service]
Type=simple
User=ben
WorkingDirectory=/path/to/transcriber/flask-app
EnvironmentFile=/path/to/transcriber/flask-app/transcriber.env
ExecStart=/path/to/transcriber/flask-app/.venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 600 app:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and validate:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now transcriber.service
sudo systemctl status transcriber.service
journalctl -u transcriber.service -f
```

### 6.3 Caddy site block (excerpt)

```caddy
http://transcriber.solfamily.group {
   encode zstd gzip

   header {
      X-Frame-Options DENY
      X-Content-Type-Options nosniff
      Referrer-Policy strict-origin-when-cross-origin
      Permissions-Policy "microphone=(), camera=(), geolocation()"
      Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
   }

   # Optional fast edge response; backend now also serves /healthz with JSON.
   handle_path /healthz {
      respond "ok" 200
   }

   reverse_proxy http://192.168.50.10:5000 {
      header_up Host {http.request.host}
      header_up X-Real-IP {http.request.remote}
      header_up X-Forwarded-For {http.request.remote}
      header_up X-Forwarded-Proto {http.request.scheme}
      header_up CF-Connecting-IP {http.request.remote}
      header_up CF-Access-Jwt-Assertion {http.request.header.CF-Access-Jwt-Assertion}
   }

   log {
      output file /var/log/caddy/transcriber.log
      format json
   }
}
```

### 6.4 cloudflared ingress (unchanged)

```yaml
ingress:
   - hostname: transcriber.solfamily.group
      service: "http://localhost:8000"
   - service: http_status:404
```

Cloudflared already forwards to Caddy on port `8000`.

## 7. Cloudflare-based access control roadmap

1. **Protect the route with Cloudflare Access** – create an Access application for `transcriber.solfamily.group`, choose identity providers, and enable header injection (e.g., `Cf-Access-Authenticated-User-Email`).
2. **Surface identity inside Flask** – read the header in Flask (`request.headers.get("Cf-Access-Authenticated-User-Email")`) and, if desired, route transcripts per user (e.g., `/transcriptions/{email}/`).
3. **Enhance UX** – add logout links (Cloudflare Access revoke endpoint), audit logging, or role-based defaults. Until per-user directories are implemented, all users will still share the same transcript archive.

## 8. Validation Checklist for Next Agent

- [ ] Virtualenv refreshed and dependencies installed (`.venv`, `gunicorn`).
- [ ] `transcriber.env` created with correct paths and permissions.
- [ ] `transcriber.service` enabled and healthy (`systemctl status`, `journalctl`).
- [ ] Caddy reloaded; `/healthz` reachable via `https://transcriber.solfamily.group/healthz`.
- [ ] Cloudflare Access (if enabled) tested with at least one user login.
- [ ] End-to-end transcription succeeds; transcripts persist on Sol.
- [ ] Transcript files write under per-user directories (`transcriptions/<user-slug>/...`).
- [ ] Logs reviewed on Sol and lunanode4 for errors.

## 9. Supporting Resources

- Project docs: `README.md`, `docs/API.md`, `docs/gpu-acceleration-milestone.md`.
- Contributor guidance: `.github/copilot-instructions.md`.
- Legacy assets reference: `old/legacy-stack/` (no action needed for deployment).
- Sync script: `sync_local_to_online_repos.sh` (safe on a clean tree when committing future changes).

---

**Next Agent Notes:** If GPU driver versions differ from expectations, Whisper falls back to CPU (slower). Keep secrets (API keys, Cloudflare tokens) in environment files or secret managers—never commit them. Document any deviations from this plan for the next handoff.
