# ConvoBridge Agent Flow & Architecture

## Overview

ConvoBridge uses a **multi-agent architecture** with an Orchestrator Team that coordinates specialized sub-agents. The Orchestrator makes intelligent decisions about conversation flow, dimension selection, and delegates tasks to appropriate sub-agents.

---

## Agent Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│              Orchestrator Team (Agno Team)              │
│  - Coordinates all sub-agents                           │
│  - Makes intelligent dimension selection                │
│  - Analyzes user engagement & speech performance        │
│  - Returns structured JSON: {question, dimension,       │
│    reasoning, difficulty_level}                         │
└──────────────────┬──────────────────────────────────────┘
                   │
       ┌───────────┼───────────┬──────────────┐
       │           │           │              │
       ▼           ▼           ▼              ▼
┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Conversation│ │ Response │ │Vocabulary│ │Speech Analysis│
│   Agent     │ │  Agent   │ │  Agent   │ │    Agent      │
└─────────────┘ └──────────┘ └──────────┘ └──────────────┘
```

---

## Agent Details

### 1. Orchestrator Team

**Location**: `backend/orchestrator_agent.py`

**Type**: Agno Team (coordinates sub-agents)

**Model**: GPT-4o-mini

**Members**:
- Conversation Agent
- Response Agent
- Vocabulary Agent
- Speech Analysis Agent

**Tools**: ReasoningTools (think, analyze)

**Key Responsibilities**:
1. **Topic-Based Reasoning**: Analyzes user-chosen topics to determine best conversation approach
2. **Intelligent Dimension Selection**:
   - Analyzes user engagement (response length, detail, enthusiasm)
   - Reviews dimension history (enforces max 2 consecutive turns on same dimension)
   - Considers speech performance metrics (clarity trends, pace, confidence)
   - Selects appropriate dimension from 9 available dimensions
3. **Difficulty Adjustment**: Adjusts difficulty based on speech performance
4. **Delegation**: Instructs Conversation Agent with topic-specific guidance
5. **Output**: Returns structured JSON with question, dimension, reasoning, difficulty_level

**Key Instructions**:
- CRITICAL: DO NOT use the same dimension for more than 2 consecutive turns
- If last 2 turns used same dimension, MUST switch to different dimension
- Analyze speech performance trends to adapt questions
- Ensure variety to keep conversation interesting

**Output Format**:
```json
{
  "question": "the conversation question text",
  "dimension": "Basic Preferences | Depth/Specificity | Social Context | etc.",
  "reasoning": "brief explanation of why this dimension was chosen",
  "difficulty_level": 1
}
```

---

## Orchestrator Abilities - Detailed Documentation

### Core Capabilities

The Orchestrator is the **intelligent decision-making center** of ConvoBridge. It uses advanced reasoning capabilities to analyze multiple data sources and make contextually-aware decisions about conversation flow.

#### 1. Reasoning Tools

The Orchestrator has access to **ReasoningTools** from Agno, which provide:

- **`think`**: Deep reasoning about complex problems
- **`analyze`**: Structured analysis of data and context
- **Few-shot examples**: Built-in examples for better reasoning patterns

**When Orchestrator Uses Reasoning Tools**:
- Analyzing user's chosen topic to determine best conversation approach
- Deciding which conversation dimension is most appropriate
- Considering user's conversation history and engagement level
- Breaking down complex coordination tasks into steps
- Deciding which sub-agent to delegate to and when
- Reflecting on the quality of responses from sub-agents
- Adjusting approach based on conversation context
- Considering multiple perspectives before making decisions

#### 2. Topic-Based Reasoning

**Ability**: Analyzes user-chosen topics to determine the best conversation approach

**Process**:
1. **THINK**: Analyzes what makes the topic engaging for conversation practice
   - Understands topic characteristics (gaming = interactive, food = sensory, hobbies = personal)
   - Identifies natural conversation entry points
   - Considers age-appropriateness and educational value

2. **ANALYZE**: Considers what types of questions work best for the topic
   - Gaming: Preferences, experiences, social aspects
   - Food: Tastes, cooking, cultural aspects
   - Hobbies: Activities, time spent, personal growth
   - Weekend Plans: Social interactions, preferences
   - YouTube: Content preferences, watching habits

3. **DECIDE**: Chooses the most appropriate conversation dimension based on:
   - Topic characteristics (gaming = preferences, food = experiences, hobbies = activities)
   - User's conversation history (if returning user)
   - Engagement level and difficulty needs

4. **DELEGATE**: Instructs Conversation Agent with topic-specific guidance
   - Provides clear instructions about topic focus
   - Ensures questions are relevant to the specific topic
   - Maintains educational and age-appropriate content

**Topic-Specific Guidance**:
- **Gaming**: Focus on game preferences, favorite genres, playing experiences
- **Food**: Focus on favorite dishes, cooking experiences, restaurant preferences
- **Hobbies**: Focus on activities, interests, time spent on hobbies
- **Weekend Plans**: Focus on activities, preferences, social interactions
- **YouTube**: Focus on favorite channels, content preferences, watching habits

#### 3. User Response Analysis

**Ability**: Deeply analyzes user responses to understand context and emotional state

**Analysis Dimensions**:

1. **Content Analysis**:
   - What the user said and their main points
   - Key topics or themes they mentioned
   - Specific items, preferences, or experiences mentioned
   - Cultural or regional context (e.g., "Indian festivals", "Super Mario")

2. **Emotional Tone Detection**:
   - **Positive**: Happy, excited, enthusiastic responses
   - **Negative**: Frustrated, sad, disappointed, difficult experiences
   - **Neutral**: Matter-of-fact, informative responses
   - Orchestrator uses this to match emotional tone in follow-up questions

3. **Engagement Level Assessment**:
   - **High Engagement**: Detailed responses (>20 words), specific mentions, enthusiasm
   - **Medium Engagement**: Moderate responses (10-20 words), some detail
   - **Low Engagement**: Short responses (<10 words), minimal detail
   - Orchestrator adapts dimension selection based on engagement:
     - High engagement → Deeper dimensions (Depth/Specificity, Reflective/Why)
     - Low engagement → Simpler dimensions (Basic Preferences, Temporal/Frequency)

4. **Response Depth Analysis**:
   - Short/quick responses → Keep questions simple
   - Detailed/engaged responses → Can explore deeper dimensions
   - Orchestrator matches question complexity to response depth

#### 4. Conversation Context Analysis

**Ability**: Reviews and analyzes conversation history to maintain continuity and variety

**Context Elements Analyzed**:

1. **Previous Questions**:
   - Tracks all questions asked in the conversation
   - Ensures questions are not repeated
   - Identifies question patterns and themes
   - Builds on previous discussions naturally

2. **Dimension History**:
   - Tracks last 2-3 dimensions used
   - **CRITICAL ENFORCEMENT**: Detects if same dimension used 2+ times consecutively
   - If detected, forces immediate switch to different dimension
   - Avoids recently used dimensions (unless natural continuation AND not already used 2+ times)
   - Actively rotates through dimensions to maintain variety

3. **Natural Conversation Flow**:
   - Determines what would logically come next
   - Ensures questions build naturally on previous responses
   - Maintains topic coherence while exploring different angles

4. **User Engagement Patterns**:
   - Tracks response length and detail over time
   - Identifies engagement trends (increasing/decreasing)
   - Adapts dimension selection to match engagement patterns

#### 5. Speech Performance Integration

**Ability**: Integrates speech analysis metrics into decision-making for adaptive conversations

**Speech Metrics Analyzed**:

1. **Clarity Scores**:
   - Recent clarity scores (last 3-5 turns)
   - Average clarity over conversation
   - Clarity trends: improving, declining, or stable
   - Orchestrator uses this to:
     - **If improving**: Gradually increase challenge, explore new dimensions
     - **If declining**: Simplify, use familiar dimensions, reduce difficulty
     - **If stable and high (>0.85)**: User is excelling, can increase challenge
     - **If stable and low (<0.65)**: User may be struggling, provide more support

2. **Speaking Pace**:
   - Words per minute (WPM)
   - Pace trends: increasing, decreasing, or stable
   - Orchestrator considers pace when:
     - Adjusting question complexity
     - Selecting dimensions (faster pace might indicate confidence)

3. **Confidence Level**:
   - **High**: User is confident, can handle more challenging questions
   - **Medium**: Maintain current difficulty or slight adjustment
   - **Low**: User may be struggling, simplify and provide support
   - Orchestrator uses confidence to:
     - Adjust difficulty level
     - Select appropriate dimensions
     - Determine question complexity

4. **Adaptation Strategy**:
   - **Immediate Feedback**: Next question adapts based on recent speech performance
   - **Trend-Based**: Analyzes patterns over multiple turns
   - **Confidence-Based**: Adjusts difficulty and dimension selection

#### 6. Intelligent Dimension Selection

**Ability**: Selects the most appropriate conversation dimension from 9 available options

**Available Dimensions**:
1. **Basic Preferences**: Likes, dislikes, favorites, simple choices (ALWAYS used for first question)
2. **Depth/Specificity**: Deeper, more detailed questions
3. **Social Context**: Discussing social aspects, involving others
4. **Emotional**: Feelings, excitement, frustration, reactions
5. **Temporal / Frequency**: When, how often, past experiences, future plans
6. **Comparative**: Comparing two things, what is better/worse
7. **Reflective / Why**: Reasons, motivations, 'why' questions
8. **Descriptive / Detail**: Sensory details, appearance, setting
9. **Challenge / Growth**: Learning curves, difficulties, improvements

**Selection Criteria**:

1. **Dimension Switching Enforcement** (CRITICAL):
   - Checks last 2 dimensions in history
   - If same dimension appears 2+ times consecutively → **MUST switch**
   - Explicit warning added to prompt: "⚠️ CRITICAL: Last 2 turns used 'X'. You MUST switch to a DIFFERENT dimension now!"
   - This ensures conversation variety and prevents getting stuck

2. **Topic Characteristics**:
   - Gaming → Preferences, Social Context, Comparative
   - Food → Preferences, Descriptive, Emotional
   - Hobbies → Temporal, Challenge/Growth, Reflective

3. **User Engagement Level**:
   - High engagement → Depth/Specificity, Reflective/Why, Challenge/Growth
   - Medium engagement → Social Context, Emotional, Temporal
   - Low engagement → Basic Preferences, Descriptive, Temporal

4. **Speech Performance**:
   - High clarity + improving → Explore new dimensions, increase challenge
   - Low clarity + declining → Use familiar dimensions, simplify
   - Stable high clarity → Can increase challenge
   - Stable low clarity → Provide more support

5. **Natural Conversation Flow**:
   - Builds on what user mentioned
   - Explores different angles of the topic
   - Maintains logical progression

6. **Dimension History**:
   - Avoids recently used dimensions (unless natural continuation)
   - Actively rotates through dimensions
   - Ensures variety over conversation

**Selection Process**:
```
1. Check dimension history → Detect if same dimension used 2+ times
2. If yes → Force switch to different dimension
3. If no → Analyze:
   - Topic characteristics
   - User engagement level
   - Speech performance metrics
   - Natural conversation flow
