import React, { useState } from 'react'

interface FileUploadProps {
  onFileUpload: (file: File) => void;
  isUploading: boolean;
}

export const FileUpload = React.forwardRef<HTMLInputElement, FileUploadProps>(
  ({ onFileUpload, isUploading }, ref) => {
    const [isDragOver, setIsDragOver] = useState(false);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file) {
        onFileUpload(file);
      }
    };

    const handleDragOver = (event: React.DragEvent) => {
      event.preventDefault();
      setIsDragOver(true);
    };

    const handleDragLeave = (event: React.DragEvent) => {
      event.preventDefault();
      setIsDragOver(false);
    };

    const handleDrop = (event: React.DragEvent) => {
      event.preventDefault();
      setIsDragOver(false);
      
      const file = event.dataTransfer.files[0];
      if (file) {
        onFileUpload(file);
      }
    };

    const handleClick = () => {
      if (ref && 'current' in ref && ref.current) {
        ref.current.click();
      }
    };

    return (
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Upload Audio File</h3>
        
        <input
          ref={ref}
          type="file"
          accept="audio/*,.wav,.mp3,.m4a,.flac,.ogg,.opus"
          onChange={handleFileChange}
          style={{ display: 'none' }}
          disabled={isUploading}
        />
        
        <div
          className={`upload-area ${isDragOver ? 'dragover' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClick}
          style={{
            cursor: isUploading ? 'not-allowed' : 'pointer',
            opacity: isUploading ? 0.6 : 1
          }}
        >
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>
            📁
          </div>
          
          <h4 style={{ marginBottom: '8px' }}>
            {isUploading ? 'Uploading...' : 'Drop audio file here or click to select'}
          </h4>
          
          <p style={{ color: '#666', fontSize: '14px' }}>
            Supports: WAV, MP3, M4A, FLAC, OGG, OPUS
          </p>
        </div>
      </div>
    );
  }
);