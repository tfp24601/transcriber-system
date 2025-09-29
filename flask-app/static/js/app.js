(() => {
  const configScript = document.getElementById("transcriber-config");
  const fallbackConfig = {
    languages: [["auto", "Automatic"]],
    defaultLanguage: "auto",
    defaultBeamSize: 5,
    defaultTemperature: 0.0,
    modelName: "small",
    availableModels: ["small"],
    defaultUseGpu: true,
    diagnosticNotes: [],
    gpuSupported: true,
  };

  let config = fallbackConfig;
  if (configScript) {
    try {
      const parsed = JSON.parse(configScript.textContent || "{}");
      config = { ...fallbackConfig, ...parsed };
    } catch (error) {
      console.warn("Failed to parse embedded config, falling back to defaults", error);
    }
  }

  const fileInput = document.getElementById("audio-file");
  const recordBtn = document.getElementById("record-btn");
  const stopBtn = document.getElementById("stop-btn");
  const recordingIndicator = document.getElementById("recording-indicator");
  const playback = document.getElementById("playback");
  const form = document.getElementById("upload-form");
  const modelSelect = document.getElementById("model");
  const languageSelect = document.getElementById("language");
  const translateCheckbox = document.getElementById("translate");
  const useGpuCheckbox = document.getElementById("use-gpu");
  const temperatureInput = document.getElementById("temperature");
  const beamSizeInput = document.getElementById("beam-size");
  const statusSection = document.getElementById("status");
  const statusMessage = document.getElementById("status-message");
  const resultsSection = document.getElementById("results");
  const transcriptOutput = document.getElementById("transcript-output");
  const metadataContainer = document.getElementById("metadata");
  const downloadText = document.getElementById("download-text");
  const downloadSrt = document.getElementById("download-srt");
  const diagnosticSection = document.getElementById("diagnostics");
  const diagnosticList = document.getElementById("diagnostic-list");
  const gpuStatus = document.getElementById("gpu-status");

  let mediaRecorder = null;
  let recordedChunks = [];
  let recordedBlob = null;

  function populateModels() {
    if (!modelSelect) return;
    modelSelect.innerHTML = "";
    for (const model of config.availableModels || []) {
      const option = document.createElement("option");
      option.value = model;
      option.textContent = model;
      if (model === config.modelName) {
        option.selected = true;
      }
      modelSelect.appendChild(option);
    }
  }

  function populateLanguages() {
    languageSelect.innerHTML = "";
    for (const [value, label] of config.languages) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      if (value === config.defaultLanguage) {
        option.selected = true;
      }
      languageSelect.appendChild(option);
    }
  }

  function resetRecording() {
    recordedBlob = null;
    recordedChunks = [];
    playback.classList.add("hidden");
    playback.src = "";
    stopBtn.disabled = true;
    recordBtn.disabled = false;
    recordingIndicator.classList.add("hidden");
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recordedChunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunks.push(event.data);
        }
      };
      mediaRecorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        recordedBlob = new Blob(recordedChunks, { type: "audio/webm" });
        playback.src = URL.createObjectURL(recordedBlob);
        playback.classList.remove("hidden");
      };
      mediaRecorder.start();
      recordBtn.disabled = true;
      stopBtn.disabled = false;
      recordingIndicator.classList.remove("hidden");
    } catch (error) {
      console.error("Unable to start recording", error);
      alert("Failed to access microphone. Please allow microphone permissions.");
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    recordBtn.disabled = false;
    stopBtn.disabled = true;
    recordingIndicator.classList.add("hidden");
  }

  function setStatus(message, show = true) {
    statusMessage.textContent = message;
    statusSection.classList.toggle("hidden", !show);
  }

  function showError(message) {
    setStatus(message, true);
    statusSection.classList.add("error");
  }

  function populateDiagnostics(notes) {
    if (!diagnosticSection || !diagnosticList) return;
    const messages = Array.isArray(notes) ? notes.filter(Boolean) : [];
    if (!messages.length) {
      diagnosticList.innerHTML = "";
      diagnosticSection.classList.add("hidden");
      return;
    }

    diagnosticList.innerHTML = "";
    for (const note of messages) {
      const li = document.createElement("li");
      li.textContent = note;
      diagnosticList.appendChild(li);
    }
    diagnosticSection.classList.remove("hidden");
  }

  function applyGpuAvailability() {
    if (!useGpuCheckbox) return;
    if (config.gpuSupported) {
      useGpuCheckbox.disabled = false;
      if (gpuStatus) {
        gpuStatus.textContent = "";
        gpuStatus.classList.add("hidden");
      }
      return;
    }

    useGpuCheckbox.checked = false;
    useGpuCheckbox.disabled = true;
    if (gpuStatus) {
      gpuStatus.textContent = "Unavailable: GPU requirements missing, running on CPU.";
      gpuStatus.classList.remove("hidden");
    }
  }

  async function submitForm(event) {
    event.preventDefault();
    statusSection.classList.remove("error");
    setStatus("Uploading audio…", true);
    resultsSection.classList.add("hidden");

    const formData = new FormData();
    const file = fileInput.files[0];

    if (recordedBlob) {
      formData.append("audio", recordedBlob, "recording.webm");
    } else if (file) {
      formData.append("audio", file, file.name);
    } else {
      showError("Please upload a file or record audio first.");
      return;
    }

    formData.append("model", (modelSelect && modelSelect.value) || config.modelName);
    formData.append("language", languageSelect.value || "auto");
    formData.append("translate", String(translateCheckbox.checked));
    formData.append("temperature", temperatureInput.value || config.defaultTemperature);
    formData.append("beam_size", beamSizeInput.value || config.defaultBeamSize);
    formData.append(
      "use_gpu",
      useGpuCheckbox ? String(useGpuCheckbox.checked) : String(config.defaultUseGpu)
    );

    try {
      const response = await fetch("/transcribe", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || response.statusText);
      }

      const payload = await response.json();
      transcriptOutput.value = payload.transcript || "";
      populateMetadata(payload.metadata || {});

      if (payload.downloads) {
        downloadText.href = payload.downloads.text;
        downloadSrt.href = payload.downloads.srt;
      }

      resultsSection.classList.remove("hidden");
      setStatus("Transcription complete!", true);
    } catch (error) {
      console.error(error);
      showError(`Transcription failed: ${error.message}`);
    }
  }

  function populateMetadata(metadata) {
    metadataContainer.innerHTML = "";
    const entries = Object.entries(metadata);

    if (!entries.length) {
      metadataContainer.textContent = "No metadata returned.";
      return;
    }

    for (const [key, value] of entries) {
      const item = document.createElement("div");
      item.innerHTML = `<strong>${key}</strong><br />${value ?? "—"}`;
      metadataContainer.appendChild(item);
    }
  }

  function init() {
    populateModels();
    populateLanguages();
    temperatureInput.value = config.defaultTemperature;
    beamSizeInput.value = config.defaultBeamSize;
    if (useGpuCheckbox) {
      useGpuCheckbox.checked = Boolean(config.defaultUseGpu);
    }

    populateDiagnostics(config.diagnosticNotes);
    applyGpuAvailability();

    recordBtn.addEventListener("click", startRecording);
    stopBtn.addEventListener("click", stopRecording);
    form.addEventListener("submit", submitForm);
    fileInput.addEventListener("change", () => {
      resetRecording();
      if (fileInput.files.length) {
        playback.src = URL.createObjectURL(fileInput.files[0]);
        playback.classList.remove("hidden");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