4. Select dimension that:
   - Builds on user's response
   - Matches engagement level
   - Adapts to speech performance
   - Maintains variety
```

#### 7. Difficulty Level Adjustment

**Ability**: Dynamically adjusts conversation difficulty based on multiple factors

**Adjustment Factors**:

1. **Speech Performance**:
   - **High confidence + improving clarity** → Consider increasing difficulty
   - **Low confidence + declining clarity** → Consider decreasing difficulty
   - **Medium confidence** → Maintain current difficulty or slight adjustment

2. **User Engagement**:
   - High engagement → Can handle higher difficulty
   - Low engagement → Keep difficulty low

3. **Clarity Trends**:
   - Improving → Gradually increase challenge
   - Declining → Simplify and reduce difficulty
   - Stable high → User is excelling, can increase challenge
   - Stable low → User may be struggling, provide more support

**Difficulty Levels**:
- **Level 1**: Simple, direct questions (default)
- **Level 2**: Moderate complexity, some depth
- **Level 3**: Complex questions, deeper exploration

**Adjustment Strategy**:
- Orchestrator can override requested difficulty level
- Adjusts based on real-time performance data
- Ensures questions match user's current capability

#### 8. Sub-Agent Delegation

**Ability**: Intelligently delegates tasks to appropriate sub-agents with clear instructions

**Delegation Patterns**:

1. **To Conversation Agent**:
   - **For Initial Questions**: "Generate a simple question about [topic] using Basic Preferences dimension"
   - **For Follow-Up Questions**: 
     - "Generate a follow-up question that:
       - Acknowledges the user's response appropriately
       - Matches the emotional tone (empathetic for negative, enthusiastic for positive)
       - Builds naturally on what the user mentioned
       - Uses the chosen dimension effectively
       - Adapts complexity based on speech performance trends
       - Does NOT repeat the previous question"

2. **To Response Agent** (via API, not direct delegation):
   - Orchestrator doesn't directly delegate to Response Agent
   - API endpoint calls Response Agent with topic-aware prompts

3. **To Vocabulary Agent** (via API, not direct delegation):
   - Orchestrator doesn't directly delegate to Vocabulary Agent
   - API endpoint calls Vocabulary Agent with question context

4. **To Speech Analysis Agent** (via API, not direct delegation):
   - Orchestrator doesn't directly delegate to Speech Analysis Agent
   - API endpoint calls Speech Analysis Agent with audio data

**Delegation Instructions Include**:
- Topic-specific guidance
- Dimension requirements
- Emotional tone matching
- Complexity adaptation
- Context awareness requirements

#### 9. Safety & Content Moderation

**Ability**: Ensures all generated content is safe, appropriate, and educational

**Safety Guidelines** (CRITICAL):
- All questions MUST be appropriate for teens and educational
- NEVER generate questions involving:
  - Violence
  - Self-harm
  - Harming others
  - Anti-social elements
  - Illegal activities
- Keep all content:
  - Positive and supportive
  - Age-appropriate
  - Focused on building confidence and social skills

**Content Validation**:
- Orchestrator validates dimension appropriateness
- Checks for teen-appropriate content
- Ensures educational value
- Maintains positive, supportive tone

#### 10. Context Data Processing

**Ability**: Processes and synthesizes multiple data sources into intelligent decisions

**Input Data Sources**:

1. **Topic Information**:
   - Current conversation topic
   - Topic characteristics and natural conversation angles

2. **User Response**:
   - What user said
   - Emotional tone
   - Engagement level
   - Key themes and mentions

3. **Conversation History**:
   - Previous questions (summarized, max 2-3 turns)
   - Dimension history (last 2-3 dimensions)
   - Conversation flow and patterns

4. **Speech Performance Metrics**:
   - Clarity scores and trends
   - Speaking pace and trends
   - Confidence level
   - Recent performance data

5. **User Context**:
   - User ID
   - Difficulty level preference
   - Engagement level (low/medium/high)

**Data Processing**:
- Orchestrator receives compressed, structured JSON context
- Processes all data sources simultaneously
- Synthesizes information into coherent decisions
- Balances multiple factors (engagement, speech, history, topic)

**Context JSON Format** (for follow-up questions):
```json
{
  "user_id": "uuid",
  "topic": "gaming",
  "prev_q": "What's your favorite game?",
  "user_resp": "I like Super Mario",
  "diff": 1,
  "eng": "high",
  "history": "summary of conversation...",
  "dims_used": ["Basic Preferences"],
  "speech": "sp:tr=i,cl=0.88,pace=130,conf=high"
}
```

#### 11. Output Generation

**Ability**: Returns structured, validated JSON responses

**Output Structure**:
```json
{
  "question": "the conversation question text generated by the Conversation Agent",
  "dimension": "the chosen conversation dimension",
  "reasoning": "brief explanation of why this dimension was chosen (optional but preferred)",
  "difficulty_level": 1
}
```

**Output Validation**:
- Orchestrator response is parsed and validated
- Required fields checked: `question`, `dimension`
- Optional fields: `reasoning`, `difficulty_level`
- Dimension validated against standard list (with flexibility for new dimensions)
- Detailed logging of orchestrator decisions

**Error Handling**:
- If orchestrator returns invalid JSON → Error with details
- If required fields missing → Error with specific field
- If dimension not in list → Warning logged, but allowed (with teen-appropriateness check)
- Rate limit errors → Automatic retry with exponential backoff

#### 12. Decision Logging

**Ability**: Provides detailed logging of all decisions for transparency and debugging

**Logged Information**:
- Topic
- Is First Question (true/false)
- Chosen Dimension
- Chosen Difficulty Level
- Requested Difficulty Level
- Reasoning (if provided)
- Generated Question
- Dimension validation status

**Log Format**:
```
[ORCHESTRATOR] ===== DECISION LOG =====
[ORCHESTRATOR] Topic: gaming
[ORCHESTRATOR] Is First Question: True
[ORCHESTRATOR] Chosen Dimension: Basic Preferences
[ORCHESTRATOR] Chosen Difficulty Level: 1
[ORCHESTRATOR] Requested Difficulty Level: 1
[ORCHESTRATOR] Reasoning: This question explores gaming preferences...
[ORCHESTRATOR] Generated Question: What's your favorite video game?
[ORCHESTRATOR] ===== END DECISION LOG =====
```

---

### Orchestrator Decision-Making Process

#### For First Questions

```
1. Receive: Topic, difficulty_level, user_id
2. THINK: Analyze topic characteristics
3. ANALYZE: Determine best approach for first question
4. DECIDE: Always select "Basic Preferences" dimension
5. DECIDE: Set difficulty_level = 1 (or requested level)
6. DELEGATE: Instruct Conversation Agent to generate simple question
7. RETURN: JSON with question, dimension, reasoning, difficulty_level
```

#### For Follow-Up Questions

```
1. Receive: Topic, previous_question, user_response, difficulty_level, context
2. THINK: Analyze user response
   - What user said
   - Emotional tone
   - Response depth
   - Key themes
