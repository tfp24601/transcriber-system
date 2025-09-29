import { useState } from 'react'
import { Recording } from '../App'
import { formatDate, formatDuration } from '../utils/platform'

interface RecordingHistoryProps {
  recordings: Recording[];
  onRecordingSelect: (recordingId: string) => void;
}

export function RecordingHistory({ recordings, onRecordingSelect }: RecordingHistoryProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (recordings.length === 0) {
    return (
      <div className="card">
        <h3>Recording History</h3>
        <p style={{ color: '#666', textAlign: 'center', padding: '2rem 0' }}>
          No recordings yet. Upload an audio file or record using your device to get started.
        </p>
      </div>
    );
  }

  const displayedRecordings = isExpanded ? recordings : recordings.slice(0, 5);

  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'queued':
        return { text: 'Queued', color: '#ffc107', icon: '⏳' };
      case 'processing':
        return { text: 'Processing', color: '#17a2b8', icon: '🔄' };
      case 'done':
        return { text: 'Complete', color: '#28a745', icon: '✅' };
      case 'failed':
        return { text: 'Failed', color: '#dc3545', icon: '❌' };
      default:
        return { text: status, color: '#6c757d', icon: '❓' };
    }
  };

  return (
    <div className="card">
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '1rem'
      }}>
        <h3>Recording History</h3>
        {recordings.length > 5 && (
          <button
            className="button"
            onClick={() => setIsExpanded(!isExpanded)}
            style={{ fontSize: '14px', padding: '6px 12px' }}
          >
            {isExpanded ? 'Show Less' : `Show All (${recordings.length})`}
          </button>
        )}
      </div>

      <div style={{ display: 'grid', gap: '12px' }}>
        {displayedRecordings.map((recording) => {
          const status = getStatusDisplay(recording.status);
          
          return (
            <div
              key={recording.id}
              onClick={() => recording.status === 'done' && onRecordingSelect(recording.id)}
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr auto auto',
                alignItems: 'center',
                gap: '16px',
                padding: '12px',
                border: '1px solid #dee2e6',
                borderRadius: '8px',
                backgroundColor: recording.status === 'done' ? '#f8f9fa' : '#fff',
                cursor: recording.status === 'done' ? 'pointer' : 'default',
                transition: 'all 0.2s'
              }}
              onMouseOver={(e) => {
                if (recording.status === 'done') {
                  e.currentTarget.style.backgroundColor = '#e9ecef';
                }
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = recording.status === 'done' ? '#f8f9fa' : '#fff';
              }}
            >
              <div>
                <div style={{ fontWeight: '500', marginBottom: '4px' }}>
                  {recording.mode === 'single' ? '👤' : '👥'} {recording.name}
                </div>
                <div style={{ fontSize: '14px', color: '#666' }}>
                  {formatDate(recording.created_at)}
                  {recording.duration_seconds && ` • ${formatDuration(recording.duration_seconds)}`}
                </div>
              </div>
              
              <div style={{ 
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '14px',
                color: status.color
              }}>
                <span>{status.icon}</span>
                <span>{status.text}</span>
              </div>

              {recording.status === 'done' && (
                <div style={{ fontSize: '12px', color: '#666' }}>
                  Click to view →
                </div>
              )}
            </div>
          );
        })}
      </div>

      {recordings.length > 5 && !isExpanded && (
        <div style={{ 
          textAlign: 'center', 
          marginTop: '1rem',
          fontSize: '14px',
          color: '#666'
        }}>
          Showing 5 of {recordings.length} recordings
        </div>
      )}
    </div>
  );
}