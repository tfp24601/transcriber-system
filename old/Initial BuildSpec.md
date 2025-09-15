# Transcriber System — Build Spec for agent

**Goal:**
Build a private, multi-user **transcriber system** that feels like one-tap "record → send → read transcript" on phones and desktop, while keeping **recording** and **transcription** decoupled for reliability and privacy. Phones use native capture (for screen-off recording), then upload to the web app which orchestrates transcription on my home server (Sol). Long-term reliability > fancy UI.

**Key Principles:**

* **Privacy-first** (no third-party clouds; audio stored on Sol).
* **Decoupled**: Recording is native (Android/iOS); the **web app is a transcriber + launcher**.
* **Multi-user**: simple auth via **Cloudflare Access**; per-user history in Postgres; per-user audio directories on disk.
* **Two modes**: 👤 **single-speaker** (highest accuracy), 👥 **multi-speaker** (speed + diarization/timestamps).
* **Reliability**: resumable uploads; background-safe; idempotent jobs; clear error states; storage quotas.

---

## Critical Context

- See the details of my system stack and architecture by going to my tfp24601/SystemsInfoRepo on github
- You're working on Sol, my main computer.
- This will be a webpage, a tool accessible via a browser by going to transcriber.solfamily.group
- The files for this will all be stored [repo? local only?]
- This will need to run through my caddy cloudflared reverse proxy, which is run through Lunanode4, not through Sol. So you will not be able to directly change the caddyfile and the cloudflared config file, but you can see copies of those files there on the repo and you can tell me what changes to make to them on Lunanode4.
- You should also be able to see my docker compose file at /home/ben/SolWorkingFolder/docker-stack/docker-compose.yml here on Sol.

## High-Level Architecture

**Clients**

* **Web App (PWA)** at `https://transcriber.solfamily.group`:

  * Two big buttons: 👤 "Single note" and 👥 "Meeting".
  * On **iOS**: launches **Shortcuts** to start a native background recording, then auto-uploads and returns to the web UI.
  * On **Android**: launches a tiny **Recorder Bridge** app via deep link (`ssrec://single` or `ssrec://multi`) to start background recording, save locally, upload, and return.
  * On **Desktop**: provide file picker upload (drag & drop) to run transcription; optional keyboard shortcut to start quick local recording (non-blocker for v1).

**Ingress / Auth**

* **Cloudflare Access** in front of **Caddy** → enforces login with my allowlist (email domain or specific addresses).
* Caddy reverse proxies to internal services; sets security headers; disallows indexing.

**Server (Sol)**

* **n8n** orchestrates ingest/transcribe jobs via webhook endpoints.
* **ASR**: **Faster-Whisper OpenAI-compatible server** (GPU), model switchable by mode.
* **WhisperX worker** (GPU) for diarization + word-level timestamps (used for 👥 mode).
* **Postgres** for users/recordings/transcripts metadata.
* **File storage** on disk (bind mounts): `/data/audio/<user_id>/<recording_id>.flac` (or `.wav`), `/data/transcripts/<user_id>/<recording_id>.{txt,srt,vtt,json}`.
	* These folders are already created here in the local project folder (/home/ben/SolWorkingFolder/CustomSoftware/transcriber)
* (Optional) **tusd** (Tus resumable uploads) to handle long, robust uploads; n8n is triggered on upload completion.

---

## Non-Functional Requirements

* **Background recording must work with screen off** (native iOS Shortcut flow; Android foreground service).
* **Uploads must be resumable**; network drops cannot destroy a 60-90 min meeting.
* **Timeouts / body size** tuned for multi-GB files if needed (or avoided entirely via tus).
* **Throughput**: 4090 GPU should process large-v3 faster-than-real-time; queue if needed.
* **Security**: all endpoints behind Cloudflare Access; per-user authorization on every API call; no indexing; signed URLs for audio download; audit logs.

---

## Components & Implementation Notes

### 1) Web App (PWA)

**Tech:** TypeScript + React (Vite) or SvelteKit (either OK). No server-side rendering required.

**UI Requirements:**

* Two prominent buttons:

  * 👤 **Single** (accuracy-first)
  * 👥 **Meeting** (speed + diarization)
