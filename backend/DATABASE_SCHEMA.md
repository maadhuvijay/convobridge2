# ConvoBridge Database Schema Documentation

## Overview

This document describes the Supabase database schema for ConvoBridge. The schema is designed to track user sessions, conversation turns, topics, and progress across multiple sessions.

## Table Structure

### 1. `users`
Stores basic user information.

**Columns:**
- `id` (UUID, Primary Key): Unique user identifier
- `name` (TEXT): User's name (from login)
- `created_at` (TIMESTAMP): When the user account was created
- `updated_at` (TIMESTAMP): Last update time

**Usage:** Created when a user first logs in.

---

### 2. `sessions`
Tracks each login session (from login to logout).

**Columns:**
- `id` (UUID, Primary Key): Unique session identifier
- `user_id` (UUID, Foreign Key → `users.id`): The user this session belongs to
- `started_at` (TIMESTAMP): When the session started (login)
- `ended_at` (TIMESTAMP, Nullable): When the session ended (logout)
- `status` (TEXT): 'active' or 'completed'
- `created_at` (TIMESTAMP): Record creation time
- `updated_at` (TIMESTAMP): Last update time

**Usage:** 
- Create a new session when user logs in
- Update `ended_at` and set `status = 'completed'` when user logs out

---

### 3. `session_topics`
Tracks which topics were discussed in each session.

**Columns:**
- `id` (UUID, Primary Key): Unique identifier
- `session_id` (UUID, Foreign Key → `sessions.id`): The session
- `topic_name` (TEXT): Topic name (e.g., 'Gaming', 'Food', 'Hobbies')
- `turn_count` (INTEGER): Number of conversation turns on this topic (auto-updated)
- `started_at` (TIMESTAMP): When this topic was first discussed
- `last_activity_at` (TIMESTAMP): Last activity on this topic
- `created_at` (TIMESTAMP): Record creation time
- `updated_at` (TIMESTAMP): Last update time

**Usage:**
- Create a new record when a user selects a topic in a session
- `turn_count` is automatically incremented by trigger when turns are added
- One topic per session (enforced by UNIQUE constraint)

---

### 4. `conversation_turns`
Tracks individual conversation turns (question-answer exchanges).

**Columns:**
- `id` (UUID, Primary Key): Unique identifier
- `session_topic_id` (UUID, Foreign Key → `session_topics.id`): The topic session
- `turn_number` (INTEGER): Sequential turn number within the topic (1, 2, 3...)
- `dimension` (TEXT): Conversation dimension used (e.g., 'Basic Preferences', 'Social Context')
- `difficulty_level` (INTEGER): Difficulty level (1, 2, 3...)
- `question` (TEXT): The question asked
- `user_response` (TEXT, Nullable): User's response (transcript or text)
- `response_type` (TEXT): 'selected_option', 'custom_speech', or 'custom_text'
- `selected_option_index` (INTEGER, Nullable): If user selected a pre-generated option (0, 1, or 2)
- `transcript` (TEXT, Nullable): Transcribed speech (if speech was used)
- `clarity_score` (DECIMAL(3,2), Nullable): Speech clarity score (0.00 to 1.00)
- `wer_estimate` (DECIMAL(3,2), Nullable): Word Error Rate estimate
- `pace_wpm` (INTEGER, Nullable): Words per minute
- `filler_words` (TEXT[], Nullable): Array of filler words found
- `feedback` (TEXT, Nullable): Feedback from speech analysis
- `strengths` (TEXT[], Nullable): Array of strengths identified
- `suggestions` (TEXT[], Nullable): Array of suggestions for improvement
- `question_asked_at` (TIMESTAMP): When the question was asked
- `response_received_at` (TIMESTAMP, Nullable): When the response was received
- `created_at` (TIMESTAMP): Record creation time
- `updated_at` (TIMESTAMP): Last update time

**Usage:**
- Create a new turn when a question is generated
- Update with user response and speech analysis results when available

---

### 5. `response_options`
Stores the response options generated for each conversation turn.

**Columns:**
- `id` (UUID, Primary Key): Unique identifier
- `conversation_turn_id` (UUID, Foreign Key → `conversation_turns.id`): The turn
- `option_index` (INTEGER): Index of the option (0, 1, or 2)
- `option_text` (TEXT): The option text
- `created_at` (TIMESTAMP): Record creation time

