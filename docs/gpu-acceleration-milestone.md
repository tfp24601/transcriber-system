# GPU Acceleration Milestone (September 2025)

This document captures the work completed to bring the transcriber system's Flask preview app fully online with GPU acceleration. It summarizes the environment, configuration changes, validation steps, and next opportunities for improvement.

---

## 🎯 Goal

Enable reliable Faster-Whisper inference on the Sol workstation's RTX 4090, using cuDNN-backed CUDA kernels inside the local Flask app while keeping fallbacks to CPU mode available.

---

## 🖥 Current Environment

| Component | Version / Notes |
| --- | --- |
| Host OS | Ubuntu 24.04 |
| GPU | NVIDIA RTX 4090 |
| NVIDIA Driver | 550.163.01 (CUDA 12.4 compatible) |
| Python | 3.12.3 inside `flask-app/.venv` |
| Faster-Whisper | Installed via `requirements.txt` |
| cuDNN | 9.1.1.17 (installed via `pip install nvidia-cudnn-cu12`) |
| cuBLAS | 12.9.1.4 (pulled in automatically with cuDNN) |
| Flask App Location | `/path/to/transcriber/flask-app` |
| Log File | `/tmp/transcriber-flask.log` |

---

## 🔧 What Changed

1. **cuDNN 9 runtime installed**
    - Added NVIDIA's cuDNN 9.1 wheels to the Flask virtual environment:

       ```bash
       cd /path/to/transcriber/flask-app
       .venv/bin/python -m pip install nvidia-cudnn-cu12==9.1.1.17
       ```

    - Automatically pulled in matching `nvidia-cublas-cu12` runtime to satisfy ONNX runtime dependencies.

2. **cuDNN detection broadened** (`app.py`)
   - `_cudnn_libraries_present()` now scans:
     - System library paths (`/lib/x86_64-linux-gnu`, `/usr/lib64`, etc.)
     - `LD_LIBRARY_PATH`
     - Conda prefixes (if active)
     - Python site-packages directories such as `.venv/lib/python3.12/site-packages/nvidia/cudnn/lib`
     - Optional `CUDNN_EXTRA_LIB_DIRS` environment variable
   - Ensures the Flask diagnostics correctly report GPU readiness even when cuDNN lives only inside a virtual environment.

3. **Startup command standardised**
   - Flask app launched with `nohup` so it keeps running after the terminal closes.
   - `LD_LIBRARY_PATH` now explicitly includes the cuDNN directory before launching the app.
   - GPU-oriented environment variables exported to guarantee CUDA execution.

4. **Validation workflow scripted**
   - Added step-by-step commands to generate a test tone, invoke `/transcribe`, and confirm `"gpu_used": true` in the response.

---

## 🚀 How to Start the Flask App

From the Flask app directory:

```bash
cd /path/to/transcriber/flask-app
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
   TRANSCRIPTION_OUTPUT_DIR="$PWD/transcriptions" \
   PATH="$PWD/.venv/bin:$PATH" \
   "$PWD/.venv/bin/python" app.py >/tmp/transcriber-flask.log 2>&1 &
```

- Output is written to `/tmp/transcriber-flask.log`.
- Stop the app with `pkill -f "flask-app/.venv/bin/python app.py"` when needed.

---

## ✅ How to Test GPU Transcription

1. **Confirm the server is listening**
   ```bash
   tail -n 5 /tmp/transcriber-flask.log
   ```
   You should see `Running on http://127.0.0.1:5000`.

2. **Generate a 1-second test tone**
   ```bash
   python3 - <<'PY'
   import wave, struct, math
   framerate = 16000
   amplitude = 16000
   seconds = 1
   frequency = 440
   with wave.open("/tmp/test-tone.wav", "w") as wav_file:
      wav_file.setnchannels(1)
      wav_file.setsampwidth(2)
      wav_file.setframerate(framerate)
      for i in range(int(framerate * seconds)):
         value = int(amplitude * math.sin(2 * math.pi * frequency * (i / framerate)))
         wav_file.writeframes(struct.pack("<h", value))
   PY
   ```

3. **Run a transcription request**
    ```bash
    curl -s -X POST http://127.0.0.1:5000/transcribe \
       -F "audio=@/tmp/test-tone.wav" \
       -F "use_gpu=true" \
       -F "model=small" \
       -F "language=auto"
    ```

4. **Check for GPU usage in the response**
    - A successful result includes:

       ```json
       "device": "cuda",
       "gpu_used": true,
       "compute_type": "float16"
       ```
   - Log file shows `"POST /transcribe HTTP/1.1" 200 -` with no cuDNN errors.

---

## 📌 Known Limitations

- Flask app still uses the built-in development server (not production-grade WSGI).
- Startup currently relies on the manual `nohup` command; service automation (systemd or supervisor) is a future enhancement.
- Diagnostics only cover the Flask preview app. Dockerized components (ASR gateway, WhisperX worker) still rely on their own container configurations.

---

## ↗️ Next Improvements

1. **Service Automation**
   - Create a systemd service unit that exports the required environment variables and manages the Flask process.

2. **Monitoring & Alerts**
   - Tail logs or add health checks that verify `gpu_used` remains true.

3. **Documentation Integration**
   - Link this milestone doc from the main `README.md` and, if desired, incorporate testing steps into `/docs/INFRASTRUCTURE.md`.

4. **Performance Profiling**
   - Benchmark different model sizes and compute types to document throughput and latency on the RTX 4090.

---

## 🗂 Related Files

- `flask-app/app.py`: cuDNN detection and transcription logic
- `flask-app/requirements.txt`: Python dependencies
- `/tmp/transcriber-flask.log`: Runtime log for the preview server
- `infra/integrate-services.yml`: Docker services for the production stack

---

## ✅ Summary

- GPU inference now runs reliably with cuDNN 9 and float16 compute.
- Operators have straightforward commands to start, stop, and verify the Flask preview app.
- Documentation of the milestone ensures future contributors understand the configuration baseline before further enhancements.