* **Name** field (optional). Default = `YYYYMMDDHHMMSS` (local time).
* **Timer** (for in-app recording only if we add that later). For native-triggered recordings, show an "active job" status panel.
* **Transcript panel** with copy button and **Download .txt**.
* **History dropdown** (or searchable list) showing last N recordings (name, date, mode, duration).
* **Download audio** button (signed URL).
* **Status states**: "Waiting for upload…", "Processing…", "Done", "Failed—retry".
* **Noindex** meta and `X-Robots-Tag: noindex` response header.

**Platform-trigger logic:**

* Detect platform on load:

  * **iOS**: when 👤/👥 clicked → open `shortcuts://run-shortcut?name=<ConfiguredName>&x-success=<returnURL>&x-error=<fallbackURL>&name=<fileName>&mode=<single|multi>`
  * **Android**: try deep link `ssrec://single?name=<fileName>` or `ssrec://multi?name=<fileName>`; fall back to instruction modal if app absent.
  * **Desktop**: open **file picker**; POST to `/ingest` with `mode` and `name`.

**APIs (web app side)**

* `GET /api/me` → returns user object { id, email, name } (derived from Cloudflare Access JWT).
* `GET /api/recordings?limit=50` → lists user's recent recordings (id, name, mode, created\_at, duration, status).
* `GET /api/recordings/:id` → returns transcript text (and diarization JSON if exists) + signed URLs for audio and transcript files.
* `GET /api/jobs/:id` → polling endpoint for processing status.
* (If using tus) `POST /tus/create` → client library handles; `HEAD/PATCH` for chunks; upon completion, tusd webhook notifies n8n.

**Front-end State:**

* Store last selected mode and optional default naming pattern in localStorage.
* Keep an "active jobs" list and auto-refresh status (poll every 3-5s).

**Accessibility & UX:**

* Large touch targets, clear recording consent text when needed.
* Error banners with actionable advice (e.g., "Upload failed, tap to resume").

---

### 2) Android "Recorder Bridge" App

**Tech:** Kotlin (Android Studio). Alternatively Flutter; choose Kotlin for direct control.

**Capabilities:**

* **Deep links**: `ssrec://single` and `ssrec://multi` (with optional `name` query param).
* **Foreground Service** for recording:

  * Acquire **PARTIAL\_WAKE\_LOCK**, **FOREGROUND\_SERVICE**.
  * Use **AudioRecord** or **MediaRecorder** with **WAV PCM** or **FLAC** output.
  * Sample rate: 16 kHz or 48 kHz (configurable; default 16 kHz mono PCM).
  * Gain control optional; automatic pause/resume disabled by default.
* **Background-safe**: continues recording with screen off, app in background.
* **File naming**: default timestamp (UTC or local—match web).
* **Local path**: app-private storage: `/data/data/<pkg>/files/audio/<recording_id>.wav` (or `.flac`).
* **Upload**:

  * Preferred: **tus client** (resumable) to `<CLOUDFLARE_ACCESS_PROTECTED_ORIGIN>/uploads`.
  * Fallback: multipart `POST /ingest` with auth header; chunked streaming with retry.
* **Auth**:

  * On first run, open a webview to Cloudflare Access login to acquire a token (or use device browser). Cache Access JWT and refresh as needed.
* **Return flow**:

  * After successful upload, launch browser to `https://transcriber.solfamily.group/view?id=<job_id>`.
* **Permissions**:

  * `RECORD_AUDIO`, `FOREGROUND_SERVICE`, `WAKE_LOCK`, `POST_NOTIFICATIONS` (optional for status), `INTERNET`.
* **Edge handling**:

  * Low battery: keep service alive; warn user if OS threatens to kill foreground service.
  * Disk full: fail early with user message.
  * Network loss: tus resumes later; push notification when upload completes.

**Minimal UI:**

* First-time setup screen (permissions + test recording).
* While running: persistent notification with **stop** action and elapsed time.

---

### 3) iOS Shortcuts (v1 approach)

**Deliverables for user (not code in repo):**

* Shortcut **Quick Dictate (👤)** and **Quick Meeting (👥)** that:

  1. **Record Audio** (unlimited) → Save to **On My iPhone** (WAV/FLAC).
  2. Rename to timestamp (or provided `name`).
  3. **POST** to `https://transcriber.solfamily.group/ingest` with multipart form:

     * fields: `file`, `mode=single|multi`, `name`, `source=ios-shortcut`.
  4. On success, **Open URL** to `https://transcriber.solfamily.group/view?id=<job_id>`.
* The web app's 👤/👥 buttons link to `shortcuts://run-shortcut?name=...`.

