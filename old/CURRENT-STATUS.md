# Transcriber System - Current Status

**Date**: September 13, 2025  
**Time**: Late evening  
**Session**: Troubleshooting upload failure  

## 🎯 Current Issue: Upload Still Failing

**Problem**: User gets "Upload failed" error when trying to upload audio recordings through the web interface at https://transcriber.solfamily.group

**What We Fixed Tonight**:
- ✅ **WhisperX Worker Service**: Replaced LinuxServer Wyoming-protocol image with proper OpenAI-compatible HTTP API
- ✅ **Both GPU Services Now Healthy**: 
  - ASR Gateway (port 8002): `curl localhost:8002/health` returns "OK"
  - WhisperX Worker (port 8001): `curl localhost:8001/health` returns "OK"
- ✅ **Service Configuration**: Both now use `fedirz/faster-whisper-server:latest-cuda` image

**But Upload Still Fails**: Despite fixing the GPU services, user still gets "Upload failed" error.

## 🔍 Next Steps for Tomorrow

### 1. **Check N8n Workflow Logs**
The upload failure is likely in the N8n file ingest workflow. Need to:
```bash
# Check workflow execution logs
curl -H "X-N8N-API-KEY: [API_KEY]" "https://n8n.solfamily.group/api/v1/executions?limit=10"

# Or check via N8n UI at n8n.solfamily.group
```

### 2. **Verify Upload Endpoint**
Test the upload endpoint directly:
```bash
# Test if the webhook responds
curl -X POST https://n8n.solfamily.group/webhook/ingest \
  -F "file=@test.wav" \
  -H "cf-access-authenticated-user-email: user@example.com"
```

### 3. **Check TusD Upload Server**
The web app might be using TusD for resumable uploads:
```bash
# Check TusD logs
docker logs transcriber-tusd --tail 50

# Test TusD endpoint
curl -X POST http://localhost:1080/files/
```

### 4. **Frontend Error Investigation**
Check browser developer tools when upload fails:
- Network tab: See exact error response
- Console tab: Check for JavaScript errors
- Look at the actual HTTP request being made

## 📊 Current System State

### ✅ **Working Components**
- **Web Interface**: https://transcriber.solfamily.group (accessible)
- **Database**: PostgreSQL with `transcriber` schema (confirmed working)
- **GPU Services**: Both ASR gateway and WhisperX worker responding
- **N8n Instance**: Running at n8n.solfamily.group
- **Authentication**: Cloudflare Access configured

### 🔧 **Service Status**
```bash
# All transcriber containers
docker ps -f name=transcriber
# NAMES                         STATUS                   PORTS
# transcriber-web               Up 3 days               0.0.0.0:3010->80/tcp
# transcriber-tusd              Up 3 days               0.0.0.0:1080->1080/tcp  
# transcriber-asr-gateway       Up 23 minutes           0.0.0.0:8002->8000/tcp
# transcriber-whisperx-worker   Up 1 minute             0.0.0.0:8001->8000/tcp
```

### ⚠️ **Unknown Status**
- **N8n Workflows**: 5 transcriber workflows exist, but don't know if they're properly configured
- **File Upload Flow**: Don't know if web app uses TusD or direct N8n webhook
- **Error Source**: Could be frontend, N8n workflow, or authentication issue

## 🔑 **Access Information**

### **API Keys & Credentials**
- **N8n API Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZTZjNjZlZi0yMjczLTQwOGEtODM4OC1mYjZjYmE1ZWU5NGEiLCJpYXQiOjE3MjYxODkwODV9.WY1U3MKoN8DFHfCWqWBqsz6KrXQDfKPr64vhOAOLa_E`
- **Database**: Connected to existing `main_sol_db` with `transcriber` schema

### **Key URLs**
- **Web App**: https://transcriber.solfamily.group
- **N8n Interface**: https://n8n.solfamily.group  
- **Upload Webhook**: https://n8n.solfamily.group/webhook/ingest
- **Local GPU Services**: localhost:8001, localhost:8002

## 📁 **File Locations**

### **Project Root**
```
/home/ben/SolWorkingFolder/CustomSoftware/transcriber/
```

### **Docker Stack**
```
/home/ben/SolWorkingFolder/docker-stack/docker-compose.yml
```

### **Data Directories** (should exist)
```
/home/ben/SolWorkingFolder/CustomSoftware/transcriber/data/
├── audio/       # User audio files
├── transcripts/ # Generated transcripts  
└── uploads/     # Temporary uploads
```

## 🚀 **Working Context**

**What User Can Do Tomorrow**:
1. Start by checking N8n workflow logs in the UI
2. Test upload endpoint directly with curl
3. Check browser developer tools during failed upload
4. Verify data directories exist and have proper permissions

**What's Been Ruled Out**:
- ❌ GPU service configuration (both working)
- ❌ Basic Docker service health (all running)
- ❌ Database connectivity (confirmed working)

**Most Likely Culprits**:
- 🔍 N8n workflow error (processing logic or parameter validation)
- 🔍 Authentication headers not being passed correctly
- 🔍 File upload method mismatch (TusD vs direct webhook)
- 🔍 Missing data directories or permission issues

## 📋 **Quick Diagnostic Commands**

```bash
# Check all transcriber services
docker ps -f name=transcriber

# Test GPU services
curl localhost:8002/health && echo " - ASR OK"
curl localhost:8001/health && echo " - WhisperX OK"

# Check N8n workflows via API  
curl -H "X-N8N-API-KEY: [API_KEY]" "https://n8n.solfamily.group/api/v1/workflows"

# Check data directories
ls -la /home/ben/SolWorkingFolder/CustomSoftware/transcriber/data/

# Test database connection
PGPASSWORD="AvenR3n33" psql -h localhost -p 5432 -U ben -d main_sol_db -c "\dt transcriber.*"
```

---

**Resume Point**: User still getting "Upload failed" despite GPU services being fixed. Need to trace the upload flow from frontend → N8n → database to find where it's breaking.