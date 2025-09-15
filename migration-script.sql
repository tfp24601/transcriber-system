-- Migration script to create transcriber schema and move existing data

-- Create the transcriber schema
CREATE SCHEMA IF NOT EXISTS transcriber;

-- Create the function in the transcriber schema first
CREATE OR REPLACE FUNCTION transcriber.get_or_create_user(user_email TEXT, user_display_name TEXT DEFAULT NULL)
RETURNS UUID AS $$
DECLARE
    user_uuid UUID;
BEGIN
    -- Try to find existing user
    SELECT id INTO user_uuid FROM transcriber.users WHERE email = user_email;
    
    -- If not found, create new user
    IF user_uuid IS NULL THEN
        INSERT INTO transcriber.users (email, display_name) 
        VALUES (user_email, COALESCE(user_display_name, split_part(user_email, '@', 1)))
        RETURNING id INTO user_uuid;
    END IF;
    
    RETURN user_uuid;
END;
$$ LANGUAGE plpgsql;

-- If you have existing tables in public schema, migrate them:
-- (Skip this section if you're starting fresh)

-- Check if public schema tables exist and migrate
DO $$
BEGIN
    -- Migrate users table if it exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users') THEN
        -- Create new table in transcriber schema
        CREATE TABLE transcriber.users AS SELECT * FROM public.users;
        -- Add constraints
        ALTER TABLE transcriber.users ADD CONSTRAINT users_pkey PRIMARY KEY (id);
        ALTER TABLE transcriber.users ADD CONSTRAINT users_email_key UNIQUE (email);
        -- Drop old table
        DROP TABLE public.users CASCADE;
    ELSE
        -- Create fresh users table
        CREATE TABLE transcriber.users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email TEXT UNIQUE NOT NULL,
            display_name TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    END IF;
    
    -- Migrate recordings table if it exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'recordings') THEN
        CREATE TABLE transcriber.recordings AS SELECT * FROM public.recordings;
        -- Add constraints
        ALTER TABLE transcriber.recordings ADD CONSTRAINT recordings_pkey PRIMARY KEY (id);
        ALTER TABLE transcriber.recordings ADD CONSTRAINT recordings_user_id_fkey 
            FOREIGN KEY (user_id) REFERENCES transcriber.users(id) ON DELETE CASCADE;
        DROP TABLE public.recordings CASCADE;
    ELSE
        -- Create fresh recordings table
        CREATE TABLE transcriber.recordings (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES transcriber.users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            mode TEXT NOT NULL CHECK (mode IN ('single', 'multi')),
            source TEXT DEFAULT 'unknown' CHECK (source IN ('web-desktop', 'android-bridge', 'ios-shortcut', 'unknown')),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            duration_seconds INTEGER,
            file_size_bytes BIGINT,
            original_filename TEXT,
            audio_path TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'done', 'failed')),
            error_message TEXT,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            language TEXT DEFAULT 'auto',
            model_used TEXT
        );
    END IF;
    
    -- Create transcripts table
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'transcriber' AND table_name = 'transcripts') THEN
        CREATE TABLE transcriber.transcripts (
            recording_id UUID PRIMARY KEY REFERENCES transcriber.recordings(id) ON DELETE CASCADE,
            text_path TEXT,
            vtt_path TEXT, 
            srt_path TEXT,
            words_json_path TEXT,
            diarization_json_path TEXT,
            speaker_count INTEGER,
            language_detected TEXT,
            confidence_score FLOAT,
            processing_time_seconds FLOAT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_recordings_user_id ON transcriber.recordings(user_id);
CREATE INDEX IF NOT EXISTS idx_recordings_status ON transcriber.recordings(status);
CREATE INDEX IF NOT EXISTS idx_recordings_created_at ON transcriber.recordings(created_at DESC);