*(Later: native iOS helper can mirror Android Bridge; v1 relies on Shortcuts which supports background recording reliably and is user-installable.)*

---

### 4) Backend: n8n + ASR + Storage + DB

**Docker Compose services:**

* `caddy` (reverse proxy)
* `n8n`
* `asr-gateway` (Faster-Whisper OpenAI-compatible server, GPU)
* `whisperx-worker` (GPU)
* `postgres`
* `tusd` (optional, for resumable uploads)
* `redis` (optional, for queues and job status pub/sub)

**Volumes & Paths (bind mounts):**

* `/data/audio/<user_id>/<recording_id>.{wav,flac,opus}`
* `/data/transcripts/<user_id>/<recording_id>.{txt,srt,vtt,json}`
* `/data/tmp` (tmpfs if desired for staging)

**Postgres Schema (DDL sketch):**

```sql
create table users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  display_name text,
  created_at timestamptz default now()
);

create table recordings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  name text not null,              -- default timestamp string
  mode text check (mode in ('single','multi')) not null,
  created_at timestamptz default now(),
  duration_seconds int,
  status text check (status in ('queued','processing','done','failed')) not null default 'queued',
  audio_path text not null,        -- absolute path on disk
  transcript_ready boolean default false
);

create table transcripts (
  recording_id uuid primary key references recordings(id) on delete cascade,
  text_path text,                  -- .txt
  vtt_path text,                   -- .vtt
  srt_path text,                   -- .srt
  diarization_json_path text,      -- for multi / whisperx
  language text,
  words_json_path text,            -- optional word-level timings
  created_at timestamptz default now()
);
```

**n8n Workflows (must be created):**

*A. `/ingest` (webhook)*

* Input: multipart form (`file`, `mode`, `name?`, inferred `user_id` from Access JWT headers).
* Steps:

  1. Validate mode + auth; create `recordings` row with `status='queued'`.
  2. Save uploaded file to `/data/audio/<user_id>/<recording_id>.flac` (or as received).
  3. Queue **Transcribe Job**: set `status='processing'` and invoke workflow B with payload (recording\_id, mode, paths).
  4. Respond `200 { job_id: <recording_id> }`.

*B. Transcribe Job (called by A or by tusd webhook)*

* Branch by `mode`:

  * **single**:

    * Call `asr-gateway` (model `large-v3` by default) with file path.
    * Save outputs `.txt`, `.vtt`, `.srt`.
  * **multi**:

    * Call `asr-gateway` (model `medium.en` or `large-v3`), then call `whisperx-worker` to align words + diarize speakers.
    * Save `.txt/.vtt/.srt` and `diarization.json` (segments with speaker labels).
* Update `transcripts` and set `recordings.status='done'`, `transcript_ready=true`.
* On error: `status='failed'` + error detail.

*C. `/api/recordings` (webhook GET)*

* Auth: derive user from Cloudflare Access header; list last N items for `user_id`.

*D. `/api/recordings/:id` (webhook GET)*

* Return transcript text, diarization JSON if any, and **signed URLs** for audio and files (or proxy download endpoints that re-check auth).

*E. `/api/jobs/:id` (webhook GET)*

* Return status + progress (if available) for polling.

**asr-gateway (Faster-Whisper server)**

* Must expose OpenAI-compatible `POST /v1/audio/transcriptions`:

  * Accept `model`, `file`, `language?`, `temperature?`, `prompt?`.
  * Return `{ text: "...", language: "en", segments: [...] }` if available.

**whisperx-worker**

* Accept CLI or HTTP to perform alignment + diarization given an existing transcript/audio; return diarization JSON and aligned words.
* GPU-enabled container; can share model cache volume.

**tusd (optional but recommended)**

* Handles large, resumable uploads out-of-the-box.
* Configure a **post-finish hook** to HTTP-callback n8n with user\_id/mode/name/uploaded\_file\_path to start workflow B.
* Web app and Android Bridge both speak tus.

---

## Security & Auth

* **Cloudflare Access** protects all routes. Web and Android/iOS clients obtain and pass Access JWT as `Authorization: Bearer <token>` or a CF-specific header; server verifies signature.
* **Caddy** adds `X-Robots-Tag: noindex` and denies everything without valid Access session.
* **Per-user** authorization checks on every API + download request.
* **Signed URLs** (short TTL) for downloading audio/transcripts, or proxy endpoints that stream files after auth check.
* **Rate limits** on `/ingest` and uploads.
* **CORS** locked to the transcriber origin.

