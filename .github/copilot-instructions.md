# Transcriber Flask App – AI Agent Playbook

## 🎯 Quick Summary

The active product is the **GPU-accelerated Flask transcription app** in `flask-app/`. All legacy services (PWA, n8n workflows, Docker stack, etc.) were archived to `old/legacy-stack/` on 2025-09-29; treat them as read-only historians unless a task explicitly says to revive or reference them. Every change, test, and deployment plan should focus on the Flask codebase.

---

## 🚨 Critical Guardrails

- **No VS Code search**: Built-in search freezes the session. Use terminal tools (`grep`, `rg`, `find`) instead.
- **Stay in the active tree**: Touch `flask-app/` (and supporting docs) only. Do not modify anything under `old/legacy-stack/` unless the user says so.

---

## 📁 Current Layout

```
transcriber/
  flask-app/
    app.py                # Flask entrypoint + Faster-Whisper integration
    requirements.txt      # Flask + faster-whisper + numpy
    templates/            # HTML UI
    static/               # CSS/JS assets
    transcriptions/       # Output files (TXT/SRT)
    README.md             # Local quick-start
    .venv/                # Python 3.12 virtualenv (preferred interpreter)
  docs/
    gpu-acceleration-milestone.md  # Notes on enabling GPU + testing
  old/
    legacy-stack/         # Archived monorepo (PWA, n8n, Docker, etc.)
```

---

## 🛠️ Day-to-Day Workflow

1. **Activate the virtualenv**
   ```bash
   cd /home/ben/SolWorkingFolder/CustomSoftware/transcriber/flask-app
   source .venv/bin/activate
   ```

2. **Launch the server (GPU-enabled)**
   ```bash
   LD_DIR="$PWD/.venv/lib/python3.12/site-packages/nvidia/cudnn/lib"
   nohup env \
     LD_LIBRARY_PATH="$LD_DIR:${LD_LIBRARY_PATH:-}" \
     CT2_USE_CUDNN=1 \
     WHISPER_DEFAULT_USE_GPU=true \
     WHISPER_DEVICE=cuda \
     WHISPER_GPU_DEVICE=cuda \
     WHISPER_GPU_COMPUTE_TYPE=float16 \
     WHISPER_CPU_COMPUTE_TYPE=float32 \
     WHISPER_VAD=true \
     PATH="$PWD/.venv/bin:$PATH" \
     "$PWD/.venv/bin/python" app.py >/tmp/transcriber-flask.log 2>&1 &
   ```

3. **Stop the server**
   ```bash
   pkill -f "flask-app/.venv/bin/python app.py"
   ```

4. **Check status/logs**
   ```bash
   tail -n 20 /tmp/transcriber-flask.log
   ```

5. **Smoke-test GPU path**
   ```bash
   curl -s -X POST http://127.0.0.1:5000/transcribe \
     -F "audio=@/tmp/test-tone.wav" \
     -F "use_gpu=true" \
     -F "model=small" \
     -F "language=auto"
   ```
   Expect `"device": "cuda"` and `"gpu_used": true` in the JSON response.

> Legacy sync scripts (`sync_online_repos_to_local.sh`, `sync_local_to_online_repos.sh`) live in the archive. Use standard git unless a task explicitly revives them.

---

## 🌐 Deployment Objectives

- Serve the Flask UI at `https://transcriber.solfamily.group` via Caddy + Cloudflared.
- Replace the legacy backend currently mapped behind that domain with this Flask service when production-ready.
- Keep the GPU runtime (cuDNN 9, CUDA 12.4) available on the host; reuse the same environment variables as the local run.
- Future idea: surface buttons/endpoints that trigger n8n workflows (e.g., “Polish this as an email”). Design hooks but do not depend on archived workflows until instructed.

---

## 🔍 Key Files & References

| Path | Why it matters |
| --- | --- |
| `flask-app/app.py` | Whisper model loading, cuDNN detection, request handling |
| `flask-app/templates/index.html` | UI for uploads + options |
| `flask-app/static/` | Styling/scripts used by the UI |
| `flask-app/requirements.txt` | Dependency pinning |
| `docs/gpu-acceleration-milestone.md` | What changed to enable GPU + validation steps |
| `old/legacy-stack/` | Historical code for reference only |
| `docs/API.md` | n8n API code location |

External references:
- SystemsInfoRepo (hardware, networking, reverse proxy patterns)
- **Existing Docker stack**: `/home/ben/SolWorkingFolder/docker-stack/docker-compose.yml`
- Archived docs in `old/legacy-stack/docs/` when historical context is needed

---

## ✅ Definition of Done (Flask tasks)

A change is complete when:
- The Flask service runs without errors (log is clean).
- GPU metadata shows `gpu_used: true` when requested with `use_gpu=true`.
- The UI remains clear and functional (no heavy dependencies unless required).
- Documentation reflects user-facing or operational changes.
- Archived stack remains untouched (or intentional edits are clearly documented).

---

## 🧭 Roadmap Reminders (Future, not current work)

