# Setting Up Local Diarization (pyannote)

## Issue
You're getting a 403 error when trying to use local diarization because the pyannote models are **gated** - they require accepting license terms on Hugging Face.

## Solution

### Step 1: Accept Model Licenses

You need to accept the terms for **BOTH** of these models:

1. **Main Model**: https://huggingface.co/pyannote/speaker-diarization-3.1
   - Click "Agree and access repository"
   
2. **Dependency Model**: https://huggingface.co/pyannote/speaker-diarization-community-1
   - Click "Agree and access repository"

### Step 2: Verify Your Hugging Face Token

1. Go to: https://huggingface.co/settings/tokens
2. Make sure your token has **READ** access
3. Copy your token

### Step 3: Update Your .env File

```bash
cd /home/ben/SolWorkingFolder/CustomSoftware/transcriber/flask-app
nano .env
```

Update this line:
```bash
HF_TOKEN=hf_your_actual_token_here
```

### Step 4: Restart the Service

```bash
./stop.sh
./start-production.sh
```

### Step 5: Test

1. Upload an audio file
2. Go to **Diarization** tab
3. Select **Local (pyannote - Uses VRAM)**
4. Click **Transcribe Audio**

You should see speaker labels like:
```markdown
## SPEAKER_00
[00:00:05] Hello everyone...

## SPEAKER_01
[00:00:12] Thanks for joining...
```

## Troubleshooting

**Still getting 403 errors?**
- Wait 5-10 minutes after accepting the licenses (Hugging Face needs time to update permissions)
- Make sure you're logged into Hugging Face with the same account that owns the token
- Try creating a NEW token with READ access

**Alternative: Use AssemblyAI**
If you can't get pyannote working, use cloud-based diarization:
1. Get API key from: https://www.assemblyai.com/
2. Add to .env: `ASSEMBLYAI_API_KEY=your_key`
3. In UI, select **AssemblyAI API (Cloud)** instead of Local

## Why This Happens

The pyannote models use research data that requires accepting academic/research terms. It's a one-time setup per Hugging Face account.
