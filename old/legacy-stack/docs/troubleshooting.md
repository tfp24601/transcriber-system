# Transcriber System Troubleshooting Guide

## Common Issues and Solutions

### File Upload Issues

#### Binary Data Loss

**Symptom**: Files upload but Save Audio File node fails.  
**Solution**: Use a Merge node to preserve binary data throughout the workflow.

#### Volume Mount Problems

**Symptom**: Files do not appear on the host system.  
**Solution**:

1. Check docker-compose volume mount: `./local-files:/files`
2. Restart container: `docker compose restart n8n`
3. Fix ownership: `docker exec -u root n8n chown -R node:node /files`

#### Wrong File Extensions

**Symptom**: All files saved as `.wav`.  
**Solution**: Update the workflow to extract and use the original file extension.

### Database Issues

#### Missing User Records

**Symptom**: Cannot find user error.  
**Solution**: Ensure the `get_or_create_user` function exists and works.

#### UUID Generation Errors

**Symptom**: Null value in ID column.  
**Solution**: Use `gen_random_uuid()` in `INSERT` statements.

#### Parameter Errors in Updates

**Symptom**: "Could not get parameter valueToMatchOn".  
**Solution**: Add an Edit Fields node to provide the proper ID field.

### Workflow Execution Issues

#### Parse Job Data Errors

**Symptom**: "Cannot read properties of undefined".  
**Solution**: Check webhook payload structure and data access.

#### Container File Access

**Symptom**: Transcription services cannot read files.  
**Solution**: Ensure volume mounts are consistent across containers.

### GPU / cuDNN Issues

#### GPU Disabled at Startup

**Symptom**: Web UI banner shows "GPU requirements missing" or server logs warn that GPU execution was disabled.

**Solution**:

1. Confirm the NVIDIA driver and GPU visibility: `nvidia-smi`
1. Ensure transcriber containers start with GPU access (Docker `--gpus all` or Compose `deploy.resources` block)
1. Verify cuDNN shared objects are present:

  ```bash
  ldconfig -p | grep libcudnn
  ls /usr/lib/x86_64-linux-gnu/libcudnn_ops.so*
  ```

1. If cuDNN is missing, install the matching CUDA/cuDNN runtime (see NVIDIA documentation) and restart the stack.

#### cuDNN Libraries Missing

**Symptom**: Flask logs contain `libcudnn_ops.so` load errors or the diagnostic list reports missing cuDNN.

**Solution**:

1. On Ubuntu/Debian with the CUDA repository configured, install:

   ```bash
   sudo apt install libcudnn8 libcudnn8-dev
   ```

   Make sure versions align with your CUDA toolkit.

1. For Conda environments, install within the environment:

   ```bash
   conda install -c conda-forge cudnn
   ```

1. Restart the Flask service after installation so the new libraries are detected.

#### Forced CPU Mode

**Symptom**: Metadata shows `device: cpu` even when GPU is requested, but no errors are raised.

**Solution**:

1. Check the diagnostic banner for details (missing GPU, cuDNN, or incompatible compute type).
2. Override compute type if necessary by setting `WHISPER_GPU_COMPUTE_TYPE=float32`.
3. When GPU acceleration is intentionally unavailable, keep the service running in CPU mode by leaving `CT2_USE_CUDNN=0`.

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

1. Test volume mount with simple file creation.
2. Check container ownership and permissions.
3. Verify binary data preservation in workflow.
4. Test with different file types or sizes.

### For Database Issues

1. Verify schema exists and functions work.
2. Check parameter syntax in SQL queries.
3. Ensure proper data types and constraints.
4. Test queries manually in `psql`.

### For Workflow Issues

1. Check n8n execution logs for detailed errors.
2. Add debug logging to code nodes.
3. Test individual nodes in isolation.
4. Verify webhook payload structure.

## Known Working Configurations

### Volume Mounts

```yaml
volumes:
  - /home/ben/SolWorkingFolder/CustomSoftware/transcriber/local-files:/files
  - /home/ben/SolWorkingFolder/CustomSoftware/transcriber/data:/data
```

### Database Connection

```text
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
