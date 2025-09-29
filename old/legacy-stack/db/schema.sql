-- Transcriber System Database Schema
-- PostgreSQL 16+ with UUID support

-- Enable UUID generation extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table - stores user information from Cloudflare Access
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recordings table - stores recording metadata and status
CREATE TABLE IF NOT EXISTS recordings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('single', 'multi')),
    source TEXT DEFAULT 'unknown' CHECK (source IN ('web-desktop', 'android-bridge', 'ios-shortcut', 'unknown')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- File and processing info
    duration_seconds INTEGER,
    file_size_bytes BIGINT,
    original_filename TEXT,
    audio_path TEXT NOT NULL,
    
    -- Processing status
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'done', 'failed')),
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Metadata
    language TEXT DEFAULT 'auto',
    model_used TEXT
);

-- Transcripts table - stores transcript outputs and file paths  
CREATE TABLE IF NOT EXISTS transcripts (
    recording_id UUID PRIMARY KEY REFERENCES recordings(id) ON DELETE CASCADE,
    
    -- Transcript files
    text_path TEXT,
    vtt_path TEXT, 
    srt_path TEXT,
    words_json_path TEXT,
    
    -- Multi-speaker diarization (for 'multi' mode)
    diarization_json_path TEXT,
    speaker_count INTEGER,
    
    -- Processing info
    language_detected TEXT,
    confidence_score FLOAT,
    processing_time_seconds FLOAT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs table - for tracking processing jobs and progress
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recording_id UUID NOT NULL REFERENCES recordings(id) ON DELETE CASCADE,
    job_type TEXT NOT NULL DEFAULT 'transcribe' CHECK (job_type IN ('transcribe', 'diarize')),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'done', 'failed')),
    progress FLOAT DEFAULT 0.0 CHECK (progress >= 0.0 AND progress <= 1.0),
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_recordings_user_id ON recordings(user_id);
CREATE INDEX IF NOT EXISTS idx_recordings_status ON recordings(status);
CREATE INDEX IF NOT EXISTS idx_recordings_created_at ON recordings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_recordings_user_created ON recordings(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_recording_id ON jobs(recording_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_recordings_updated_at ON recordings;
CREATE TRIGGER update_recordings_updated_at 
    BEFORE UPDATE ON recordings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_transcripts_updated_at ON transcripts;
CREATE TRIGGER update_transcripts_updated_at 
    BEFORE UPDATE ON transcripts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at 
    BEFORE UPDATE ON jobs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Helper function to get or create user by email (for n8n workflows)
CREATE OR REPLACE FUNCTION get_or_create_user(user_email TEXT, user_display_name TEXT DEFAULT NULL)
RETURNS UUID AS $$
DECLARE
    user_uuid UUID;
BEGIN
    -- Try to find existing user
    SELECT id INTO user_uuid FROM users WHERE email = user_email;
    
    -- If not found, create new user
    IF user_uuid IS NULL THEN
        INSERT INTO users (email, display_name) 
        VALUES (user_email, COALESCE(user_display_name, split_part(user_email, '@', 1)))
        RETURNING id INTO user_uuid;
    END IF;
    
    RETURN user_uuid;
END;
$$ LANGUAGE plpgsql;

-- Storage cleanup function (for maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_recordings(days_to_keep INTEGER DEFAULT 90)
RETURNS TABLE (
    deleted_recordings INTEGER,
    deleted_transcripts INTEGER
) AS $$
DECLARE 
    rec_count INTEGER := 0;
    trans_count INTEGER := 0;
BEGIN
    -- Delete old transcripts first (cascade will handle it, but being explicit)
    DELETE FROM transcripts 
    WHERE recording_id IN (
        SELECT id FROM recordings 
        WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep
    );
    GET DIAGNOSTICS trans_count = ROW_COUNT;
    
    -- Delete old recordings
    DELETE FROM recordings 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    GET DIAGNOSTICS rec_count = ROW_COUNT;
    
    RETURN QUERY SELECT rec_count, trans_count;
END;
$$ LANGUAGE plpgsql;

-- Usage quota view (for future user management)
CREATE OR REPLACE VIEW user_storage_stats AS
SELECT 
    u.id,
    u.email,
    u.display_name,
    COUNT(r.id) as total_recordings,
    COUNT(CASE WHEN r.status = 'done' THEN 1 END) as completed_recordings,
    COUNT(CASE WHEN r.created_at > NOW() - INTERVAL '30 days' THEN 1 END) as recordings_last_30_days,
    COALESCE(SUM(r.file_size_bytes), 0) as total_storage_bytes,
    COALESCE(AVG(r.duration_seconds), 0) as avg_duration_seconds,
    MAX(r.created_at) as last_recording_at
FROM users u
LEFT JOIN recordings r ON u.id = r.user_id
GROUP BY u.id, u.email, u.display_name
ORDER BY total_recordings DESC;