3. ANALYZE: Review context
   - Previous questions
   - Dimension history (check for 2+ consecutive uses)
   - Engagement level
   - Speech performance metrics
4. DECIDE: Select next dimension
   - If same dimension used 2+ times → Force switch
   - Otherwise: Analyze topic, engagement, speech performance
   - Choose dimension that builds on response, matches engagement, adapts to speech
5. DECIDE: Adjust difficulty
   - Based on speech confidence and clarity trends
6. DELEGATE: Instruct Conversation Agent
   - With dimension, tone matching, complexity adaptation
7. RETURN: JSON with question, dimension, reasoning, difficulty_level
```

---

### Orchestrator Strengths

1. **Multi-Factor Analysis**: Considers topic, history, engagement, and speech performance simultaneously
2. **Adaptive Intelligence**: Adjusts questions based on real-time user performance
3. **Variety Enforcement**: Actively prevents getting stuck on one dimension
4. **Context Awareness**: Maintains conversation continuity while exploring new angles
5. **Safety First**: Ensures all content is appropriate and educational
6. **Transparency**: Provides reasoning for all decisions
7. **Resilience**: Handles errors gracefully with retry logic
8. **Efficiency**: Uses compressed context to reduce token usage

---

### Orchestrator Limitations & Considerations

1. **LLM-Based**: Decisions depend on LLM reasoning quality
2. **Context Window**: Limited by token budget (mitigated by compression)
3. **Rate Limits**: Subject to OpenAI API rate limits (handled with retry logic)
4. **Dimension Flexibility**: Can choose dimensions not in standard list (with validation)
5. **First Question Constraint**: Always uses "Basic Preferences" for first questions

---

### Orchestrator vs Direct Agent Calls

**Orchestrator Used For**:
- All question generation (initial and follow-up)
- Dimension selection
- Difficulty adjustment
- Context-aware decision making

**Direct Agent Calls** (bypass orchestrator):
- Response options generation (Response Agent)
- Vocabulary generation (Vocabulary Agent)
- Speech analysis (Speech Analysis Agent)

**Why This Architecture**:
- Orchestrator provides intelligent coordination for questions
- Direct calls for simpler, context-independent tasks
- Balances intelligence with efficiency

---

### 2. Conversation Agent

**Location**: `backend/subagents/conversation_agent.py`

**Type**: Agno Agent (member of Orchestrator Team)

**Model**: GPT-4o-mini

**Tools**:
- `get_context`: Gathers conversation context
- `generate_followup_question`: Generates contextual follow-up questions

**Key Responsibilities**:
1. **Initial Questions**: Generate simple questions using "Basic Preferences" dimension
2. **Follow-Up Questions**: 
   - Use `get_context` to gather context
   - Use `generate_followup_question` to create follow-ups
   - Format: "Acknowledgement + Personal Preference + Question"
   - Match emotional tone (positive/negative/neutral)
   - Vary acknowledgements to avoid repetition
   - NEVER repeat the same question

**Key Instructions**:
- For INITIAL questions: Return ONLY the question text
- For FOLLOW-UP questions: Use tools to gather context first
- Match emotional tone of user's response
- Adapt to requested dimension from orchestrator
- Format follow-ups with line breaks: "Ack + preference\n\nQuestion"

**Output**: Plain text question (no JSON, no markdown)

---

### 3. Response Agent

**Location**: `backend/subagents/response_generate_agent.py`

**Type**: Agno Agent (member of Orchestrator Team)

**Model**: GPT-4o-mini

**Tools**: None (direct prompt-based generation)

**Key Responsibilities**:
1. Generate exactly 2 response options
2. **Topic-Aware Generation**: Options MUST be specifically relevant to the topic
   - Gaming → games, gaming experiences, gaming preferences
   - Food → food, dishes, cooking, eating experiences
   - Hobbies → hobbies, activities, interests
3. **User Context Integration**: Use user's previous response when available
4. Match conversation dimension (Preferences→opinions, Emotional→feelings, etc.)

**Key Instructions**:
- ⚠️ TOPIC IS MANDATORY - NO EXCEPTIONS
- ⚠️ USER CONTEXT IS MANDATORY (when provided)
- NO generic options that could apply to any topic
- Simple, direct responses (Level 1 difficulty)

**Output Format**:
```json
["option1", "option2"]
```

**Note**: Frontend adds "Choose your own response" as third option

---

### 4. Vocabulary Agent

**Location**: `backend/subagents/vocabulary_agent.py`

**Type**: Agno Agent (member of Orchestrator Team)

**Model**: GPT-4o-mini

**Tools**: None (direct prompt-based generation)

**Key Responsibilities**:
1. Identify key vocabulary word relevant to the question
2. Provide definition, type, and example
3. Ensure word is contextually appropriate for the specific question
4. Choose different words for different questions (no reuse)

**Key Instructions**:
- Vocabulary word MUST be directly relevant to the specific question and topic
- Choose a different word for each different question
- Educational and meaningful for the conversation

**Output Format**:
```json
{
  "word": "preference",
  "type": "noun",
  "definition": "a greater liking for one alternative over another",
  "example": "My preference is to play action games."
}
```

---

### 5. Speech Analysis Agent

**Location**: `backend/subagents/speech_analysis_agent.py`

**Type**: Agno Agent (member of Orchestrator Team)

**Model**: GPT-4o-mini

**Tools**: Speech transcription tool (via `analyze_speech_with_audio`)

**Key Responsibilities**:
1. Transcribe audio using OpenAI Whisper
2. Calculate Word Error Rate (WER) when expected response provided
3. Provide clarity score (0.0 to 1.0)
4. Estimate speaking pace (words per minute)
5. Identify filler words
6. Provide encouraging feedback with strengths and suggestions

**Key Instructions**:
- Be positive and encouraging
- Focus on strengths and progress
- Calculate WER by comparing transcript to expected response
- Provide constructive feedback that builds confidence

**Output Format**:
```json
{
  "transcript": "what the teen actually said",
  "wer_estimate": 0.15,
  "clarity_score": 0.85,
  "pace_wpm": 130,
  "filler_words": ["um", "like"],
  "feedback": "Great job! Your speech was clear and well-paced.",
  "strengths": ["clear pronunciation", "good pace"],
  "suggestions": ["try to reduce filler words"]
}
```

---

## Complete Flow Diagrams

### Flow 1: Start Conversation (First Question)

```
User Selects Topic
    │
    ▼
