# cuDNN Upgrade Plan - October 2, 2025

## Current State

### System Configuration
- **OS**: Linux (Ubuntu/Debian based)
- **CUDA Version**: 12.0.140 (installed via nvcc)
- **GPU**: NVIDIA RTX 4090
- **Current cuDNN**: 8.9.2.26~cuda12+3 (installed via apt package `nvidia-cudnn`)

### Installed cuDNN 8.9.2 Files
Location: `/usr/lib/x86_64-linux-gnu/`

Libraries installed:
```
libcudnn.so.8.9.2
libcudnn.so.8 -> libcudnn.so.8.9.2
libcudnn.so -> libcudnn.so.8

libcudnn_ops_train.so.8.9.2
libcudnn_ops_train.so.8 -> libcudnn_ops_train.so.8.9.2
libcudnn_ops_train.so -> libcudnn_ops_train.so.8

libcudnn_ops_infer.so.8.9.2
libcudnn_ops_infer.so.8 -> libcudnn_ops_infer.so.8.9.2
libcudnn_ops_infer.so -> libcudnn_ops_infer.so.8

libcudnn_cnn_train.so.8.9.2
libcudnn_cnn_train.so.8 -> libcudnn_cnn_train.so.8.9.2
libcudnn_cnn_train.so -> libcudnn_cnn_train.so.8

libcudnn_cnn_infer.so.8.9.2
libcudnn_cnn_infer.so.8 -> libcudnn_cnn_infer.so.8.9.2
libcudnn_cnn_infer.so -> libcudnn_cnn_infer.so.8

libcudnn_adv_train.so.8.9.2
libcudnn_adv_train.so.8 -> libcudnn_adv_train.so.8.9.2
libcudnn_adv_train.so -> libcudnn_adv_train.so.8

libcudnn_adv_infer.so.8.9.2
libcudnn_adv_infer.so.8 -> libcudnn_adv_infer.so.8.9.2
libcudnn_adv_infer.so -> libcudnn_adv_infer.so.8
```

### Affected Applications

#### Transcriber App (BROKEN - needs cuDNN 9.x)
- **Location**: `/path/to/transcriber/flask-app/`
- **Dependencies**: 
  - `faster-whisper 1.2.0`
  - `ctranslate2 4.6.0` (requires cuDNN 9.1.0)
- **Status**: Workers crash with error: "Unable to load any of {libcudnn_ops.so.9.1.0...}"
- **Impact**: Currently non-functional

#### ComfyUI (Should remain working)
- **Location**: `/home/<user>/ComfyUI/`
- **Dependencies**: 
  - `torch 2.5.1+cu121` (PyTorch with CUDA 12.1 support)
- **Status**: Working
- **Impact**: Should continue working (PyTorch dynamically loads cuDNN, compatible with both 8.x and 9.x)

#### Other AI Tools
- Most modern AI tools use PyTorch or TensorFlow, which bundle or dynamically load cuDNN
- Forward compatibility means they should work with newer cuDNN versions

## Why We're Upgrading

### Root Cause
The transcriber app uses `ctranslate2 4.6.0`, which requires cuDNN 9.x libraries. The current system has cuDNN 8.9.2, causing version mismatch errors:

```
[2025-10-02 09:45:27] ERROR: Unable to load any of {libcudnn_ops.so.9.1.0, libcudnn_ops.so.9.1, libcudnn_ops.so.9, libcudnn_ops.so}
[2025-10-02 09:45:27] ERROR: Invalid handle. Cannot load symbol cudnnCreateTensorDescriptor
[2025-10-02 09:45:27] ERROR: Worker (pid:3663099) was sent code 134 (SIGABRT)
```

### Goals
1. Fix transcriber app worker crashes
2. Enable GPU-accelerated transcription with RTX 4090
3. Maintain compatibility with ComfyUI and other AI tools
4. Improve performance (cuDNN 9.x has optimizations for newer GPUs)

## Upgrade Plan

