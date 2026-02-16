'use client';

import { Bot, Volume2, Mic, BookOpen, Activity, Signal, Wifi, Circle } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

const TOPICS = [
  { id: 'gaming', label: 'Gaming' },
  { id: 'weekend', label: 'Weekend plans' },
  { id: 'hobbies', label: 'Hobbies' },
  { id: 'food', label: 'Food' },
  { id: 'youtube', label: 'YouTube' },
];

export function ChatInterface() {
  const searchParams = useSearchParams();
  const userName = searchParams.get('user') || 'USER';
  const userId = searchParams.get('userId') || userName.toLowerCase().replace(/\s+/g, '_');

  const [currentTopic, setCurrentTopic] = useState<string | null>(null);
  const [question, setQuestion] = useState(""); // Question is managed dynamically
  const [previousQuestion, setPreviousQuestion] = useState<string | null>(null);
  const [welcomeMessage, setWelcomeMessage] = useState({
    line1: `Hi ${userName}! Welcome to ConvoBridge!`,
    line2: "Select a topic to begin the mission."
  });

  // Update welcome message when userName changes
  useEffect(() => {
    setWelcomeMessage({
      line1: `Hi ${userName}! Welcome to ConvoBridge!`,
      line2: "Select a topic to begin the mission."
    });
  }, [userName]);
  const [responses, setResponses] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedResponse, setSelectedResponse] = useState<string | null>(null);

  // Speech Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingStartTimeRef = useRef<number | null>(null);
  const actualRecordingDurationRef = useRef<number>(0);

  // Vocabulary State (Mocked for now until Backend is fully connected)
  const [vocab, setVocab] = useState({
    word: 'Mission',
    type: 'noun',
    definition: 'An important assignment given to a person or group.',
    example: 'Your mission is to choose a topic.'
  });

  // Speech Analysis State
  const [speechAnalysis, setSpeechAnalysis] = useState<{
    transcript: string;
    wer_estimate: number | null;
    clarity_score: number;
    pace_wpm: number;
    filler_words: string[];
    feedback: string;
    strengths: string[];
    suggestions: string[];
  } | null>(null);

  const handleContinueChat = async () => {
    // Clear speech analysis and reset state
    setSpeechAnalysis(null);
    setSelectedResponse(null);
    setIsLoading(true);
    setResponses([]);
    
    // Generate follow-up question based on current topic and user response
    if (!currentTopic || !previousQuestion) return;
    
    // Get user response from selected response or speech transcript
    const userResponse = speechAnalysis?.transcript || selectedResponse || "";
    
    if (!userResponse) {
      console.warn("No user response available for follow-up question");
      setIsLoading(false);
      return;
    }
    
    try {
      // Get follow-up question using continue_conversation endpoint (uses tools)
      const questionRes = await fetch('http://localhost:8000/api/continue_conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: currentTopic,
          user_id: userId,
          previous_question: previousQuestion,
          user_response: userResponse,
          difficulty_level: 1
        })
      });

      if (!questionRes.ok) {
        throw new Error(`API error: ${questionRes.status}`);
      }

      const questionData = await questionRes.json();
      setQuestion(questionData.question);
      setPreviousQuestion(questionData.question); // Store for next follow-up
      setIsLoading(false);

      // Load response options and vocabulary
      try {
        const detailsRes = await fetch('http://localhost:8000/api/get_conversation_details', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            question: questionData.question,
            topic: currentTopic,
            difficulty_level: 1,
            dimension: questionData.dimension || "Basic Preferences"
          })
        });

        if (detailsRes.ok) {
          const detailsData = await detailsRes.json();
          setResponses(detailsData.response_options || []);
          
          if (detailsData.vocabulary) {
            setVocab({
              word: detailsData.vocabulary.word || "Topic",
              type: detailsData.vocabulary.type || "noun",
              definition: detailsData.vocabulary.definition || "A matter dealt with in a text, discourse, or conversation.",
              example: detailsData.vocabulary.example || "That is an interesting topic."
            });
          }
        }
      } catch (detailsError) {
        console.error("Failed to load conversation details", detailsError);
        setResponses([
          "I like that topic.",
          "I'm not sure about that.",
          "Choose your own response"
        ]);
      }
    } catch (error) {
      console.error("Failed to generate follow-up question", error);
      setIsLoading(false);
    }
  };

  const handleTopicSelect = async (topicId: string) => {
    setCurrentTopic(topicId);
    setIsLoading(true);
    setResponses([]); // Clear previous responses
    setQuestion(""); // Clear previous question
    setSpeechAnalysis(null); // Clear any previous speech analysis
    setSelectedResponse(null); // Clear selected response
    
    try {
      // Step 1: Get question immediately using orchestrator (fast endpoint)
      const questionRes = await fetch('http://localhost:8000/api/start_conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
          body: JSON.stringify({
            topic: topicId,
            user_id: userId,
            difficulty_level: 1
          })
      }).catch((fetchError) => {
        // Handle network errors (backend not running, CORS, etc.)
        if (fetchError instanceof TypeError && fetchError.message.includes('fetch')) {
          throw new Error('BACKEND_NOT_RUNNING');
        }
        throw fetchError;
      });

      if (!questionRes.ok) {
        const errorText = await questionRes.text();
        throw new Error(`API error: ${questionRes.status} - ${errorText}`);
      }

      const questionData = await questionRes.json();
      
      // Display question immediately
      setQuestion(questionData.question);
      setPreviousQuestion(questionData.question); // Store for follow-up questions
      setWelcomeMessage({ line1: "", line2: "" });
      setIsLoading(false); // Stop loading spinner - question is shown
      
      // Step 2: Load response options and vocabulary in parallel (background)
      try {
        const detailsRes = await fetch('http://localhost:8000/api/get_conversation_details', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            question: questionData.question,
            topic: topicId,
            difficulty_level: 1,
            dimension: questionData.dimension || "Basic Preferences"
          })
        });

        if (detailsRes.ok) {
          const detailsData = await detailsRes.json();
          
          // Update with response options and vocabulary
          setResponses(detailsData.response_options || []);
          
          if (detailsData.vocabulary) {
            setVocab({
              word: detailsData.vocabulary.word || "Topic",
              type: detailsData.vocabulary.type || "noun",
              definition: detailsData.vocabulary.definition || "A matter dealt with in a text, discourse, or conversation.",
              example: detailsData.vocabulary.example || "That is an interesting topic."
            });
          }
        } else {
          // Fallback if details endpoint fails
          console.warn("Failed to load conversation details, using defaults");
          setResponses([
            "I like that topic.",
            "I'm not sure about that.",
            "Choose your own response"
          ]);
          setVocab({ 
            word: "Topic", 
            type: "noun", 
            definition: "A matter dealt with in a text, discourse, or conversation.", 
            example: "That is an interesting topic." 
          });
        }
      } catch (detailsError) {
        // Non-fatal error - question is already shown
        console.error("Failed to load conversation details", detailsError);
        setResponses([
          "I like that topic.",
          "I'm not sure about that.",
          "Choose your own response"
        ]);
        setVocab({ 
          word: "Topic", 
          type: "noun", 
          definition: "A matter dealt with in a text, discourse, or conversation.", 
          example: "That is an interesting topic." 
        });
      }

    } catch (error) {
      console.error("Failed to fetch conversation", error);
      let errorMessage = "Unknown error occurred";
      
      if (error instanceof Error) {
        if (error.message === 'BACKEND_NOT_RUNNING') {
          errorMessage = "Cannot connect to backend server. Please ensure the backend is running:\n\n1. Open a terminal\n2. Navigate to the backend directory: cd backend\n3. Start the server: python main.py\n\nThe server should run on http://localhost:8000";
        } else if (error.message.includes('fetch') || error.message.includes('Failed to fetch')) {
          errorMessage = "Network error: Cannot reach backend server. Please check:\n\n• Backend server is running (python main.py in backend directory)\n• Server is running on port 8000\n• No firewall blocking the connection";
        } else {
          errorMessage = error.message;
        }
      }
      
      setQuestion(`⚠️ Connection Error\n\n${errorMessage}\n\nPlease start the backend server and try again.`);
      setResponses([]);
      setIsLoading(false);
    }
  };

  // Speech Recording Functions
  const startRecording = async () => {
    try {
      setRecordingError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Calculate actual recording duration
        if (recordingStartTimeRef.current) {
          actualRecordingDurationRef.current = Math.floor((Date.now() - recordingStartTimeRef.current) / 1000);
        }
        
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await handleAudioUpload(audioBlob);
        
        // Cleanup
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
        recordingStartTimeRef.current = null;
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      recordingStartTimeRef.current = Date.now();
      actualRecordingDurationRef.current = 0;

      // Start timer
      timerIntervalRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          const newTime = prev + 1;
          // Auto-stop after 15 seconds
          if (newTime >= 15) {
            stopRecording();
          }
          return newTime;
        });
      }, 1000);

    } catch (error: any) {
      console.error("Error starting recording:", error);
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        setRecordingError("Microphone permission denied. Please allow microphone access.");
      } else {
        setRecordingError("Failed to start recording. Please try again.");
      }
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      // Calculate actual duration before stopping
      if (recordingStartTimeRef.current) {
        actualRecordingDurationRef.current = Math.floor((Date.now() - recordingStartTimeRef.current) / 1000);
      }
      
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }
    }
  };

  const handleAudioUpload = async (audioBlob: Blob) => {
    // Validate recording length using actual duration
    const duration = actualRecordingDurationRef.current || recordingTime;
    
    if (duration < 1) {
      setRecordingError("Recording too short. Please record for at least 1 second.");
      setRecordingTime(0);
      actualRecordingDurationRef.current = 0;
      return;
    }

    setIsUploading(true);
    setRecordingError(null);

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      
      // Include expected response if a response option was selected
      if (selectedResponse && selectedResponse !== "Choose your own response") {
        formData.append('expected_response', selectedResponse);
      }

      const response = await fetch('http://localhost:8000/api/process-audio', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = 'Failed to process audio';
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorMessage;
        } catch {
          errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('Audio processed:', result);
      
      // Store speech analysis results
      if (result.transcript) {
        setSpeechAnalysis({
          transcript: result.transcript || '',
          wer_estimate: result.wer_estimate ?? null,
          clarity_score: result.clarity_score ?? 0,
          pace_wpm: result.pace_wpm ?? 0,
          filler_words: result.filler_words || [],
          feedback: result.feedback || '',
          strengths: result.strengths || [],
          suggestions: result.suggestions || []
        });
      }
      
      // Reset timer and clear error on success
      setRecordingTime(0);
      actualRecordingDurationRef.current = 0;
      setRecordingError(null);
      
    } catch (error: any) {
      console.error("Error uploading audio:", error);
      const errorMessage = error.message || "Failed to upload audio. Please try again.";
      setRecordingError(errorMessage);
      
      // Check if it's a network error (backend not running)
      if (error.message?.includes('fetch') || error.message?.includes('Failed to fetch')) {
        setRecordingError("Cannot connect to server. Please ensure the backend is running on port 8000.");
      }
    } finally {
      setIsUploading(false);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Format time as MM:SS
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full h-full px-8 pt-24 pb-8 grid grid-cols-1 md:grid-cols-12 gap-8 relative min-h-screen">
      
      {/* Left Panel: Topics - Wider & Taller with Glowing Outline */}
      <div className="md:col-span-3 flex flex-col">
        <div className="h-full min-h-[600px] p-6 rounded-2xl bg-black/40 backdrop-blur-xl border border-copper shadow-[0_0_20px_rgba(255,107,53,0.3)] hover:shadow-[0_0_30px_rgba(255,107,53,0.5)] transition-all duration-300 flex flex-col">
          <h3 className="text-copper font-mono text-sm tracking-widest uppercase mb-6 border-b border-white/10 pb-4">Select Topic</h3>
          <div className="flex flex-col gap-4 flex-grow">
            {TOPICS.map((topic) => (
              <button 
                key={topic.id}
                onClick={() => handleTopicSelect(topic.id)}
                className={`w-full text-left px-5 py-4 rounded-xl border transition-all duration-300 font-medium text-lg relative overflow-hidden group ${
                  currentTopic === topic.id 
                    ? 'bg-copper/20 border-copper text-white shadow-[0_0_15px_rgba(255,107,53,0.4)]' 
                    : 'bg-white/5 border-white/10 text-gray-300 hover:bg-copper/10 hover:border-copper hover:text-white'
                }`}
              >
                <div className="relative z-10 flex items-center justify-between">
                  {topic.label}
                  {currentTopic === topic.id && <Activity className="w-4 h-4 text-cyan animate-pulse" />}
                </div>
                {/* Active Indicator Bar */}
                {currentTopic === topic.id && <div className="absolute left-0 top-0 h-full w-1 bg-cyan"></div>}
              </button>
            ))}
          </div>

          {/* System Status */}
          <div className="mt-auto pt-6 border-t border-white/10 flex flex-col gap-4 opacity-70">
             <div className="text-xs font-mono text-gray-500 uppercase tracking-widest mb-2">System Status</div>
             
             {/* Fake Data Visualization 1 */}
             <div className="flex items-center justify-between text-xs text-gray-400 font-mono">
                <span className="flex items-center gap-2"><Activity className="w-3 h-3 text-cyan" /> Neural Link</span>
                <span className="text-cyan animate-pulse">ACTIVE</span>
             </div>
             <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                <div className="h-full w-3/4 bg-cyan/50 rounded-full animate-pulse"></div>
             </div>

             {/* Fake Data Visualization 2 */}
             <div className="flex items-center justify-between text-xs text-gray-400 font-mono">
                <span className="flex items-center gap-2"><Signal className="w-3 h-3 text-copper" /> Voice Uplink</span>
                <span className="text-copper">STABLE</span>
             </div>
             <div className="flex gap-1 h-3 items-end">
                {[1,2,3,4,5,4,3,2,5,3,4,2].map((h, i) => (
                    <div key={i} className="w-1 bg-copper/40 rounded-sm animate-pulse" style={{ height: `${h * 20}%`, animationDelay: `${i * 0.1}s` }}></div>
                ))}
             </div>

             {/* Connection Info */}
             <div className="flex items-center gap-2 text-[10px] text-gray-600 font-mono mt-2">
                <Wifi className="w-3 h-3" />
                <span>ID: {userName}-007 // ENCRYPTED</span>
             </div>
          </div>

        </div>
      </div>

      {/* Main Content Area */}
      <div className="md:col-span-9 flex flex-col h-full gap-8 relative">
        
        {/* Top Section: Robot + Question */}
        <div className="flex flex-col md:flex-row items-start gap-8 mt-4">
          
          {/* Robot Avatar */}
          <div className="flex-shrink-0 w-48 h-48 rounded-2xl bg-black/40 backdrop-blur-xl border border-copper/40 flex items-center justify-center shadow-[0_0_40px_rgba(255,107,53,0.1)] relative group">
             <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,11,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-0 bg-[length:100%_4px,6px_100%] pointer-events-none rounded-2xl"></div>
             <Bot className={`w-24 h-24 text-copper group-hover:text-cyan transition-colors duration-500 drop-shadow-[0_0_20px_rgba(255,107,53,0.6)] ${isLoading ? 'animate-pulse' : 'animate-float'}`} />
          </div>

          {/* Question Panel */}
          <div className="relative mt-6 max-w-2xl w-full">
             <div className="absolute top-6 -left-3 w-6 h-6 bg-black/60 border-l border-b border-cyan/30 transform rotate-45 z-0 hidden md:block"></div>
             
             <div className="relative z-10 p-6 rounded-2xl rounded-tl-none bg-black/60 backdrop-blur-xl border border-cyan/30 shadow-[0_0_30px_rgba(0,229,255,0.15)] flex flex-col gap-3 min-h-[150px]">
                <div className="flex justify-between items-start">
                    <span className="text-cyan font-mono text-xs tracking-widest uppercase mb-2">Agent Message</span>
                    <button className="p-1.5 rounded-full hover:bg-white/10 text-cyan transition-colors">
                      <Volume2 className="w-4 h-4" />
                    </button>
                </div>
                
                {isLoading ? (
                  <div className="flex items-center gap-2 text-copper animate-pulse mt-2">
                    <span className="w-2 h-2 bg-copper rounded-full"></span>
                    <span className="w-2 h-2 bg-copper rounded-full animation-delay-200"></span>
                    <span className="w-2 h-2 bg-copper rounded-full animation-delay-400"></span>
                    <span className="font-mono text-sm uppercase">Processing Input...</span>
                  </div>
                ) : (
                  <div className="text-lg md:text-xl text-white font-light leading-relaxed animate-in fade-in slide-in-from-bottom-2 duration-500">
                    {welcomeMessage.line1 ? (
                      <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-2">
                           <span>{welcomeMessage.line1}</span>
                           <Activity className="w-5 h-5 text-cyan animate-pulse" />
                        </div>
                        <span className="text-gray-300 text-base">{welcomeMessage.line2}</span>
                      </div>
                    ) : (
                      `"${question}"`
                    )}
                  </div>
                )}
             </div>
          </div>
        </div>

        {/* Speech Analysis Feedback Window */}
        {speechAnalysis && (
          <div className="w-full max-w-4xl flex flex-col gap-6 mt-8">
            <div className="p-6 rounded-2xl bg-black/60 backdrop-blur-xl border border-cyan/30 shadow-[0_0_40px_rgba(0,229,255,0.2)] animate-in fade-in slide-in-from-bottom-4">
              <div className="flex items-center justify-between mb-4 pb-4 border-b border-white/10">
                <h3 className="text-cyan font-mono text-sm tracking-widest uppercase">Speech Analysis Feedback</h3>
              </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left Column: Metrics */}
              <div className="flex flex-col gap-4">
                {/* Transcript */}
                <div>
                  <h4 className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-2">Transcript</h4>
                  <p className="text-white text-sm bg-white/5 p-3 rounded-lg border border-white/10 italic">
                    "{speechAnalysis.transcript}"
                  </p>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 gap-3">
                  {/* Clarity Score */}
                  <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                    <div className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-1">Clarity</div>
                    <div className="text-2xl font-bold text-cyan">
                      {Math.round(speechAnalysis.clarity_score * 100)}%
                    </div>
                    <div className="w-full h-2 bg-white/10 rounded-full mt-2 overflow-hidden">
                      <div 
                        className="h-full bg-cyan rounded-full transition-all duration-500"
                        style={{ width: `${speechAnalysis.clarity_score * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Pace */}
                  <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                    <div className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-1">Pace</div>
                    <div className="text-2xl font-bold text-copper">
                      {speechAnalysis.pace_wpm}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">words/min</div>
                  </div>
                </div>

                {/* WER Estimate (if available) */}
                {speechAnalysis.wer_estimate !== null && (
                  <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                    <div className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-1">Word Error Rate</div>
                    <div className="text-xl font-bold text-white">
                      {(speechAnalysis.wer_estimate * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-400 mt-1">Lower is better</div>
                  </div>
                )}

                {/* Filler Words */}
                {speechAnalysis.filler_words.length > 0 && (
                  <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                    <div className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-2">Filler Words</div>
                    <div className="flex flex-wrap gap-2">
                      {speechAnalysis.filler_words.map((word, i) => (
                        <span key={i} className="px-2 py-1 rounded bg-copper/20 text-copper text-xs font-mono">
                          {word}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column: Feedback */}
              <div className="flex flex-col gap-4">
                {/* Feedback Message */}
                <div>
                  <h4 className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-2">Feedback</h4>
                  <p className="text-white text-sm bg-cyan/10 p-4 rounded-lg border border-cyan/30 leading-relaxed">
                    {speechAnalysis.feedback}
                  </p>
                </div>

                {/* Strengths */}
                {speechAnalysis.strengths.length > 0 && (
                  <div>
                    <h4 className="text-xs font-mono text-cyan uppercase tracking-widest mb-2 flex items-center gap-2">
                      <span className="w-2 h-2 bg-cyan rounded-full"></span>
                      Strengths
                    </h4>
                    <ul className="space-y-2">
                      {speechAnalysis.strengths.map((strength, i) => (
                        <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                          <span className="text-cyan mt-1">✓</span>
                          <span>{strength}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Suggestions */}
                {speechAnalysis.suggestions.length > 0 && (
                  <div>
                    <h4 className="text-xs font-mono text-copper uppercase tracking-widest mb-2 flex items-center gap-2">
                      <span className="w-2 h-2 bg-copper rounded-full"></span>
                      Suggestions
                    </h4>
                    <ul className="space-y-2">
                      {speechAnalysis.suggestions.map((suggestion, i) => (
                        <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                          <span className="text-copper mt-1">→</span>
                          <span>{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
            </div>

            {/* Continue Chat Button */}
            <button
              onClick={handleContinueChat}
              className="w-full max-w-md mx-auto px-8 py-4 rounded-xl bg-copper/20 border-2 border-copper text-white font-bold text-lg hover:bg-copper/30 hover:border-copper hover:shadow-[0_0_30px_rgba(255,107,53,0.6)] transition-all duration-300 flex items-center justify-center gap-3 group"
            >
              <span>Continue Chat</span>
              <Activity className="w-5 h-5 group-hover:animate-pulse" />
            </button>
          </div>
        )}

        {/* Response Options - Hidden when speech analysis is displayed */}
        {!speechAnalysis && (
          <div className="w-full max-w-3xl flex flex-col gap-4 mt-8">
            {isLoading ? (
               // Loading Skeletons
               [1, 2, 3].map((i) => (
                 <div key={i} className="h-16 w-full rounded-xl bg-white/5 animate-pulse border border-white/5"></div>
               ))
            ) : responses.length > 0 ? (
               responses.map((res, i) => (
                <div 
                  key={i} 
                  onClick={() => setSelectedResponse(res === "Choose your own response" ? null : res)}
                  className={`group relative p-4 rounded-xl border transition-all duration-300 flex items-center cursor-pointer animate-in fade-in slide-in-from-bottom-4 ${
                    selectedResponse === res
                      ? 'bg-copper/20 border-copper text-white shadow-[0_0_15px_rgba(255,107,53,0.4)]'
                      : 'bg-white/5 border-white/10 text-gray-300 hover:border-copper hover:bg-copper/5 hover:text-white'
                  }`}
                  style={{ animationDelay: `${i * 100}ms` }}
                >
                    <span className="text-base">{res}</span>
                    {selectedResponse === res && (
                      <span className="ml-auto text-cyan">✓</span>
                    )}
                </div>
               ))
            ) : (
              <div className="text-center text-gray-500 font-mono text-sm py-8">Select a topic to generate responses...</div>
            )}
          </div>
        )}

        {/* Speech Recording Component - Hidden when speech analysis is displayed */}
        {responses.length > 0 && !speechAnalysis && (
          <div className="w-full max-w-3xl flex flex-col items-center gap-4 mt-6">
            {/* Error Message */}
            {recordingError && (
              <div className="w-full p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-mono animate-in fade-in slide-in-from-top-2">
                {recordingError}
              </div>
            )}

            {/* Recording Timer */}
            {isRecording && (
              <div className="text-2xl font-mono font-bold text-cyan drop-shadow-[0_0_10px_rgba(0,229,255,0.6)] animate-pulse">
                {formatTime(recordingTime)}
              </div>
            )}

            {/* Record Button */}
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isUploading}
              className={`relative w-24 h-24 md:w-28 md:h-28 rounded-full flex items-center justify-center transition-all duration-300 ${
                isRecording
                  ? 'bg-red-500/20 border-2 border-red-500 shadow-[0_0_30px_rgba(239,68,68,0.6)] animate-pulse'
                  : 'bg-green-500/20 border-2 border-green-500 hover:bg-green-500/30 hover:shadow-[0_0_30px_rgba(34,197,94,0.6)]'
              } ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              {isRecording ? (
                <>
                  {/* Pulsing Circle Animation */}
                  <Circle className="absolute w-full h-full text-red-500 animate-ping opacity-75" />
                  <div className="relative z-10 w-8 h-8 md:w-10 md:h-10 rounded bg-red-500"></div>
                </>
              ) : (
                <Mic className="w-10 h-10 md:w-12 md:h-12 text-green-400" />
              )}
            </button>

            {/* Button Label */}
            <span className="text-sm font-mono text-gray-400 uppercase tracking-widest">
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </span>

            {/* Uploading Indicator */}
            {isUploading && (
              <div className="flex items-center gap-2 text-cyan animate-pulse">
                <Activity className="w-4 h-4" />
                <span className="text-sm font-mono uppercase">Processing Audio...</span>
              </div>
            )}
          </div>
        )}

        {/* Vocabulary Window */}
        <div className={`md:fixed md:bottom-4 md:right-8 w-full md:w-80 p-6 rounded-2xl bg-black/80 backdrop-blur-xl border border-copper/30 shadow-[0_0_40px_rgba(0,0,0,0.8)] flex flex-col gap-4 z-50 mt-8 md:mt-0 transition-all duration-500 hover:border-copper/60 ${isLoading ? 'opacity-50 blur-sm pointer-events-none' : 'opacity-100'}`}>
            <div className="flex items-center gap-2 text-copper border-b border-white/10 pb-2">
                <BookOpen className="w-5 h-5" />
                <h3 className="font-mono text-sm tracking-widest uppercase">Vocabulary</h3>
            </div>
            
            <div>
                <h4 className="text-2xl font-bold text-white mb-1">{vocab.word}</h4>
                <p className="text-sm text-gray-400 italic mb-3">{vocab.type} • /.../</p>
                <p className="text-gray-300 text-sm mb-4">{vocab.definition}</p>
                
                <div className="p-3 rounded-lg bg-white/5 border border-white/5 text-sm text-gray-300 italic border-l-2 border-l-cyan">
                "{vocab.example}"
                </div>

                <button className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-copper/10 border border-copper/30 text-copper hover:bg-copper/20 hover:border-copper hover:text-white hover:shadow-[0_0_15px_rgba(255,107,53,0.2)] transition-all duration-300 group">
                    <Volume2 className="w-4 h-4 group-hover:scale-110 transition-transform" />
                    <span className="text-xs font-bold tracking-widest uppercase">Hear me say</span>
                </button>
            </div>
        </div>

      </div>
    </div>
  );
}
