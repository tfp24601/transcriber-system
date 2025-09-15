import React, { useState, useRef } from 'react'
import { FileUpload } from './components/FileUpload'
import { TranscriptDisplay } from './components/TranscriptDisplay'
import { RecordingHistory } from './components/RecordingHistory'
import { detectPlatform, formatTimestamp } from './utils/platform'
import { apiClient } from './utils/api'

export interface Recording {
  id: string;
  name: string;
  mode: 'single' | 'multi';
  created_at: string;
  duration_seconds?: number;
  status: 'queued' | 'processing' | 'done' | 'failed';
}

export interface TranscriptData {
  id: string;
  name: string;
  mode: 'single' | 'multi';
  created_at: string;
  duration_seconds?: number;
  status: string;
  transcript_text?: string;
  download_audio_url?: string;
  download_txt_url?: string;
  download_srt_url?: string;
  download_vtt_url?: string;
  diarization_json?: any;
}

function App() {
  const [selectedMode, setSelectedMode] = useState<'single' | 'multi'>('single')
  const [recordingName, setRecordingName] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [currentJob, setCurrentJob] = useState<string | null>(null)
  const [transcript, setTranscript] = useState<TranscriptData | null>(null)
  const [recordings, setRecordings] = useState<Recording[]>([])
  const [error, setError] = useState<string | null>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)
  const platform = detectPlatform()

  const handleModeSelect = (mode: 'single' | 'multi') => {
    setSelectedMode(mode)
    setError(null)
    
    if (platform === 'ios') {
      // iOS Shortcuts integration
      const defaultName = recordingName || formatTimestamp(new Date())
      const shortcutName = mode === 'single' ? 'Quick Dictate' : 'Quick Meeting'
      const returnURL = `${window.location.origin}/view?id=PLACEHOLDER`
      const errorURL = `${window.location.origin}/?error=shortcut_failed`
      
      window.location.href = `shortcuts://run-shortcut?name=${shortcutName}&x-success=${encodeURIComponent(returnURL)}&x-error=${encodeURIComponent(errorURL)}&name=${encodeURIComponent(defaultName)}&mode=${mode}`
      
    } else if (platform === 'android') {
      // Android deep link
      const defaultName = recordingName || formatTimestamp(new Date())
      const deepLink = `ssrec://${mode}?name=${encodeURIComponent(defaultName)}`
      
      try {
        window.location.href = deepLink
      } catch (e) {
        setError('Android Recorder Bridge app not installed. Please install the app first.')
      }
      
    } else {
      // Desktop - trigger file upload
      fileInputRef.current?.click()
    }
  }

  const handleFileUpload = async (file: File) => {
    if (!file) return

    const name = recordingName || formatTimestamp(new Date())
    setIsUploading(true)
    setError(null)
    
    try {
      const jobId = await apiClient.uploadFile(file, selectedMode, name)
      setCurrentJob(jobId)
      
      // Start polling for job status
      pollJobStatus(jobId)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setIsUploading(false)
    }
  }

  const pollJobStatus = async (jobId: string) => {
    const maxAttempts = 120 // 10 minutes max
    let attempts = 0

    const poll = async () => {
      try {
        const job = await apiClient.getJob(jobId)
        
        if (job.status === 'done') {
          const recording = await apiClient.getRecording(jobId)
          setTranscript(recording)
          setIsUploading(false)
          setCurrentJob(null)
          loadRecordings()
          
        } else if (job.status === 'failed') {
          setError('Transcription failed')
          setIsUploading(false)
          setCurrentJob(null)
          
        } else if (attempts < maxAttempts) {
          attempts++
          setTimeout(poll, 5000) // Poll every 5 seconds
          
        } else {
          setError('Transcription timed out')
          setIsUploading(false)
          setCurrentJob(null)
        }
        
      } catch (err) {
        if (attempts < maxAttempts) {
          attempts++
          setTimeout(poll, 5000)
        } else {
          setError('Failed to check transcription status')
          setIsUploading(false)
          setCurrentJob(null)
        }
      }
    }

    poll()
  }

  const loadRecordings = async () => {
    try {
      const recordingsList = await apiClient.getRecordings()
      setRecordings(recordingsList.items || [])
    } catch (err) {
      console.error('Failed to load recordings:', err)
    }
  }

  const handleRecordingSelect = async (recordingId: string) => {
    try {
      const recording = await apiClient.getRecording(recordingId)
      setTranscript(recording)
      setError(null)
    } catch (err) {
      setError('Failed to load recording')
    }
  }

  React.useEffect(() => {
    loadRecordings()
  }, [])

  const getPlatformInstructions = () => {
    switch (platform) {
      case 'ios':
        return 'Tap a button to launch recording via Shortcuts app'
      case 'android':
        return 'Tap a button to launch recording via Recorder Bridge app'
      default:
        return 'Click a button to select audio file for transcription'
    }
  }

  return (
    <div className="container">
      <header style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1>🎙️ Transcriber</h1>
        <p style={{ color: '#666', marginBottom: '1rem' }}>
          {getPlatformInstructions()}
        </p>
      </header>

      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>Recording Mode</h2>
        
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr', 
          gap: '1rem', 
          marginBottom: '1.5rem' 
        }}>
          <button
            className={`button primary ${selectedMode === 'single' ? 'selected' : ''}`}
            onClick={() => handleModeSelect('single')}
            disabled={isUploading}
            style={{
              backgroundColor: selectedMode === 'single' ? '#1e7e34' : undefined,
              fontSize: '18px',
              padding: '20px'
            }}
          >
            👤 Single Speaker
            <br />
            <small style={{ fontWeight: 'normal', opacity: 0.9 }}>
              Highest accuracy
            </small>
          </button>

          <button
            className={`button secondary ${selectedMode === 'multi' ? 'selected' : ''}`}
            onClick={() => handleModeSelect('multi')}
            disabled={isUploading}
            style={{
              backgroundColor: selectedMode === 'multi' ? '#117a8b' : undefined,
              fontSize: '18px',
              padding: '20px'
            }}
          >
            👥 Meeting/Multi
            <br />
            <small style={{ fontWeight: 'normal', opacity: 0.9 }}>
              Speaker identification
            </small>
          </button>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="recordingName" style={{ display: 'block', marginBottom: '0.5rem' }}>
            Name (optional):
          </label>
          <input
            id="recordingName"
            type="text"
            value={recordingName}
            onChange={(e) => setRecordingName(e.target.value)}
            placeholder={`Default: ${formatTimestamp(new Date())}`}
            disabled={isUploading}
            style={{
              width: '100%',
              padding: '12px',
              border: '1px solid #dee2e6',
              borderRadius: '6px',
              fontSize: '16px'
            }}
          />
        </div>

        {error && (
          <div className="status error">
            ⚠️ {error}
          </div>
        )}

        {isUploading && (
          <div className="status processing">
            🔄 {currentJob ? 'Transcribing audio...' : 'Uploading file...'}
          </div>
        )}
      </div>

      {platform === 'desktop' && (
        <FileUpload
          onFileUpload={handleFileUpload}
          isUploading={isUploading}
          ref={fileInputRef}
        />
      )}

      {transcript && (
        <TranscriptDisplay transcript={transcript} />
      )}

      <RecordingHistory 
        recordings={recordings}
        onRecordingSelect={handleRecordingSelect}
      />
    </div>
  )
}

export default App