### Step 1: Backup Current Package State
```bash
# Save list of installed cuDNN packages
dpkg -l | grep -i cudnn > /path/to/transcriber/docs/cudnn-8-packages-backup.txt

# Save current package version
apt-cache policy nvidia-cudnn > /path/to/transcriber/docs/cudnn-8-version-backup.txt
```

### Step 2: Remove cuDNN 8.9.2
```bash
sudo apt remove --purge nvidia-cudnn
```

### Step 3: Install cuDNN 9.x for CUDA 12

**IMPORTANT**: As of October 2, 2025, cuDNN 9.x is NOT available in Ubuntu 24.04 repositories. Manual download from NVIDIA is required.

#### Method: NVIDIA .deb Package (REQUIRED - Manual Download)
1. Download cuDNN 9.x for CUDA 12 from NVIDIA Developer site:
   - **URL**: https://developer.nvidia.com/cudnn-downloads
   - **Requirements**: Free NVIDIA Developer account (sign up if needed)
   - **Select**: 
     - Linux
     - x86_64
     - Ubuntu
     - 24.04
     - deb (local)
   - **Save to**: `~/Downloads/`
   - **File name pattern**: `cudnn-local-repo-ubuntu2404-9.*.deb`

2. Install using the helper script:
```bash
cd ~/Downloads
/path/to/transcriber/docs/install-cudnn9.sh
```

   Or manually:
```bash
cd ~/Downloads
sudo apt remove --purge nvidia-cudnn -y
sudo dpkg -i cudnn-local-repo-ubuntu2404-9.*.deb
sudo cp /var/cudnn-local-repo-*/cudnn-*-keyring.gpg /usr/share/keyrings/
sudo apt update
sudo apt install libcudnn9-cuda-12 -y
```

### Step 4: Verify Installation
```bash
# Check installed version
dpkg -l | grep -i cudnn

# Verify libraries are accessible
ldconfig -p | grep cudnn

# Check for version 9 libraries
ls -la /usr/lib/x86_64-linux-gnu/libcudnn*
```

### Step 5: Test Transcriber App
```bash
# Restart Gunicorn
cd /path/to/transcriber/flask-app
pkill gunicorn
./run_gunicorn.sh

# Test transcription with small file
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@/usr/share/sounds/alsa/Front_Center.wav" \
  -F "model=small" \
  -F "language=auto"

# Check logs for errors
tail -f /tmp/transcriber-gunicorn.log
```

### Step 6: Test ComfyUI
```bash
# Start ComfyUI (or if already running, generate an image)
cd /home/<user>/ComfyUI
./venv/bin/python main.py

# Test basic image generation to verify CUDA/cuDNN still work
```

## Rollback Plan (If Something Goes Wrong)

### Scenario 1: ComfyUI or Other Tools Break

#### Quick Rollback to cuDNN 8.9.2
```bash
# Remove cuDNN 9
sudo apt remove --purge libcudnn9-cuda-12 libcudnn9-dev-cuda-12

# Reinstall cuDNN 8.9.2
sudo apt install nvidia-cudnn=8.9.2.26~cuda12+3

# Verify installation
dpkg -l | grep -i cudnn
ldconfig -p | grep cudnn
```

#### Alternative: Install Both Versions Side-by-Side
If we need both versions:
```bash
# Keep cuDNN 8 installed, add cuDNN 9 in custom location
# Download cuDNN 9 tarball from NVIDIA
# Extract to /usr/local/cuda-12.0/targets/x86_64-linux/lib/
# Set LD_LIBRARY_PATH for transcriber app only
```

### Scenario 2: Transcriber Still Doesn't Work with cuDNN 9

#### Downgrade CTranslate2 Instead

**NOTE**: Downgrading ctranslate2 alone will NOT work. Testing shows that `faster-whisper` has hard dependency on `ctranslate2>=4.0`, which requires cuDNN 9.x. All recent versions of faster-whisper (including 1.0.3) will automatically reinstall ctranslate2 4.6.0.