API: /api/start_conversation
    │
    ├─ Check if first question (database)
    ├─ Check pre-generated cache (first questions)
    │  └─ If cached → Return instantly
    │
    ├─ Skip history retrieval (optimization for first questions)
    │
    ▼
Orchestrator.run(prompt)
    │
    ├─ THINK: Analyze topic characteristics
    ├─ ANALYZE: Determine best approach
    ├─ DECIDE: Select "Basic Preferences" dimension (always for first Q)
    ├─ DECIDE: Set difficulty_level = 1
    │
    ▼
Delegates to Conversation Agent
    │
    ├─ Conversation Agent generates question
    │  └─ Simple question about topic preferences
    │
    ▼
Orchestrator returns JSON:
{
  "question": "...",
  "dimension": "Basic Preferences",
  "reasoning": "...",
  "difficulty_level": 1
}
    │
    ▼
API:
    ├─ Generate TTS audio (background)
    ├─ Create database turn
    ├─ Return question + audio + turn_id
    │
    ▼
Frontend displays question + auto-plays audio
    │
    ▼
Background: /api/get_conversation_details
    ├─ Response Agent (parallel)
    │  └─ Generate 2 topic-specific options
    └─ Vocabulary Agent (parallel)
       └─ Generate relevant vocabulary word