---

## File Conventions

* **Default name**: `YYYYMMDDHHMMSS` (24h, zero-padded; local TZ).
* **Extensions**: prefer `.flac` (lossless, smaller) or `.wav` (PCM). Accept `.m4a`, `.mp3`, `.ogg`, `.opus`.
* **Paths**:

  * Audio: `/data/audio/<user_id>/<recording_id>.<ext>`
  * Transcripts: `/data/transcripts/<user_id>/<recording_id>.{txt,srt,vtt,json}`

---

## Caddy & Cloudflare Access (outline)

* Caddy routes:

  * `/` → web app
  * `/api/*` → n8n webhook endpoints
  * `/ingest` → n8n ingest webhook
  * `/uploads/*` → tusd (if enabled)
  * Static files for transcript downloads (or proxy endpoints)
* Set headers:

  * `Permissions-Policy: microphone=()` (web app doesn't need mic if using native capture)
  * `X-Robots-Tag: noindex, nofollow`
* Cloudflare Access policy:

  * Allowlist specific emails/domains.
  * Pass JWT claims (email, sub) to origin via headers for `user_id` lookups.

---

## Desktop Convenience (nice-to-have for v1.1)

* Add a **record hotkey** helper (Electron mini-tray app) that:

  * Captures mic to WAV, saves to `~/Recordings/Transcriber/<timestamp>.wav`, and uploads (tus or multipart), then opens the transcript page.
  * Uses the same Access token via an OAuth device flow or cookie hand-off.

---

## Error Handling & Edge Cases

* **Upload failures**: tus resumes; multipart retries with exponential backoff.
* **ASR server unavailable**: queue job, notify user status; optional fallback to CPU.
* **WhisperX failure**: still deliver base transcript; flag diarization as failed.
* **Storage full**: reject uploads gracefully with actionable message.
* **Huge files**: warn at client, enforce server max duration and size; suggest meeting split.

---

## Observability

* Structured logs with correlation IDs (`recording_id`, `user_id`) across web, n8n, asr-gateway, whisperx-worker.
* Health endpoints for ASR and WhisperX.
* (Optional) Prometheus metrics for queue depth, job durations, errors.

---

## Project Structure (monorepo suggested)

```
/transcriber
  /web           # PWA frontend
  /android-bridge
  /n8n           # workflow exports + helper scripts
  /asr-gateway   # Docker context / configs
  /whisperx      # Docker context / scripts
  /infra         # docker-compose.yml, caddy config, CF Access notes
  /db            # schema.sql, migrations
  /docs          # SPEC.md (this), API.md, FLOWS.md
```

---

## API Contracts (examples)

**POST /ingest (multipart)**

* Headers: `Authorization: Bearer <AccessJWT>`
* Fields:

  * `file`: binary
  * `mode`: `single` | `multi`
  * `name` (optional): string
  * `source`: `android-bridge` | `ios-shortcut` | `web-desktop`
* Response: `200 { job_id: "<uuid>" }`

**GET /api/recordings?limit=50**

* Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "20250907162602",
      "mode": "multi",
      "created_at": "2025-09-07T20:26:02Z",
      "duration_seconds": 3780,
      "status": "done"
    }
  ]
}
```

**GET /api/recordings/\:id**

```json
{
  "id": "uuid",
  "name": "20250907162602",
  "mode": "multi",
  "created_at": "2025-09-07T20:26:02Z",
  "duration_seconds": 3780,
  "status": "done",
  "transcript_text": "…",
  "download_audio_url": "https://.../signed/audio",
  "download_txt_url": "https://.../signed/txt",
  "download_srt_url": "https://.../signed/srt",
  "download_vtt_url": "https://.../signed/vtt",
  "diarization_json": { "segments": [ /* optional */ ] }
}
```

**GET /api/jobs/\:id**

```json
{ "id":"uuid", "status":"processing", "progress":0.42 }
```

---

## Model Choices & Defaults

* **👤 Single**: Faster-Whisper `large-v3` (CUDA FP16)
* **👥 Multi**: Faster-Whisper `medium.en` (or `large-v3`), then WhisperX diarization + alignment
* Language auto-detect; option to pin `language=en` for speed.

---

## Acceptance Criteria

* iOS: tap 👤/👥 in web → Shortcut launches → screen can lock → recording saved locally → uploaded → redirected to transcript page when done.
* Android: tap 👤/👥 in web → deep link opens Bridge app → background recording works with screen off → saved → resumable upload → redirect to transcript page on completion.
* Desktop: drag & drop a `.wav/.flac/.m4a/.mp3` file into web → transcript appears; history shows it.
* History dropdown loads last 50 items; selecting one populates transcript and enables downloads.
* Audio stored only on Sol; transcripts saved to disk + Postgres metadata. No third-party storage.

---

## Tasks for agent (generate code & configs)

1. **Scaffold `web/` PWA** with the UI elements above, platform detection helpers, history pages, and API client (fetch wrapper with Access JWT).
2. **Help implement deep-link launchers** for iOS Shortcuts and Android Bridge; parameterize `name` and `mode`.
3. **3. **Add to the `docker-compose.yml`** whatever additional is needed for this: already have n8n, postgres, will need asr-gateway, whisperx-worker, (optional tusd), volumes for `/data/audio` and `/data/transcripts`.
4. **Provide Caddy config** with reverse proxy routes, security headers, and `X-Robots-Tag: noindex`.
5. **Export n8n workflows** for `/ingest`, `/api/recordings`, `/api/recordings/:id`, `/api/jobs/:id`, and the Transcribe Job; include HTTP Request nodes to ASR and WhisperX and file-write nodes.
6. **Add `db/schema.sql`** for the tables above; include seed script to auto-create user rows on first request (look up by email).
7. **Build `android-bridge/`** app with:

   * Deep link handling,
   * Foreground service recorder (WAV or FLAC),
   * Tus client uploads with Access JWT,
   * Notification and return-to-browser flow.
8. **(Optional) Add tusd** service and configure post-finish hook to n8n.
9. **Implement signed download URLs** or secure proxy endpoints.
10. **Write `docs/API.md` and `docs/FLOWS.md`** reflecting actual routes, request/response shapes, and job life-cycle.

---

## Additional Context & References

**Repository Structure:** This project is maintained at `tfp24601/transcriber-system` on GitHub.

**System Context:** For complete infrastructure details, see `tfp24601/SystemsInfoRepo`:
- **Hardware specs**: Sol workstation (Ryzen 9 7950X, RTX 4090, 128GB RAM)
- **Network setup**: Caddy reverse proxy + Cloudflared tunnels via Lunanode4 VPS
- **Current Docker stack**: `/home/ben/SolWorkingFolder/docker-stack/docker-compose.yml`
- **Caddy config**: See `Lunanode4 -etc-caddy-Caddyfile contents.md` in SystemsInfoRepo
- **Cloudflared config**: See `Lunanode4 -etc-cloudflared-config.yml contents.md` in SystemsInfoRepo

**Development Environment:**
- **Local development**: Sol workstation (Ubuntu 24.04.2, XFCE)
- **GPU acceleration**: RTX 4090 available for Whisper models
- **Storage**: Local project folder `/home/ben/SolWorkingFolder/CustomSoftware/transcriber`
- **Domain**: `transcriber.solfamily.group` (requires Caddy + Cloudflared config updates on Lunanode4)

**AI Agent Collaboration:**
- **GitHub Copilot**: Repository-specific instructions in `.github/copilot-instructions.md`
- **Claude Code**: Access via GitHub integration or local permissions
- **Context source**: Reference SystemsInfoRepo for infrastructure understanding the `docker-compose.yml`** whatever additional is needed for this: already have n8n, postgres,, will need asr-gateway, whisperx-worker, (optional tusd), volumes for `/data/audio` and `/data/transcripts`.
4. **Provide Caddy config** with reverse proxy routes, security headers, and `X-Robots-Tag: noindex`.
5. **Export n8n workflows** for `/ingest`, `/api/recordings`, `/api/recordings/:id`, `/api/jobs/:id`, and the Transcribe Job; include HTTP Request nodes to ASR and WhisperX and file-write nodes.
6. **Add `db/schema.sql`** for the tables above; include seed script to auto-create user rows on first request (look up by email).
7. **Build `android-bridge/`** app with:

   * Deep link handling,
   * Foreground service recorder (WAV or FLAC),
   * Tus client uploads with Access JWT,
   * Notification and return-to-browser flow.
8. **(Optional) Add tusd** service and configure post-finish hook to n8n.
9. **Implement signed download URLs** or secure proxy endpoints.
10. **Write `docs/API.md` and `docs/FLOWS.md`** reflecting actual routes, request/response shapes, and job life-cycle.
