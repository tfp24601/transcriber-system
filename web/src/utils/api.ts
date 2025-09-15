export interface ApiRecording {
  id: string;
  name: string;
  mode: 'single' | 'multi';
  created_at: string;
  duration_seconds?: number;
  status: 'queued' | 'processing' | 'done' | 'failed';
}

export interface ApiRecordingDetail extends ApiRecording {
  transcript_text?: string;
  download_audio_url?: string;
  download_txt_url?: string;
  download_srt_url?: string;
  download_vtt_url?: string;
  diarization_json?: any;
}

export interface ApiRecordingsList {
  items: ApiRecording[];
}

export interface ApiJob {
  id: string;
  status: 'queued' | 'processing' | 'done' | 'failed';
  progress?: number;
}

class ApiClient {

  async uploadFile(file: File, mode: 'single' | 'multi', name: string): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode);
    formData.append('name', name);
    formData.append('source', 'web-desktop');

    const response = await fetch('/ingest', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    const result = await response.json();
    return result.job_id;
  }

  async getRecordings(limit = 50): Promise<ApiRecordingsList> {
    const response = await fetch(`/api/recordings?limit=${limit}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch recordings: ${response.statusText}`);
    }

    return response.json();
  }

  async getRecording(id: string): Promise<ApiRecordingDetail> {
    const response = await fetch(`/api/recordings/${id}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch recording: ${response.statusText}`);
    }

    return response.json();
  }

  async getJob(id: string): Promise<ApiJob> {
    const response = await fetch(`/api/jobs/${id}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch job status: ${response.statusText}`);
    }

    return response.json();
  }
}

export const apiClient = new ApiClient();