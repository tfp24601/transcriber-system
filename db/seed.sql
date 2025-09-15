-- Seed data for development and testing
-- This file creates sample data for development/testing purposes

-- Insert a test user (replace with your actual email for testing)
INSERT INTO users (email, display_name) 
VALUES ('test@solfamily.group', 'Test User')
ON CONFLICT (email) DO NOTHING;

-- You can add more test users here as needed
-- INSERT INTO users (email, display_name) 
-- VALUES ('another@solfamily.group', 'Another User')
-- ON CONFLICT (email) DO NOTHING;

-- Sample recordings for testing (optional)
-- These will only be inserted in development environments
DO $$
DECLARE
    test_user_id UUID;
BEGIN
    -- Get the test user ID
    SELECT id INTO test_user_id FROM users WHERE email = 'test@solfamily.group';
    
    IF test_user_id IS NOT NULL THEN
        -- Sample completed recording
        INSERT INTO recordings (
            user_id, name, mode, source, status, 
            duration_seconds, audio_path, completed_at,
            language, model_used
        ) VALUES (
            test_user_id, 'sample_meeting_20250909120000', 'multi', 'web-desktop', 'done',
            1800, '/data/audio/' || test_user_id || '/sample_meeting.wav', NOW() - INTERVAL '1 hour',
            'en', 'large-v3'
        ) ON CONFLICT DO NOTHING;
        
        -- Sample processing recording
        INSERT INTO recordings (
            user_id, name, mode, source, status,
            duration_seconds, audio_path, started_at
        ) VALUES (
            test_user_id, 'sample_dictation_20250909130000', 'single', 'ios-shortcut', 'processing', 
            300, '/data/audio/' || test_user_id || '/sample_dictation.wav', NOW() - INTERVAL '5 minutes'
        ) ON CONFLICT DO NOTHING;
    END IF;
END $$;