**Usage:**
- Insert 2-3 options when response options are generated for a turn
- Used to track what options were presented to the user

---

### 6. `vocabulary_words`
Stores vocabulary words shown during conversation turns.

**Columns:**
- `id` (UUID, Primary Key): Unique identifier
- `conversation_turn_id` (UUID, Foreign Key → `conversation_turns.id`): The turn
- `word` (TEXT): The vocabulary word
- `word_type` (TEXT, Nullable): Part of speech (e.g., 'noun', 'verb')
- `definition` (TEXT): Word definition
- `example` (TEXT): Example sentence
- `created_at` (TIMESTAMP): Record creation time

**Usage:**
- Insert when vocabulary is generated for a turn

---

### 7. `user_progress_summary`
Summary table for quick access to user progress statistics.

**Columns:**
- `user_id` (UUID, Primary Key, Foreign Key → `users.id`): The user
- `total_sessions` (INTEGER): Total number of sessions
- `total_topics_discussed` (INTEGER): Total unique topics discussed
- `total_conversation_turns` (INTEGER): Total conversation turns
- `average_clarity_score` (DECIMAL(3,2), Nullable): Average clarity score
- `average_pace_wpm` (INTEGER, Nullable): Average speaking pace
- `topics_breakdown` (JSONB, Nullable): Topic counts (e.g., `{"Gaming": 5, "Food": 3}`)
- `dimensions_used` (JSONB, Nullable): Dimension usage counts
- `last_session_at` (TIMESTAMP, Nullable): Last session timestamp
- `created_at` (TIMESTAMP): Record creation time
- `updated_at` (TIMESTAMP): Last update time

**Usage:**
- Can be updated via triggers or computed on-the-fly
- Useful for dashboard and progress tracking

---

## Relationships

```
users (1) ──→ (many) sessions
sessions (1) ──→ (many) session_topics
session_topics (1) ──→ (many) conversation_turns
conversation_turns (1) ──→ (many) response_options
conversation_turns (1) ──→ (many) vocabulary_words
users (1) ──→ (1) user_progress_summary
```

---

## Automatic Features

### Triggers

1. **`update_updated_at_column()`**: Automatically updates `updated_at` timestamp on relevant tables
2. **`update_session_topic_turn_count()`**: Automatically increments `turn_count` in `session_topics` when a new turn is created

### Indexes

All foreign keys and commonly queried columns are indexed for performance.

---

## Setup Instructions

1. **Open Supabase Dashboard**: Go to your Supabase project
2. **Open SQL Editor**: Navigate to SQL Editor
3. **Run the Schema**: Copy and paste the contents of `database_schema.sql` and execute
4. **Verify Tables**: Check that all tables are created successfully

---

## Example Queries

### Get all sessions for a user
```sql
SELECT * FROM sessions 
WHERE user_id = 'user-uuid-here' 
ORDER BY started_at DESC;
```

### Get conversation turns for a topic in a session
```sql
SELECT ct.*, st.topic_name
FROM conversation_turns ct
JOIN session_topics st ON ct.session_topic_id = st.id
WHERE st.session_id = 'session-uuid-here'
  AND st.topic_name = 'Gaming'
ORDER BY ct.turn_number;
```

### Get user's average clarity score
```sql
SELECT 
    u.name,
    AVG(ct.clarity_score) as avg_clarity,
    COUNT(ct.id) as total_turns
FROM users u
JOIN sessions s ON u.id = s.user_id
JOIN session_topics st ON s.id = st.session_id
JOIN conversation_turns ct ON st.id = ct.session_topic_id
WHERE u.id = 'user-uuid-here'
GROUP BY u.id, u.name;
```

### Get topics discussed in a session
```sql
SELECT topic_name, turn_count, started_at, last_activity_at
FROM session_topics
WHERE session_id = 'session-uuid-here'
ORDER BY started_at;
```

---

## Notes

- All timestamps use `TIMESTAMP WITH TIME ZONE` for proper timezone handling
- UUIDs are used for all primary keys for better distribution and security
- Row Level Security (RLS) is enabled but policies need to be configured based on your authentication setup
- The `user_progress_summary` table can be updated via triggers or computed on-demand
- Consider adding additional indexes based on your query patterns

---

## Future Enhancements

- Add audio file storage references (if storing audio files)
- Add conversation flow tracking (which dimension led to which)
- Add difficulty progression tracking
- Add vocabulary learning progress
- Add session analytics and insights
