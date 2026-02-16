-- ============================================================================
-- ConvoBridge Database Schema for Supabase
-- ============================================================================
-- This file contains all the SQL statements needed to create the database
-- tables for tracking user sessions, topics, conversation turns, and progress.
-- ============================================================================

-- ============================================================================
-- Table: users
-- ============================================================================
-- Stores basic user information
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_name ON users(name);

-- ============================================================================
-- Table: sessions
-- ============================================================================
-- Tracks each login session (from login to logout)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at);

-- ============================================================================
-- Table: session_topics
-- ============================================================================
-- Tracks which topics were discussed in each session
-- Allows multiple topics per session and tracks turn count per topic
-- ============================================================================
CREATE TABLE IF NOT EXISTS session_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    topic_name TEXT NOT NULL, -- e.g., 'Gaming', 'Weekend plans', 'Hobbies', 'Food', 'YouTube'
    turn_count INTEGER NOT NULL DEFAULT 0, -- Number of conversation turns on this topic
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, topic_name) -- One topic per session (can be changed if needed)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_session_topics_session_id ON session_topics(session_id);
CREATE INDEX IF NOT EXISTS idx_session_topics_topic_name ON session_topics(topic_name);

-- ============================================================================
-- Table: conversation_turns
-- ============================================================================
-- Tracks individual conversation turns within a topic in a session
-- Each turn represents one question-answer exchange
-- ============================================================================
CREATE TABLE IF NOT EXISTS conversation_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_topic_id UUID NOT NULL REFERENCES session_topics(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL, -- Sequential turn number within the topic
    dimension TEXT NOT NULL, -- e.g., 'Basic Preferences', 'Social Context', 'Emotional', etc.
    difficulty_level INTEGER NOT NULL DEFAULT 1, -- Level 1, 2, 3, etc.
    
    -- Question details
    question TEXT NOT NULL,
    
    -- User response details
    user_response TEXT, -- The actual response the user gave (transcript or selected option)
    response_type TEXT CHECK (response_type IN ('selected_option', 'custom_speech', 'custom_text')),
    selected_option_index INTEGER, -- If user selected a pre-generated option (0, 1, or 2)
    
    -- Speech analysis results (if speech was analyzed)
    transcript TEXT, -- Transcribed speech
    clarity_score DECIMAL(3, 2), -- 0.00 to 1.00 (converted from 0-100)
    wer_estimate DECIMAL(3, 2), -- Word Error Rate estimate (0.00 to 1.00)
    pace_wpm INTEGER, -- Words per minute
    filler_words TEXT[], -- Array of filler words found
    
    -- Feedback and analysis
    feedback TEXT, -- Encouraging feedback from speech analysis
    strengths TEXT[], -- Array of strengths identified
    suggestions TEXT[], -- Array of suggestions for improvement
    
    -- Timestamps
    question_asked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_received_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_conversation_turns_session_topic_id ON conversation_turns(session_topic_id);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_turn_number ON conversation_turns(session_topic_id, turn_number);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_dimension ON conversation_turns(dimension);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_difficulty_level ON conversation_turns(difficulty_level);

-- ============================================================================
-- Table: response_options
-- ============================================================================
-- Stores the response options generated for each conversation turn
-- This allows tracking what options were presented to the user
-- ============================================================================
CREATE TABLE IF NOT EXISTS response_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_turn_id UUID NOT NULL REFERENCES conversation_turns(id) ON DELETE CASCADE,
    option_index INTEGER NOT NULL CHECK (option_index IN (0, 1, 2)), -- 0, 1, or 2
    option_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_response_options_conversation_turn_id ON response_options(conversation_turn_id);

-- ============================================================================
-- Table: vocabulary_words
-- ============================================================================
-- Stores vocabulary words shown during conversation turns
-- ============================================================================
CREATE TABLE IF NOT EXISTS vocabulary_words (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_turn_id UUID NOT NULL REFERENCES conversation_turns(id) ON DELETE CASCADE,
    word TEXT NOT NULL,
    word_type TEXT, -- e.g., 'noun', 'verb', 'adjective'
    definition TEXT NOT NULL,
    example TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_vocabulary_words_conversation_turn_id ON vocabulary_words(conversation_turn_id);
CREATE INDEX IF NOT EXISTS idx_vocabulary_words_word ON vocabulary_words(word);

-- ============================================================================
-- Table: user_progress_summary
-- ============================================================================
-- Materialized view or table for quick access to user progress statistics
-- This can be updated via triggers or computed on-the-fly
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_progress_summary (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    
    -- Overall statistics
    total_sessions INTEGER NOT NULL DEFAULT 0,
    total_topics_discussed INTEGER NOT NULL DEFAULT 0,
    total_conversation_turns INTEGER NOT NULL DEFAULT 0,
    
    -- Average scores
    average_clarity_score DECIMAL(3, 2), -- Average clarity score across all turns
    average_pace_wpm INTEGER, -- Average speaking pace
    
    -- Topic-specific counts (stored as JSONB for flexibility)
    topics_breakdown JSONB, -- e.g., {"Gaming": 5, "Food": 3, "Hobbies": 2}
    
    -- Dimension usage (stored as JSONB)
    dimensions_used JSONB, -- e.g., {"Social Context": 3, "Emotional": 2, "Basic Preferences": 10}
    
    -- Timestamps
    last_session_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index
CREATE INDEX IF NOT EXISTS idx_user_progress_summary_user_id ON user_progress_summary(user_id);

-- ============================================================================
-- Functions and Triggers
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_session_topics_updated_at BEFORE UPDATE ON session_topics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversation_turns_updated_at BEFORE UPDATE ON conversation_turns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_progress_summary_updated_at BEFORE UPDATE ON user_progress_summary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update session_topic turn_count when a new turn is created
CREATE OR REPLACE FUNCTION update_session_topic_turn_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE session_topics
    SET turn_count = turn_count + 1,
        last_activity_at = NOW(),
        updated_at = NOW()
    WHERE id = NEW.session_topic_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update turn count
CREATE TRIGGER update_turn_count_after_turn_insert
    AFTER INSERT ON conversation_turns
    FOR EACH ROW EXECUTE FUNCTION update_session_topic_turn_count();

-- ============================================================================
-- Row Level Security (RLS) Policies (Optional but Recommended)
-- ============================================================================
-- Enable RLS on all tables for security
-- Users should only see their own data

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_turns ENABLE ROW LEVEL SECURITY;
ALTER TABLE response_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE vocabulary_words ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progress_summary ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own data
-- Note: Adjust these policies based on your authentication setup
-- This assumes you're using Supabase Auth with user.id matching users.id

-- Example policy (adjust based on your auth setup):
-- CREATE POLICY "Users can view own data" ON users
--     FOR SELECT USING (auth.uid() = id);

-- ============================================================================
-- Useful Views (Optional)
-- ============================================================================

-- View: Active sessions with user info
CREATE OR REPLACE VIEW active_sessions_view AS
SELECT 
    s.id AS session_id,
    u.id AS user_id,
    u.name AS user_name,
    s.started_at,
    s.status,
    COUNT(DISTINCT st.id) AS topics_count,
    SUM(st.turn_count) AS total_turns
FROM sessions s
JOIN users u ON s.user_id = u.id
LEFT JOIN session_topics st ON s.id = st.session_id
WHERE s.status = 'active'
GROUP BY s.id, u.id, u.name, s.started_at, s.status;

-- View: User progress by topic
CREATE OR REPLACE VIEW user_topic_progress_view AS
SELECT 
    u.id AS user_id,
    u.name AS user_name,
    st.topic_name,
    COUNT(DISTINCT st.session_id) AS sessions_count,
    SUM(st.turn_count) AS total_turns,
    AVG(ct.clarity_score) AS avg_clarity_score,
    AVG(ct.pace_wpm) AS avg_pace_wpm
FROM users u
JOIN sessions s ON u.id = s.user_id
JOIN session_topics st ON s.id = st.session_id
LEFT JOIN conversation_turns ct ON st.id = ct.session_topic_id
GROUP BY u.id, u.name, st.topic_name;

-- ============================================================================
-- End of Schema
-- ============================================================================