```

---

### Flow 2: Continue Conversation (Follow-Up Question)

```
User Responds (audio/text)
    │
    ▼
API: /api/continue_conversation
    │
    ├─ Parallel: Update previous turn + Fetch context
    │  ├─ Get conversation history
    │  ├─ Get dimension history
    │  └─ Get speech metrics & trends
    │
    ├─ Check pre-generated cache
    │  └─ If cached → Return instantly
    │
    ├─ Analyze engagement level (response length)
    │
    ├─ Check dimension history:
    │  └─ If same dimension used 2+ times → Force switch
    │
    ▼
Orchestrator.run(prompt)
    │
    ├─ THINK: Analyze user response
    │  ├─ What user said
    │  ├─ Emotional tone
    │  ├─ Response depth
    │  └─ Key themes
    │
    ├─ ANALYZE: Review context
    │  ├─ Previous questions
    │  ├─ Dimensions used (last 2-3)
    │  ├─ Engagement level
    │  └─ Speech performance metrics:
    │     * Clarity trends (improving/declining/stable)
    │     * Pace trends
    │     * Confidence level
    │
    ├─ DECIDE: Select next dimension
    │  ├─ CRITICAL: Check if same dimension used 2+ times
    │  ├─ If yes → Force switch to different dimension
    │  ├─ Avoid recently used dimensions
    │  ├─ Match engagement level
    │  └─ Adapt based on speech performance
    │
    ├─ DECIDE: Adjust difficulty
    │  └─ Based on speech confidence & clarity trends
    │
    ├─ DELEGATE: Instruct Conversation Agent
    │  └─ With dimension, tone matching, complexity adaptation
    │
    ▼
