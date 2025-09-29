// Process transcription + diarization result for multi mode
const diarization = $input.first().json;
const transcription = $node["Multi Speaker Transcribe"].json;
const recordingId = $node["Parse Job Data"].json.recordingId;
const audioPath = $node["Parse Job Data"].json.audioPath;
const userId = audioPath.split('/')[3];

// Prepare file paths
const transcriptDir = `/data/transcripts/${userId}`;
const textPath = `${transcriptDir}/${recordingId}.txt`;
const vttPath = `${transcriptDir}/${recordingId}.vtt`;
const srtPath = `${transcriptDir}/${recordingId}.srt`;
const jsonPath = `${transcriptDir}/${recordingId}.json`;
const diarizationPath = `${transcriptDir}/${recordingId}_diarization.json`;

// Generate combined transcript with speaker labels
let transcriptText = '';
let vttContent = 'WEBVTT\n\n';
let srtContent = '';

if (diarization.segments) {
  diarization.segments.forEach((segment, index) => {
    const speaker = segment.speaker || 'Speaker';
    const text = segment.text || '';
    transcriptText += `${speaker}: ${text}\n\n`;
    
    const start = formatTime(segment.start);
    const end = formatTime(segment.end);
    
    // VTT format
    vttContent += `${index + 1}\n${start} --> ${end}\n${speaker}: ${text}\n\n`;
    
    // SRT format 
    const srtStart = formatSRTTime(segment.start);
    const srtEnd = formatSRTTime(segment.end);
    srtContent += `${index + 1}\n${srtStart} --> ${srtEnd}\n${speaker}: ${text}\n\n`;
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
  diarizationPath,
  transcriptText,
  vttContent,
  srtContent,
  jsonContent: JSON.stringify(transcription, null, 2),
  diarizationContent: JSON.stringify(diarization, null, 2),
  language: transcription.language || 'unknown',
  duration: transcription.duration || 0,
  speakerCount: diarization.num_speakers || 0,
  mode: 'multi',
  status: 'done',
  completed_at: new Date().toISOString(),
  processing_time_seconds: transcription.duration || 0
};