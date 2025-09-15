# Transcriber System Troubleshooting Guide

## Common Issues and Solutions

### File Upload Issues

#### Binary Data Loss
**Symptom**: Files upload but Save Audio File node fails  
**Solution**: Use Merge node to preserve binary data through workflow

#### Volume Mount Problems  
**Symptom**: Files don't appear on host system  
**Solution**: 
1. Check docker-compose volume mount: `./local-files:/files`
2. Restart container: `docker compose restart n8n`
3. Fix ownership: `docker exec -u root n8n chown -R node:node /files`

#### Wrong File Extensions
**Symptom**: All files saved as .wav  
**Solution**: Update workflow to extract and use original file extension

### Database Issues

#### Missing User Records
**Symptom**: Cannot find user error  
**Solution**: Ensure `get_or_create_user` function exists and works

#### UUID Generation Errors
**Symptom**: Null value in ID column  
**Solution**: Use `gen_random_uuid()` in INSERT statements

#### Parameter Errors in Updates
**Symptom**: "Could not get parameter valueToMatchOn"  
**Solution**: Add Edit Fields node to provide proper ID field

### Workflow Execution Issues

#### Parse Job Data Errors
**Symptom**: "Cannot read properties of undefined"  
**Solution**: Check webhook payload structure and data access

#### Container File Access
**Symptom**: Transcription services can't read files  
**Solution**: Ensure volume mounts are consistent across containers

### Authentication Issues

#### Cloudflare Headers Missing
**Symptom**: Authentication failures  
**Solution**: Check header extraction and provide fallback values

## Debugging Commands

### Check File Storage
```bash
# Host side
ls -la /home/ben/SolWorkingFolder/CustomSoftware/transcriber/local-files/

# Container side  
docker exec n8n ls -la /files/
```

### Check Database
```bash
# Recent recordings
docker exec postgres_db psql -U ben -d main_sol_db -c "SELECT * FROM transcriber.recordings ORDER BY created_at DESC LIMIT 5;"

# User records
docker exec postgres_db psql -U ben -d main_sol_db -c "SELECT * FROM transcriber.users;"
```

### Check n8n Executions
```bash
# List recent executions
curl -H "X-N8N-API-KEY: your-key" https://n8n.solfamily.group/api/v1/executions

# Get specific execution
curl -H "X-N8N-API-KEY: your-key" https://n8n.solfamily.group/api/v1/executions/{id}
```

### Check Container Status
```bash
# Service status
docker compose ps

# Container logs
docker compose logs n8n
docker compose logs postgres_db
```

## Resolution Steps

### For File Upload Issues
1. Test volume mount with simple file creation
2. Check container ownership and permissions  
3. Verify binary data preservation in workflow
4. Test with different file types/sizes

### For Database Issues  
1. Verify schema exists and functions work
2. Check parameter syntax in SQL queries
3. Ensure proper data types and constraints
4. Test queries manually in psql

### For Workflow Issues
1. Check n8n execution logs for detailed errors
2. Add debug logging to code nodes
3. Test individual nodes in isolation
4. Verify webhook payload structure

## Known Working Configurations

### Volume Mounts
```yaml
volumes:
  - /home/ben/SolWorkingFolder/CustomSoftware/transcriber/local-files:/files
  - /home/ben/SolWorkingFolder/CustomSoftware/transcriber/data:/data
```

### Database Connection
```
Host: postgres_db
Port: 5432  
Database: main_sol_db
User: ben
Schema: transcriber
```

### File Paths
- Upload storage: `/files/user_id/recording_id.ext`
- Transcripts: `/data/transcripts/user_id/recording_id.{txt,vtt,srt,json}`

## Emergency Recovery

### Reset File Storage
```bash
rm -rf /home/ben/SolWorkingFolder/CustomSoftware/transcriber/local-files/*
mkdir -p /home/ben/SolWorkingFolder/CustomSoftware/transcriber/local-files
chmod 775 /home/ben/SolWorkingFolder/CustomSoftware/transcriber/local-files
```

### Reset Database  
```sql
TRUNCATE transcriber.recordings CASCADE;
TRUNCATE transcriber.transcripts CASCADE; 
-- Users table typically kept
```

### Restart Services
```bash
cd /home/ben/SolWorkingFolder/docker-stack
docker compose restart n8n postgres_db
```
