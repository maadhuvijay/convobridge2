-- ============================================================================
-- Fix RLS Policies for Development
-- ============================================================================
-- This script creates policies that allow full access for development.
-- WARNING: These policies are permissive and should be restricted for production!
-- ============================================================================

-- Option 1: Disable RLS entirely (Easiest for development)
-- Uncomment the lines below to disable RLS on all tables:

-- ALTER TABLE users DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE session_topics DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversation_turns DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE response_options DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE vocabulary_words DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_progress_summary DISABLE ROW LEVEL SECURITY;

-- Option 2: Create permissive policies for development
-- These allow all operations for authenticated and anonymous users
-- (Use this if you want to keep RLS enabled but allow access)

-- Sessions table policies
CREATE POLICY "Allow all operations on sessions" ON sessions
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Users table policies
CREATE POLICY "Allow all operations on users" ON users
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Session topics table policies
CREATE POLICY "Allow all operations on session_topics" ON session_topics
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Conversation turns table policies
CREATE POLICY "Allow all operations on conversation_turns" ON conversation_turns
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Response options table policies
CREATE POLICY "Allow all operations on response_options" ON response_options
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Vocabulary words table policies
CREATE POLICY "Allow all operations on vocabulary_words" ON vocabulary_words
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- User progress summary table policies
CREATE POLICY "Allow all operations on user_progress_summary" ON user_progress_summary
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- Note: If you get "policy already exists" errors, drop them first:
-- ============================================================================
-- DROP POLICY IF EXISTS "Allow all operations on sessions" ON sessions;
-- DROP POLICY IF EXISTS "Allow all operations on users" ON users;
-- DROP POLICY IF EXISTS "Allow all operations on session_topics" ON session_topics;
-- DROP POLICY IF EXISTS "Allow all operations on conversation_turns" ON conversation_turns;
-- DROP POLICY IF EXISTS "Allow all operations on response_options" ON response_options;
-- DROP POLICY IF EXISTS "Allow all operations on vocabulary_words" ON vocabulary_words;
-- DROP POLICY IF EXISTS "Allow all operations on user_progress_summary" ON user_progress_summary;