1. **Reverse proxy rollout** – prepare Caddy/Cloudflared configs for production deployment.
2. **n8n workflow buttons** – add endpoints or UI hooks to trigger future AI post-processing.
3. **Service automation** – convert the nohup command into a managed service (systemd).
4. **UX improvements** – better status messaging, transcript previews, optional auth.

Update this playbook as those initiatives go live.

---

## 🧪 Testing Checklist

- Upload short WAV/MP3 → transcript returns quickly with GPU metadata.
- Toggle GPU option in UI → CPU fallback still works.
- Verify files saved in `transcriptions/` (TXT + SRT).
- Review `/tmp/transcriber-flask.log` for cuDNN/CUDA warnings.
- Optional: Stress-test with longer recordings to confirm stability on RTX 4090.

---

## 🤖 Guidance for AI Agents

- Clarify assumptions about legacy components. Ask before touching `old/legacy-stack/`.
- Prefer enhancing existing Flask code instead of introducing new frameworks.
- Provide configuration snippets (e.g., Caddy) rather than applying them directly.
- Keep explanations user-friendly; the maintainer expects pragmatic, no-jargon guidance.

---

**TL;DR:** Work inside `flask-app/`, keep GPU inference running, prep for Caddy deployment, and treat the archived monorepo as read-only history.

## 🔌 n8n API Integration Guide

### API Access & Authentication

**n8n Instance**: `https://n8n.solfamily.group`
**API Key Location**: `/home/ben/SolWorkingFolder/CustomSoftware/transcriber/docs/API.md`
**OpenAPI Schema**: `/home/ben/SolWorkingFolder/CustomSoftware/transcriber/reference/n8n API uploads/openapi.yml`

### Common n8n API Operations

#### 1. List Workflows
```bash
curl -s "https://n8n.solfamily.group/api/v1/workflows" \
  -H "X-N8N-API-KEY: [API_KEY_FROM_API_MD]" | jq '.data[] | {id, name}'
```

#### 2. Get Specific Workflow
```bash
curl -s "https://n8n.solfamily.group/api/v1/workflows/{WORKFLOW_ID}" \
  -H "X-N8N-API-KEY: [API_KEY_FROM_API_MD]"
```

#### 3. Update Workflow (CRITICAL SCHEMA)
**Required Fields**: `name`, `nodes`, `connections`, `settings`

```bash
# Extract proper schema from workflow file
jq '{name, nodes, connections, settings}' "n8n/workflows/[WORKFLOW_FILE].json" > /tmp/workflow_update.json

# Update via API
curl -X PUT "https://n8n.solfamily.group/api/v1/workflows/{WORKFLOW_ID}" \
  -H "X-N8N-API-KEY: [API_KEY_FROM_API_MD]" \
  -H "Content-Type: application/json" \
  -d @/tmp/workflow_update.json
```

#### 4. Common Workflow Issues & Fixes

**Parse Job Data Node Error**: `Cannot read properties of undefined (reading 'recordingId')`
- **Problem**: Using `$input.first().body` for webhook data
- **Solution**: Use `$json` instead
```js
// WRONG:
const data = $input.first().body;

// CORRECT:
const data = $json;
```

**Read Audio File Node Error**: Binary data not properly handled
- **Problem**: Using `executeCommand` with `cat` for file reading
- **Solution**: Use `readWriteFile` node type
```json
// WRONG:
{
  "type": "n8n-nodes-base.executeCommand",
  "parameters": {
    "command": "=cat {{ $json.audioPath }}"
  }
}

// CORRECT:
{
  "type": "n8n-nodes-base.readWriteFile",
  "parameters": {
    "operation": "read",
    "fileName": "={{ $json.audioPath }}",
    "dataPropertyName": "audioFile"
  }
}
```

### n8n Workflow Development Best Practices

1. **Always backup before changes**: Get workflow via API first
2. **Use proper schema**: Only include required fields in PUT requests  
3. **Test webhook data**: Use `console.log()` in Code nodes for debugging
4. **Binary data handling**: Use `readWriteFile` for file operations
5. **Reference existing workflows**: Study working patterns in `/n8n/workflows/`

### Key Workflow Files
- `01 Transcriber - File Ingest.json` - ✅ WORKING
- `02 Transcriber - Transcribe Job.json` - ✅ FIXED (Parse Job Data + Read Audio File nodes)
- `03-api-recordings-live.json` - Status unknown

### Debugging n8n Workflows

1. **Check Execution Logs**: n8n UI → Executions tab
2. **Add Debug Logging**: Use `console.log()` in Code nodes
3. **Validate Data Structure**: Check webhook payload format
4. **Test Individual Nodes**: Run workflow step-by-step

### n8n API Schema Reference

**Workflow Schema** (from OpenAPI):
```yaml
workflow:
  type: object
  required: [name, nodes, connections, settings]
  properties:
    name: {type: string}
    nodes: {type: array, items: {$ref: '#/components/schemas/node'}}
    connections: {type: object}
    settings: {type: object}
```

**Node Schema** (critical for updates):
```yaml
node:
  type: object
  properties:
    id: {type: string}
    name: {type: string}
    type: {type: string}
    typeVersion: {type: number}
    parameters: {type: object}
    position: {type: array}
```

*For questions about infrastructure integration, always reference SystemsInfoRepo first.*
