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
  private devHeaders(): HeadersInit {
    // In dev mode, we'll use query parameters instead of headers
    // because Cloudflare strips client-supplied cf-* headers
    return {};
  }

  private addDevParams(url: string): string {
    // Dev mode identity via query parameter fallback
    // Remove when Cloudflare Access is configured
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}user_email=ben@solfamily.group`;
  }

  async uploadFile(file: File, mode: 'single' | 'multi', name: string): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode);
    formData.append('name', name);
    formData.append('source', 'web-desktop');

    const url = this.addDevParams('/ingest');
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      headers: this.devHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    const result = await response.json();
    return result.job_id;
  }

  async getRecordings(limit = 50): Promise<ApiRecordingsList> {
    const url = this.addDevParams(`/api/recordings?limit=${limit}`);
    const response = await fetch(url, {
      headers: this.devHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch recordings: ${response.statusText}`);
    }

    return response.json();
  }

  async getRecording(id: string): Promise<ApiRecordingDetail> {
    const url = this.addDevParams(`/api/recordings/${id}`);
    const response = await fetch(url, {
      headers: this.devHeaders(),
    });
    if (!response.ok) {
      throw new Error(`Failed to fetch recording: ${response.statusText}`);
    }

  const raw = await response.json();

    // Normalize keys between different backend variants
    const normalized: any = {
      id: raw.id || id,
      name: raw.name,
      mode: raw.mode,
      status: raw.status,
      created_at: raw.created_at || raw.createdAt,
      duration_seconds: raw.duration_seconds,
      // Prefer canonical download_* fields if present
      download_audio_url: raw.download_audio_url,
      download_txt_url: raw.download_txt_url || raw.textUrl,
      download_srt_url: raw.download_srt_url || raw.srtUrl,
      download_vtt_url: raw.download_vtt_url || raw.vttUrl,
      diarization_json: raw.diarization_json,
      language_detected: raw.language_detected,
      speaker_count: raw.speaker_count,
    };

    // Synthesize download URLs if missing but id is known
    const origin = window.location.origin;
    if (!normalized.download_audio_url && normalized.id) {
      normalized.download_audio_url = `${origin}/downloads/audio/${normalized.id}`;
    }
    if (!normalized.download_txt_url && normalized.id) {
      normalized.download_txt_url = `${origin}/downloads/txt/${normalized.id}`;
    }
    if (!normalized.download_srt_url && normalized.id) {
      normalized.download_srt_url = `${origin}/downloads/srt/${normalized.id}`;
    }
    if (!normalized.download_vtt_url && normalized.id) {
      normalized.download_vtt_url = `${origin}/downloads/vtt/${normalized.id}`;
    }

    // If transcript text is not inlined, try to fetch from provided URL
    if (!raw.transcript_text && normalized.download_txt_url) {
      try {
        const txtUrl = this.addDevParams(normalized.download_txt_url);
        const txtResp = await fetch(txtUrl, { headers: this.devHeaders() });
        if (txtResp.ok) {
          normalized.transcript_text = await txtResp.text();
        }
      } catch (e) {
        // Non-fatal: leave transcript_text undefined
      }
    } else {
      normalized.transcript_text = raw.transcript_text;
    }

    // Optionally fetch diarization JSON if only a URL variant is present
    if (!normalized.diarization_json && (raw.diarizationUrl || raw.diarization_json_url)) {
      const dUrl = raw.diarizationUrl || raw.diarization_json_url;
      try {
        const diarizationUrl = this.addDevParams(dUrl);
        const dResp = await fetch(diarizationUrl, { headers: this.devHeaders() });
        if (dResp.ok) {
          normalized.diarization_json = await dResp.json();
        }
      } catch (e) {
        // ignore
      }
    }

    return normalized as ApiRecordingDetail;
  }

  async getJob(id: string): Promise<ApiJob> {
    const url = this.addDevParams(`/api/jobs/${id}`);
    const response = await fetch(url, {
      headers: this.devHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch job status: ${response.statusText}`);
    }

    return response.json();
  }
}

export const apiClient = new ApiClient();