**Option A**: Downgrade to very old versions (NOT RECOMMENDED - loses features):
```bash
cd /path/to/transcriber/flask-app
source .venv/bin/activate

# Downgrade to ancient versions that work with cuDNN 8
pip install 'faster-whisper<0.10' --force-reinstall

deactivate
pkill gunicorn
./run_gunicorn.sh
```

**Option B**: Install cuDNN 9 (RECOMMENDED - see Step 3 above)

### Scenario 3: Complete System Issues

#### Full Rollback Steps
1. Remove all cuDNN packages:
   ```bash
   sudo apt remove --purge 'libcudnn*'
   ```

2. Reinstall exact previous version:
   ```bash
   sudo apt install nvidia-cudnn=8.9.2.26~cuda12+3
   ```

3. Hold the package to prevent auto-upgrade:
   ```bash
   sudo apt-mark hold nvidia-cudnn
   ```

4. Verify exact state matches backup:
   ```bash
   diff <(dpkg -l | grep cudnn) /path/to/transcriber/docs/cudnn-8-packages-backup.txt
   ```

## Testing Checklist

After upgrade, verify:

- [ ] cuDNN 9.x packages installed: `dpkg -l | grep cudnn`
- [ ] Libraries visible to system: `ldconfig -p | grep cudnn`
- [ ] Transcriber health endpoint works: `curl http://localhost:5000/healthz`
- [ ] Transcriber accepts upload: Test via browser at http://localhost:5000
- [ ] Transcriber processes audio: Check logs for successful transcription
- [ ] No worker crashes: `tail -20 /tmp/transcriber-gunicorn.log`
- [ ] ComfyUI starts: `cd ~/ComfyUI && ./venv/bin/python main.py`
- [ ] ComfyUI generates images: Test basic workflow
- [ ] No CUDA errors in ComfyUI console

## Expected Outcomes

### Success Indicators
- Transcriber workers no longer crash with cuDNN errors
- GPU-accelerated transcription works (faster than CPU)
- ComfyUI continues working normally
- System logs show cuDNN 9.x libraries loading successfully

### Performance Improvements
- cuDNN 9.x includes optimizations for RTX 40-series GPUs
- Faster inference times for transformer models (Whisper)
- Better memory utilization

## Emergency Contacts / Resources

- **NVIDIA cuDNN Documentation**: https://docs.nvidia.com/deeplearning/cudnn/
- **CTranslate2 Requirements**: https://github.com/OpenNMT/CTranslate2#requirements
- **PyTorch CUDA Compatibility**: https://pytorch.org/get-started/locally/

## Notes

- This upgrade is necessary because `ctranslate2 4.6.0` has a hard dependency on cuDNN 9.x
- **Cannot downgrade ctranslate2 alone**: `faster-whisper>=1.0` requires `ctranslate2>=4.0`, which requires cuDNN 9.x
- Downgrading to `faster-whisper<0.10` would work with cuDNN 8, but loses significant performance and features
- The upgrade path is well-tested; cuDNN maintains backward compatibility for most use cases
- PyTorch 2.x (used by ComfyUI) is designed to work with multiple cuDNN versions
- Ubuntu 24.04 repositories only have cuDNN 8.9.2 as of October 2025 - manual download required

## Helper Scripts Created

- **Installation script**: `/path/to/transcriber/docs/install-cudnn9.sh`
  - Automates the entire cuDNN 9 installation process
  - Includes safety checks and confirmations
  - Usage: Download cuDNN 9 .deb to ~/Downloads/, then run the script

## Verification Completed

- ✅ Ubuntu repositories confirmed to only have cuDNN 8.9.2
- ✅ ComfyUI uses PyTorch 2.5.1+cu121 (compatible with cuDNN 9.x)
- ✅ Backup files created: `cudnn-8-packages-backup.txt` and `cudnn-8-version-backup.txt`
- ✅ System currently running cuDNN 8.9.2 (stable state for other tools)
- ✅ Transcriber requires manual cuDNN 9 upgrade to function

## Created
October 2, 2025 @ 10:00 AM

## Last Updated
October 2, 2025 @ 10:45 AM - Added repository verification, helper script info, and downgrade limitations