Delegates to Conversation Agent
    │
    ├─ Conversation Agent uses tools:
    │  ├─ get_context → Gather context
    │  └─ generate_followup_question → Generate follow-up
    │     └─ Format: "Ack + preference\n\nQuestion"
    │     └─ Match emotional tone
    │     └─ Build on user's specific mentions
    │
    ▼
Orchestrator returns JSON:
{
  "question": "...",
  "dimension": "...",
  "reasoning": "...",
  "difficulty_level": 1
}
    │
    ▼
API:
    ├─ Parallel: Update previous turn (background)
    ├─ Generate TTS audio (background, 1s max wait)
    ├─ Create database turn
    ├─ Return question + audio (or null if TTS not ready) + turn_id
    │
    ▼
Frontend displays question + auto-plays audio (if available)
    │
    ▼
Background: /api/get_conversation_details
    ├─ Response Agent (parallel)
    │  └─ Generate 2 topic-specific options
    │  └─ Use user's previous response context
    └─ Vocabulary Agent (parallel)
       └─ Generate relevant vocabulary word
```

---

### Flow 3: Speech Analysis & Pre-Generation

```
User Records Audio Response
    │
    ▼
API: /api/process-audio
    │
    ├─ Convert audio format (if needed)
    │
    ▼
Speech Analysis Agent
    │
    ├─ Transcribe audio (OpenAI Whisper)
    │
    ├─ Analyze transcript:
    │  ├─ Calculate WER (if expected response provided)
    │  ├─ Calculate clarity score
    │  ├─ Estimate pace (WPM)
    │  ├─ Identify filler words
    │  └─ Generate feedback
    │
    ▼
