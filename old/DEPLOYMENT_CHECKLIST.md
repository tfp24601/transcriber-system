# Transcriber N8n Workflow Fixes - Deployment Checklist

## ✅ **Step 1: Database Schema Update**
```bash
# Connect to your PostgreSQL database and run:
psql -U transcriber -d transcriber_db -f migration-script.sql
```

## ✅ **Step 2: Update N8n Workflow Nodes**

### **2.1 Fix Audio File Reading Nodes:**
1. Open N8n workflow "Transcriber - Transcribe Job"
2. **"Read Audio File (single)" node:**
   - Delete current node
   - Add new `Read Binary Files` node
   - Set operation: `read`
   - Set file selector: `={{ $node["Parse Job Data"].json["audioPath"] }}`

3. **"Read Audio File (multi)" node:**
   - Delete current node  
   - Add new `Read Binary Files` node
   - Set operation: `read`
   - Set file selector: `={{ $node["Parse Job Data"].json["audioPath"] }}`

### **2.2 Fix Processing Logic Nodes:**
1. **"Process Single Result" node:**
   - Copy code from `process-single-result-code.js`
   - Replace entire JavaScript code block

2. **"Process Multi Result" node:**
   - Copy code from `process-multi-result-code.js`
   - Replace entire JavaScript code block

### **2.3 Fix HTTP Request Nodes:**
1. **"Single Speaker Transcribe" node:**
   - Change `inputDataFieldName` from `"audioFile"` to `"data"`

2. **"Multi Speaker Transcribe" node:**
   - Change `inputDataFieldName` from `"audioFile"` to `"data"`

3. **"Diarize Audio" node:**
   - Change `inputDataFieldName` from `"audioFile"` to `"data"`

### **2.4 Fix Database Query Parameters:**
1. **"Save Transcript Record" node:**
   - Update query parameters to use correct field names:
     - `$json.recordingId` (not `recording_id`)
     - `$json.language` (not `language_detected`)
     - `$json.processing_time_seconds` (not `duration_seconds`)

2. **"Update Recording Status" node:**
   - Update query parameters similarly

## ✅ **Step 3: Test the Pipeline**

### **3.1 Create Test Data Directory:**
```bash
mkdir -p /data/audio/test-user-id
mkdir -p /data/transcripts/test-user-id
```

### **3.2 Test File Upload:**
```bash
# Test the file ingest endpoint
curl -X POST https://n8n.solfamily.group/webhook/ingest \
  -F "file=@test-audio.wav" \
  -F "mode=single" \
  -F "name=test-recording" \
  -F "source=web-desktop"
```

### **3.3 Check Workflow Execution:**
1. Monitor N8n workflow execution logs
2. Check database for new records in `transcriber.recordings`
3. Verify files are created in `/data/transcripts/`

## ✅ **Step 4: Verify All Endpoints**

### **4.1 Test API Endpoints:**
```bash
# List recordings
curl https://n8n.solfamily.group/webhook/api/recordings

# Get recording detail  
curl https://n8n.solfamily.group/webhook/api/recordings/{recording-id}

# Check job status
curl https://n8n.solfamily.group/webhook/api/jobs/{job-id}
```

## ✅ **Step 5: Production Readiness**

### **5.1 Enable Cloudflare Access:**
- Update webhook nodes to properly handle Cloudflare Access headers
- Test with real user authentication

### **5.2 Configure File Serving:**
- Set up file download endpoints for transcripts
- Configure signed URLs for security

### **5.3 Monitor and Logging:**
- Set up workflow error handling
- Configure logging for debugging

## 🚨 **Common Issues & Solutions**

**Issue**: "File not found" errors
- **Solution**: Ensure `/data/audio` and `/data/transcripts` directories exist with proper permissions

**Issue**: Binary data not reaching ASR services
- **Solution**: Verify `Read Binary Files` nodes are used (not Execute Command)

**Issue**: Database constraint errors  
- **Solution**: Ensure `transcriber` schema exists and migration script was run

**Issue**: Placeholder data in transcripts
- **Solution**: Verify Process Result nodes have updated JavaScript code

## 📁 **Files Reference**
- `process-single-result-code.js` - Single speaker processing logic
- `process-multi-result-code.js` - Multi speaker processing logic  
- `migration-script.sql` - Database schema migration
- `schema-with-transcriber.sql` - Complete schema with transcriber namespace

## ✅ **Verification Commands**
```bash
# Check database schema
psql -U transcriber -c "\dt transcriber.*"

# Check workflow status
curl -H "X-N8N-API-KEY: your-api-key" \
  https://n8n.solfamily.group/api/v1/workflows

# Test file permissions
ls -la /data/audio /data/transcripts
```