// Process transcription result for single mode
const transcription = $input.first().json;
const recordingId = $node["Parse Job Data"].json.recordingId;
const audioPath = $node["Parse Job Data"].json.audioPath;
const userId = audioPath.split('/')[3]; // Extract from path

// Prepare file paths
const transcriptDir = `/data/transcripts/${userId}`;
const textPath = `${transcriptDir}/${recordingId}.txt`;
const vttPath = `${transcriptDir}/${recordingId}.vtt`;
const srtPath = `${transcriptDir}/${recordingId}.srt`;
const jsonPath = `${transcriptDir}/${recordingId}.json`;

// Extract text and metadata
const transcriptText = transcription.text || '';
const language = transcription.language || 'unknown';
const duration = transcription.duration || 0;

// Generate VTT format
let vttContent = 'WEBVTT\n\n';
if (transcription.segments) {
  transcription.segments.forEach((segment, index) => {
    const start = formatTime(segment.start);
    const end = formatTime(segment.end);
    vttContent += `${index + 1}\n${start} --> ${end}\n${segment.text.trim()}\n\n`;
  });
}

// Generate SRT format
let srtContent = '';
if (transcription.segments) {
  transcription.segments.forEach((segment, index) => {
    const start = formatSRTTime(segment.start);
    const end = formatSRTTime(segment.end);
    srtContent += `${index + 1}\n${start} --> ${end}\n${segment.text.trim()}\n\n`;
  });
}

function formatTime(seconds) {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = (seconds % 60).toFixed(3);
  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.padStart(6, '0')}`;
}

function formatSRTTime(seconds) {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = (seconds % 60).toFixed(3).replace('.', ',');
  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.padStart(6, '0')}`;
}

return {
  recordingId,
  userId,
  transcriptDir,
  textPath,
  vttPath,
  srtPath,
  jsonPath,
  transcriptText,
  vttContent,
  srtContent,
  jsonContent: JSON.stringify(transcription, null, 2),
  language,
  duration,
  mode: 'single',
  status: 'done',
  completed_at: new Date().toISOString(),
  processing_time_seconds: duration
};