Returns JSON:
{
  "transcript": "...",
  "clarity_score": 0.85,
  "pace_wpm": 130,
  "feedback": "...",
  ...
}
    │
    ▼
API:
    ├─ Save speech metrics to database
    ├─ Trigger pre-generation (background):
    │  └─ pre_generate_next_question()
    │     ├─ Fetch context (parallel queries)
    │     ├─ Call orchestrator
    │     ├─ Generate TTS audio
    │     └─ Cache result (5 min TTL)
    │
    └─ Return speech analysis results
    │
    ▼
Frontend:
    ├─ Display speech analysis
    ├─ Poll pre-generation status
    └─ Enable "Continue Chat" when ready (or after 4s)
```

---

### Flow 4: Response Options & Vocabulary Generation

```
Question Displayed
    │
    ▼
API: /api/get_conversation_details (background)
    │
    ├─ Parallel Execution:
    │  │
    │  ├─ Response Agent
    │  │  │
    │  │  ├─ Prompt: "Q: '...' | Topic: gaming | Dim: ... | Level: 1"
    │  │  ├─ If user_response: Include user context
    │  │  │
    │  │  └─ Returns: ["option1", "option2"]
    │  │
    │  └─ Vocabulary Agent
    │     │
    │     ├─ Prompt: "Generate vocabulary for: '...'"
    │     │
    │     └─ Returns: {"word": "...", "type": "...", "definition": "...", "example": "..."}
    │
    ▼
API:
    ├─ Add "Choose your own response" to options
    ├─ Save to database (linked to turn_id)
    └─ Return both to frontend
    │
    ▼
Frontend displays response options + vocabulary
```

---

## Agent Interaction Patterns

### Pattern 1: Orchestrator → Conversation Agent (Question Generation)

```
Orchestrator
    │
    ├─ Analyzes topic, history, speech metrics
    ├─ Selects dimension
    ├─ Adjusts difficulty
    │
    └─ Delegates: "Generate a question about [topic] using [dimension] dimension.
                   The user previously said: [response]. Match their emotional tone.
                   Format: Acknowledgement + personal preference + question."
    │
    ▼
Conversation Agent
    │
    ├─ Uses get_context tool (if follow-up)
    ├─ Uses generate_followup_question tool (if follow-up)
    │  OR
    ├─ Generates initial question directly (if first question)
    │
    └─ Returns: Question text
    │
    ▼
Orchestrator
    │
    └─ Wraps in JSON: {question, dimension, reasoning, difficulty_level}
```

### Pattern 2: Direct Agent Calls (Response & Vocabulary)

```
API Endpoint
    │
    ├─ Response Agent.run(prompt)
    │  └─ Prompt includes: question, topic, dimension, difficulty, user_response
    │  └─ Returns: JSON array ["option1", "option2"]
    │
    └─ Vocabulary Agent.run(prompt)
       └─ Prompt includes: question
       └─ Returns: JSON object {word, type, definition, example}
```

### Pattern 3: Speech Analysis Agent

```
API Endpoint
    │
    ├─ analyze_speech_with_audio()
    │  ├─ Transcribe audio (OpenAI Whisper)
    │  └─ Build prompt with transcript + expected_response
    │
    ▼
Speech Analysis Agent.run(prompt)
    │
    ├─ Analyzes transcript
    ├─ Calculates WER, clarity, pace
    ├─ Identifies filler words
    └─ Generates feedback
    │
    └─ Returns: JSON object {transcript, wer_estimate, clarity_score, ...}
```

---

## Data Flow

### Context Data Passed to Orchestrator

```
┌─────────────────────────────────────────┐
│         Orchestrator Prompt              │
├─────────────────────────────────────────┤
│ Context JSON:                            │
│ {                                        │
│   "topic": "gaming",                     │
│   "prev_q": "...",                       │
│   "user_resp": "...",                    │
│   "diff": 1,                             │
│   "eng": "high",                         │
│   "history": "summary...",                │
│   "dims_used": ["Basic Preferences"],    │
│   "speech": "sp:tr=i,cl=0.88"            │
│ }                                        │
│                                          │
│ Task Instructions:                       │
│ - Analyze response                       │
│ - Select dimension (avoid: ...)          │
│ - Adjust difficulty                      │
│ - Generate question                      │
└─────────────────────────────────────────┘
```

### Speech Performance Feedback Loop

```
Speech Analysis
    │
    ├─ clarity_score: 0.85
    ├─ clarity_trend: "improving"
    ├─ pace_wpm: 130
    ├─ confidence_level: "high"
    │
    ▼
