import { TranscriptData } from '../App'
import { formatDate, formatDuration } from '../utils/platform'

interface TranscriptDisplayProps {
  transcript: TranscriptData;
}

export function TranscriptDisplay({ transcript }: TranscriptDisplayProps) {
  const copyToClipboard = () => {
    if (transcript.transcript_text) {
      navigator.clipboard.writeText(transcript.transcript_text)
        .then(() => {
          // Could add a toast notification here
          console.log('Copied to clipboard');
        })
        .catch(err => {
          console.error('Failed to copy:', err);
        });
    }
  };

  const downloadText = () => {
    if (transcript.transcript_text) {
      const blob = new Blob([transcript.transcript_text], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${transcript.name}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="card">
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'flex-start',
        marginBottom: '1rem'
      }}>
        <div>
          <h3>{transcript.name}</h3>
          <div style={{ fontSize: '14px', color: '#666', marginTop: '4px' }}>
            {transcript.mode === 'single' ? '👤 Single Speaker' : '👥 Meeting'} • 
            {formatDate(transcript.created_at)} • 
            {formatDuration(transcript.duration_seconds)}
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button 
            className="button"
            onClick={copyToClipboard}
            style={{ fontSize: '14px', padding: '8px 12px' }}
          >
            📋 Copy
          </button>
          <button 
            className="button"
            onClick={downloadText}
            style={{ fontSize: '14px', padding: '8px 12px' }}
          >
            💾 Download
          </button>
        </div>
      </div>

      {transcript.transcript_text ? (
        <div className="transcript">
          {transcript.transcript_text}
        </div>
      ) : (
        <div className="status processing">
          Transcript not yet available...
        </div>
      )}

      {transcript.download_audio_url && (
        <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #dee2e6' }}>
          <h4 style={{ marginBottom: '8px' }}>Downloads</h4>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <a 
              href={transcript.download_audio_url}
              className="button"
              style={{ 
                textDecoration: 'none', 
                fontSize: '14px', 
                padding: '6px 12px',
                display: 'inline-block'
              }}
            >
              🎵 Audio
            </a>
            {transcript.download_txt_url && (
              <a 
                href={transcript.download_txt_url}
                className="button"
                style={{ 
                  textDecoration: 'none', 
                  fontSize: '14px', 
                  padding: '6px 12px',
                  display: 'inline-block'
                }}
              >
                📄 TXT
              </a>
            )}
            {transcript.download_srt_url && (
              <a 
                href={transcript.download_srt_url}
                className="button"
                style={{ 
                  textDecoration: 'none', 
                  fontSize: '14px', 
                  padding: '6px 12px',
                  display: 'inline-block'
                }}
              >
                🎬 SRT
              </a>
            )}
            {transcript.download_vtt_url && (
              <a 
                href={transcript.download_vtt_url}
                className="button"
                style={{ 
                  textDecoration: 'none', 
                  fontSize: '14px', 
                  padding: '6px 12px',
                  display: 'inline-block'
                }}
              >
                📹 VTT
              </a>
            )}
          </div>
        </div>
      )}

      {transcript.diarization_json && transcript.diarization_json.segments && (
        <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #dee2e6' }}>
          <h4 style={{ marginBottom: '8px' }}>Speaker Timeline</h4>
          <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
            {transcript.diarization_json.segments.map((segment: any, index: number) => (
              <div key={index} style={{ 
                marginBottom: '8px', 
                padding: '8px', 
                backgroundColor: '#f8f9fa',
                borderRadius: '4px',
                fontSize: '14px'
              }}>
                <strong>Speaker {segment.speaker}</strong> 
                <span style={{ color: '#666', marginLeft: '8px' }}>
                  {Math.floor(segment.start / 60)}:{(segment.start % 60).toFixed(1).padStart(4, '0')} - 
                  {Math.floor(segment.end / 60)}:{(segment.end % 60).toFixed(1).padStart(4, '0')}
                </span>
                <div style={{ marginTop: '4px' }}>
                  {segment.text}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}