Stored in Database
    │
    ▼
Retrieved for Next Question
    │
    ▼
Included in Orchestrator Prompt
    │
    ├─ "Speech: clarity_trend=improving, clarity_avg=0.85, ..."
    │
    ▼
Orchestrator Decision:
    ├─ If clarity improving → Increase challenge, explore new dimensions
    ├─ If clarity declining → Simplify, use familiar dimensions
    └─ Adjust difficulty based on confidence level
    │
    ▼
Next Question Adapted
```

---

## Dimension Switching Enforcement

```
Dimension History: ["Basic Preferences", "Basic Preferences"]
    │
    ▼
Detection: Same dimension used 2 times
    │
    ▼
Warning Added to Prompt:
    "⚠️ CRITICAL: Last 2 turns used 'Basic Preferences'. 
     You MUST switch to a DIFFERENT dimension now!"
    │
    ▼
Orchestrator Decision:
    └─ MUST select different dimension (e.g., "Social Context")
    │
    ▼
Next Question Uses New Dimension
```

---

## Pre-Generation System

### First Questions (On Login)

```
User Logs In
    │
    ▼
Background Task: pre_generate_all_first_questions()
    │
    ├─ For each topic (gaming, food, hobbies, youtube, weekend):
    │  │
    │  ├─ Wait 2 seconds (rate limit protection)
    │  │
    │  ├─ Call orchestrator
    │  │  └─ Generate first question
    │  │
    │  ├─ Generate TTS audio
    │  │
    │  └─ Cache result (30 min TTL)
    │
    ▼
User Selects Topic
    │
    ├─ Check cache
    │  └─ If found → Return instantly
    │
    └─ If not found → Generate on-demand
```

### Next Questions (After Speech Analysis)

```
Speech Analysis Complete
    │
    ▼
Background Task: pre_generate_next_question()
    │
    ├─ Fetch context (parallel queries)
    │
    ├─ Call orchestrator
    │  └─ Generate follow-up question
    │
    ├─ Generate TTS audio
    │
    └─ Cache result (5 min TTL, key: user_id + topic + previous_turn_id)
    │
    ▼
User Clicks "Continue Chat"
    │
    ├─ Check cache
    │  └─ If found → Return instantly
    │
    └─ If not found → Generate on-demand
```

---

## Error Handling & Resilience

### Rate Limit Handling

```
Orchestrator Call
    │
    ├─ Try: orchestrator.run()
    │  │
    │  ├─ Success → Continue
    │  │
    │  └─ Rate Limit Error
    │     │
    │     ├─ Wait 2s (exponential backoff)
    │     ├─ Retry (max 3 attempts)
    │     │
    │     └─ If still fails:
    │        ├─ User-facing: HTTP 429 with message
    │        └─ Background: Return None, log error
```

### Pre-Generation Failures

```
Pre-Generation Task
    │
    ├─ If fails:
    │  ├─ Log error
    │  ├─ Don't block user flow
    │  └─ Fallback to on-demand generation
    │
    └─ User still gets question (just slower)
```

---

## Key Architectural Principles

1. **Orchestrator-Centric**: All question generation goes through orchestrator for intelligent decisions
2. **Dimension Variety**: Enforced max 2 consecutive turns on same dimension
3. **Speech Feedback Loop**: Speech metrics influence orchestrator decisions
4. **Topic Awareness**: All agents receive topic context for relevant outputs
5. **Pre-Generation**: Background tasks minimize user wait times
6. **Parallel Processing**: Database queries and agent calls run in parallel when possible
7. **Graceful Degradation**: Failures don't block user flow, fallback to on-demand
8. **Rate Limit Resilience**: Automatic retry with exponential backoff

---

## Agent Communication Summary

| Agent | Called By | Input | Output | When |
|-------|-----------|-------|--------|------|
| **Orchestrator** | API endpoints | Topic, history, speech metrics, user response | JSON: {question, dimension, reasoning, difficulty_level} | Every question generation |
| **Conversation Agent** | Orchestrator (delegated) | Topic, dimension, user response, context | Plain text question | When orchestrator delegates |
| **Response Agent** | API endpoint (direct) | Question, topic, dimension, difficulty, user_response | JSON array: ["option1", "option2"] | After question displayed |
| **Vocabulary Agent** | API endpoint (direct) | Question | JSON: {word, type, definition, example} | After question displayed |
| **Speech Analysis Agent** | API endpoint (direct) | Audio file, expected_response | JSON: {transcript, clarity_score, pace_wpm, feedback, ...} | After user records audio |

---

**Last Updated**: 2026-02-17
**Version**: 2.1.0
