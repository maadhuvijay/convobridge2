'use client';

import { Bot, Volume2, Mic, BookOpen, Activity, Signal, Wifi, Circle, Star, Sparkles, Trophy } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

const TOPICS = [
  { id: 'gaming', label: 'Gaming' },
  { id: 'weekend', label: 'Weekend plans' },
  { id: 'hobbies', label: 'Hobbies' },
  { id: 'food', label: 'Food' },
  { id: 'youtube', label: 'YouTube' },
];

export function ChatInterface() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const userName = searchParams.get('user') || 'USER';
  const userId = searchParams.get('userId') || userName.toLowerCase().replace(/\s+/g, '_');
  const sessionId = searchParams.get('sessionId') || null; // Get session_id from URL

  // Check if sessionId is missing and redirect to login
  useEffect(() => {
    const currentSessionId = searchParams.get('sessionId');
    if (!currentSessionId) {
      console.warn('No sessionId found in URL. Redirecting to login...');
      console.log('Current URL params:', {
        user: searchParams.get('user'),
        userId: searchParams.get('userId'),
        sessionId: searchParams.get('sessionId'),
        all: Array.from(searchParams.entries())
      });
      // Redirect to login immediately
      router.push('/login');
    }
  }, [router, searchParams]);

  const [currentTopic, setCurrentTopic] = useState<string | null>(null);
  const [question, setQuestion] = useState(""); // Question is managed dynamically
  const [previousQuestion, setPreviousQuestion] = useState<string | null>(null);
  const [currentTurnId, setCurrentTurnId] = useState<string | null>(null); // Track current conversation turn ID
  const [previousTurnId, setPreviousTurnId] = useState<string | null>(null); // Track previous turn ID for continue conversation
  const [questionAudio, setQuestionAudio] = useState<string | null>(null); // Base64 audio for current question
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isPlayingVocabAudio, setIsPlayingVocabAudio] = useState(false);
  const [vocabHeard, setVocabHeard] = useState(false); // Track if vocabulary has been heard
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const vocabAudioRef = useRef<HTMLAudioElement | null>(null);
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

  // Function to play audio from base64
  const playAudio = async (audioBase64: string) => {
    try {
      setIsPlayingAudio(true);
      
      // Convert base64 to blob
      const audioData = atob(audioBase64);
      const audioBytes = new Uint8Array(audioData.length);
      for (let i = 0; i < audioData.length; i++) {
        audioBytes[i] = audioData.charCodeAt(i);
      }
      const audioBlob = new Blob([audioBytes], { type: 'audio/mp3' });
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // Create and play audio
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      
      audio.onended = () => {
        setIsPlayingAudio(false);
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.onerror = () => {
        setIsPlayingAudio(false);
        URL.revokeObjectURL(audioUrl);
        console.error("Error playing audio");
      };
      
      await audio.play();
    } catch (error) {
      console.error("Error playing audio:", error);
      setIsPlayingAudio(false);
    }
  };

  // Function to handle listen button click
  const handleListenClick = async () => {
    if (questionAudio) {
      // Play existing audio
      await playAudio(questionAudio);
    } else if (question) {
      // Generate new audio
      try {
        const response = await fetch('http://localhost:8000/api/text_to_speech', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: question,
            voice: 'nova',
            model: 'tts-1-hd',
            format: 'mp3'
          })
        });

        if (!response.ok) {
          throw new Error(`Failed to generate audio: ${response.status}`);
        }

        const data = await response.json();
        setQuestionAudio(data.audio_base64);
        await playAudio(data.audio_base64);
      } catch (error) {
        console.error("Error generating audio:", error);
      }
    }
  };

  // Function to play vocabulary audio from base64
  const playVocabAudio = async (audioBase64: string) => {
    try {
      setIsPlayingVocabAudio(true);
      
      // Convert base64 to blob
      const audioData = atob(audioBase64);
      const audioBytes = new Uint8Array(audioData.length);
      for (let i = 0; i < audioData.length; i++) {
        audioBytes[i] = audioData.charCodeAt(i);
      }
      const audioBlob = new Blob([audioBytes], { type: 'audio/mp3' });
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // Create and play audio
      const audio = new Audio(audioUrl);
      vocabAudioRef.current = audio;
      
      audio.onended = () => {
        setIsPlayingVocabAudio(false);
        setVocabHeard(true); // Mark vocabulary as heard when audio finishes
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.onerror = () => {
        setIsPlayingVocabAudio(false);
        URL.revokeObjectURL(audioUrl);
        console.error("Error playing vocabulary audio");
      };
      
      await audio.play();
    } catch (error) {
      console.error("Error playing vocabulary audio:", error);
      setIsPlayingVocabAudio(false);
    }
  };

  // Function to handle vocabulary "Hear me say" button click
  const handleVocabListenClick = async () => {
    if (!vocab.word || !vocab.definition) return;
    
    // Award 10 points for clicking "Hear me say"
    setBrowniePoints(prev => {
      const newTotal = prev + 10;
      localStorage.setItem(`browniePoints_${userId}`, newTotal.toString());
      return newTotal;
    });
    setHearMeSayPointsAnimation(true);
    setTimeout(() => {
      setHearMeSayPointsAnimation(false);
    }, 1500);
    
    // Combine word and definition for TTS
    const vocabText = `${vocab.word}. ${vocab.definition}`;
    
    try {
      const response = await fetch('http://localhost:8000/api/text_to_speech', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: vocabText,
          voice: 'nova',
          model: 'tts-1-hd',
          format: 'mp3'
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to generate audio: ${response.status}`);
      }

      const data = await response.json();
      await playVocabAudio(data.audio_base64);
    } catch (error) {
      console.error("Error generating vocabulary audio:", error);
    }
  };

  // Auto-play audio when question is received
  useEffect(() => {
    if (questionAudio && question) {
      // Auto-play when new question audio is available
      playAudio(questionAudio).catch(console.error);
    }
    
    // Cleanup audio on unmount or when question changes
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [questionAudio]); // Only depend on questionAudio, question is checked inside
  const [responses, setResponses] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedResponse, setSelectedResponse] = useState<string | null>(null);

  // Brownie Points State
  const [browniePoints, setBrowniePoints] = useState<number>(0);
  const [pointsAnimation, setPointsAnimation] = useState<boolean>(false);
  const [lastPointsAwarded, setLastPointsAwarded] = useState<number>(0);
  const [clarityPointsAnimation, setClarityPointsAnimation] = useState<boolean>(false);
  const [continueChatPointsAnimation, setContinueChatPointsAnimation] = useState<boolean>(false);
  const [hearMeSayPointsAnimation, setHearMeSayPointsAnimation] = useState<boolean>(false);
  const [vocabPracticePointsAnimation, setVocabPracticePointsAnimation] = useState<boolean>(false);
  
  // Vocabulary Practice State
  const [isPracticingVocab, setIsPracticingVocab] = useState(false);
  const [vocabPracticeTime, setVocabPracticeTime] = useState(0);
  const [vocabPracticeError, setVocabPracticeError] = useState<string | null>(null);
  const [isUploadingVocabPractice, setIsUploadingVocabPractice] = useState(false);
  const [vocabRephrasedSentence, setVocabRephrasedSentence] = useState<string>("");
  const [userRephrasedSentence, setUserRephrasedSentence] = useState<string>("");
  const vocabPracticeMediaRecorderRef = useRef<MediaRecorder | null>(null);
  const vocabPracticeAudioChunksRef = useRef<Blob[]>([]);
  const vocabPracticeTimerIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const vocabPracticeStreamRef = useRef<MediaStream | null>(null);
  const vocabPracticeStartTimeRef = useRef<number | null>(null);
  const vocabPracticeDurationRef = useRef<number>(0);

  // Function to award brownie points
  const awardBrowniePoints = (points: number) => {
    setBrowniePoints(prev => {
      const newTotal = prev + points;
      localStorage.setItem(`browniePoints_${userId}`, newTotal.toString());
      return newTotal;
    });
    setLastPointsAwarded(points);
    setPointsAnimation(true);
    setTimeout(() => {
      setPointsAnimation(false);
      setLastPointsAwarded(0);
    }, 1000);
  };


  // Load points from localStorage on mount
  useEffect(() => {
    const savedPoints = localStorage.getItem(`browniePoints_${userId}`);
    if (savedPoints) {
      setBrowniePoints(parseInt(savedPoints, 10));
    }
  }, [userId]);

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

  // Function to generate rephrased sentence using vocabulary word
  const generateRephrasedSentence = (transcript: string, vocabWord: string): string => {
    // Simple rephrasing: try to incorporate the vocabulary word into the transcript
    // This is a basic implementation - could be enhanced with AI/backend
    const transcriptLower = transcript.toLowerCase();
    const vocabLower = vocabWord.toLowerCase();
    
    // Try to find a similar word to replace, or add the vocab word naturally
    // For now, create a simple rephrased version
    if (transcriptLower.includes('like to')) {
      return transcript.replace(/like to/gi, `like to use ${vocabWord} for`);
    } else if (transcriptLower.includes('like')) {
      return transcript.replace(/like/gi, `like ${vocabWord}`);
    } else if (transcriptLower.includes('enjoy')) {
      return transcript.replace(/enjoy/gi, `enjoy ${vocabWord}`);
    } else if (transcriptLower.includes('love')) {
      return transcript.replace(/love/gi, `love ${vocabWord}`);
    } else {
      // Default: incorporate vocab word naturally
      // Try to add it after the first verb or at a natural position
      const words = transcript.split(' ');
      if (words.length > 2) {
        // Insert vocab word after first few words
        return `${words.slice(0, 2).join(' ')} ${vocabWord} ${words.slice(2).join(' ')}`;
      } else {
        return `${transcript} using ${vocabWord}`;
      }
    }
  };

  const handleContinueChat = async () => {
    // Get user response from selected response or speech transcript BEFORE clearing state
    const userResponse = speechAnalysis?.transcript || selectedResponse || "";
    
    // Award 5 points for continuing the chat
    setBrowniePoints(prev => {
      const newTotal = prev + 5;
      localStorage.setItem(`browniePoints_${userId}`, newTotal.toString());
      return newTotal;
    });
    setContinueChatPointsAnimation(true);
    setTimeout(() => {
      setContinueChatPointsAnimation(false);
    }, 1500);
    
    // Award additional 5 points for continuing ONLY if clarity was 100%
    // Note: Bonus 5 points for 100% clarity are already awarded when speech analysis is displayed
    if (speechAnalysis && speechAnalysis.clarity_score === 1.0) {
      console.log('Continuing chat with 100% clarity - awarded 5 brownie points for continuing (total 10 including clarity bonus)');
    } else {
      console.log('Continuing chat - awarded 5 brownie points');
    }
    
    // Set loading state and clear responses before API call
    setIsLoading(true);
    setResponses([]);
    
    // Delay clearing speech analysis to allow animation to be visible
    setTimeout(() => {
      setSpeechAnalysis(null);
      setSelectedResponse(null);
    }, 500); // Delay to ensure animation is visible before unmounting
    
    // Generate follow-up question based on current topic and user response
    if (!currentTopic || !previousQuestion) {
      setIsLoading(false);
      return;
    }
    
    if (!userResponse) {
      console.warn("No user response available for follow-up question");
      setIsLoading(false);
      return;
    }
    
    // Get sessionId from URL params (in case it wasn't captured initially)
    const effectiveSessionId = sessionId || searchParams.get('sessionId');
    
    if (!effectiveSessionId) {
      console.error("Session ID is required for continuing conversation");
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
          session_id: effectiveSessionId, // Pass session_id
          previous_question: previousQuestion,
          previous_turn_id: previousTurnId, // Pass previous turn_id to update with user response
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
      setQuestionAudio(questionData.audio_base64 || null); // Store audio for playback
      setPreviousTurnId(currentTurnId); // Store current turn as previous for next iteration
      setCurrentTurnId(questionData.turn_id || null); // Store new turn_id
      setIsLoading(false);

      // Load response options and vocabulary
      // Only if turn_id is available
      if (questionData.turn_id) {
        try {
          const detailsRes = await fetch('http://localhost:8000/api/get_conversation_details', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              question: questionData.question,
              topic: currentTopic,
              turn_id: questionData.turn_id, // Pass turn_id to save response options and vocabulary
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
          } else {
            // Fallback if details endpoint fails
            console.warn("Failed to load conversation details, using defaults");
            setResponses([
              "I like that topic.",
              "I'm not sure about that.",
              "Choose your own response"
            ]);
          }
        } catch (detailsError) {
          console.error("Failed to load conversation details", detailsError);
          setResponses([
            "I like that topic.",
            "I'm not sure about that.",
            "Choose your own response"
          ]);
        }
      } else {
        // Fallback if no turn_id
        console.warn("No turn_id available, using default response options");
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
    setQuestionAudio(null); // Clear previous audio
    setSpeechAnalysis(null); // Clear any previous speech analysis
    setSelectedResponse(null); // Clear selected response
    
    try {
      // Step 1: Get question immediately using orchestrator (fast endpoint)
      // Get sessionId from URL params (in case it wasn't captured initially)
      const effectiveSessionId = sessionId || searchParams.get('sessionId');
      
      if (!effectiveSessionId) {
        console.error('Session ID missing. URL params:', {
          user: userName,
          userId: userId,
          sessionId: sessionId,
          allParams: Array.from(searchParams.entries())
        });
        // Redirect to login
        router.push('/login');
        setIsLoading(false);
        return;
      }
      
      const questionRes = await fetch('http://localhost:8000/api/start_conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
          body: JSON.stringify({
            topic: topicId,
            user_id: userId,
            session_id: effectiveSessionId,
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
      setQuestionAudio(questionData.audio_base64 || null); // Store audio for playback
      setCurrentTurnId(questionData.turn_id || null); // Store turn_id for linking response options/vocabulary
      setWelcomeMessage({ line1: "", line2: "" });
      setIsLoading(false); // Stop loading spinner - question is shown
      
      // Step 2: Load response options and vocabulary in parallel (background)
      // Only if turn_id is available
      if (questionData.turn_id) {
        try {
          const detailsRes = await fetch('http://localhost:8000/api/get_conversation_details', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              question: questionData.question,
              topic: topicId,
              turn_id: questionData.turn_id, // Pass turn_id to save response options and vocabulary
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
      } else {
        // Fallback if no turn_id
        console.warn("No turn_id available, using default response options");
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
      
      // Include turn_id to save speech analysis
      if (currentTurnId) {
        formData.append('turn_id', currentTurnId);
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
        const clarityScore = result.clarity_score ?? 0;
        setSpeechAnalysis({
          transcript: result.transcript || '',
          wer_estimate: result.wer_estimate ?? null,
          clarity_score: clarityScore,
          pace_wpm: result.pace_wpm ?? 0,
          filler_words: result.filler_words || [],
          feedback: result.feedback || '',
          strengths: result.strengths || [],
          suggestions: result.suggestions || []
        });
        // Reset vocabHeard when new speech analysis appears
        setVocabHeard(false);
        // Reset user rephrased sentence when new speech analysis appears
        setUserRephrasedSentence("");
        // Generate rephrased sentence for vocabulary bonus challenge (as suggestion)
        if (result.transcript && vocab.word) {
          const rephrased = generateRephrasedSentence(result.transcript, vocab.word);
          setVocabRephrasedSentence(rephrased);
        }
        
        // Award +10 bonus points immediately if clarity is 100%
        if (clarityScore === 1.0) {
          console.log('Perfect clarity (100%) - awarding bonus 10 brownie points immediately!');
          // Award points but show animation near clarity score
          setBrowniePoints(prev => {
            const newTotal = prev + 10;
            localStorage.setItem(`browniePoints_${userId}`, newTotal.toString());
            return newTotal;
          });
          // Show animation near clarity score
          setClarityPointsAnimation(true);
          setTimeout(() => {
            setClarityPointsAnimation(false);
          }, 1500);
        }
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

  // Vocabulary Practice Recording Functions
  const startVocabPractice = async () => {
    try {
      setVocabPracticeError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      vocabPracticeStreamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      vocabPracticeMediaRecorderRef.current = mediaRecorder;
      vocabPracticeAudioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          vocabPracticeAudioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Calculate actual recording duration
        if (vocabPracticeStartTimeRef.current) {
          vocabPracticeDurationRef.current = Math.floor((Date.now() - vocabPracticeStartTimeRef.current) / 1000);
        }
        
        const audioBlob = new Blob(vocabPracticeAudioChunksRef.current, { type: 'audio/webm' });
        await handleVocabPracticeUpload(audioBlob);
        
        // Cleanup
        if (vocabPracticeStreamRef.current) {
          vocabPracticeStreamRef.current.getTracks().forEach(track => track.stop());
          vocabPracticeStreamRef.current = null;
        }
        vocabPracticeStartTimeRef.current = null;
      };

      mediaRecorder.start();
      setIsPracticingVocab(true);
      setVocabPracticeTime(0);
      vocabPracticeStartTimeRef.current = Date.now();
      vocabPracticeDurationRef.current = 0;

      // Start timer
      vocabPracticeTimerIntervalRef.current = setInterval(() => {
        setVocabPracticeTime((prev) => {
          const newTime = prev + 1;
          // Auto-stop after 15 seconds
          if (newTime >= 15) {
            stopVocabPractice();
          }
          return newTime;
        });
      }, 1000);

    } catch (error: any) {
      console.error("Error starting vocabulary practice:", error);
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        setVocabPracticeError("Microphone permission denied. Please allow microphone access.");
      } else {
        setVocabPracticeError("Failed to start recording. Please try again.");
      }
      setIsPracticingVocab(false);
    }
  };

  const stopVocabPractice = () => {
    if (vocabPracticeMediaRecorderRef.current && isPracticingVocab) {
      // Calculate actual duration before stopping
      if (vocabPracticeStartTimeRef.current) {
        vocabPracticeDurationRef.current = Math.floor((Date.now() - vocabPracticeStartTimeRef.current) / 1000);
      }
      
      vocabPracticeMediaRecorderRef.current.stop();
      setIsPracticingVocab(false);
      
      if (vocabPracticeTimerIntervalRef.current) {
        clearInterval(vocabPracticeTimerIntervalRef.current);
        vocabPracticeTimerIntervalRef.current = null;
      }
    }
  };

  const handleVocabPracticeUpload = async (audioBlob: Blob) => {
    // Validate recording length
    const duration = vocabPracticeDurationRef.current || vocabPracticeTime;
    
    if (duration < 1) {
      setVocabPracticeError("Recording too short. Please record for at least 1 second.");
      setVocabPracticeTime(0);
      vocabPracticeDurationRef.current = 0;
      return;
    }

    setIsUploadingVocabPractice(true);
    setVocabPracticeError(null);

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'vocab_practice.webm');
      
      // Include expected sentence (use vocabulary example sentence)
      if (vocab.example) {
        formData.append('expected_response', vocab.example);
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
      console.log('Vocabulary practice audio processed:', result);
      
      // Award 20 points for completing vocabulary practice
      setBrowniePoints(prev => {
        const newTotal = prev + 20;
        localStorage.setItem(`browniePoints_${userId}`, newTotal.toString());
        return newTotal;
      });
      setVocabPracticePointsAnimation(true);
      setTimeout(() => {
        setVocabPracticePointsAnimation(false);
      }, 1500);
      
      // Reset timer and clear error on success
      setVocabPracticeTime(0);
      vocabPracticeDurationRef.current = 0;
      setVocabPracticeError(null);
      
    } catch (error: any) {
      console.error("Error uploading vocabulary practice audio:", error);
      const errorMessage = error.message || "Failed to upload audio. Please try again.";
      setVocabPracticeError(errorMessage);
      
      if (error.message?.includes('fetch') || error.message?.includes('Failed to fetch')) {
        setVocabPracticeError("Cannot connect to server. Please ensure the backend is running on port 8000.");
      }
    } finally {
      setIsUploadingVocabPractice(false);
    }
  };

  const handleSkipVocabPractice = () => {
    // Simply reset the practice state
    setIsPracticingVocab(false);
    setVocabPracticeTime(0);
    setVocabPracticeError(null);
    if (vocabPracticeTimerIntervalRef.current) {
      clearInterval(vocabPracticeTimerIntervalRef.current);
      vocabPracticeTimerIntervalRef.current = null;
    }
    if (vocabPracticeStreamRef.current) {
      vocabPracticeStreamRef.current.getTracks().forEach(track => track.stop());
      vocabPracticeStreamRef.current = null;
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
      if (vocabAudioRef.current) {
        vocabAudioRef.current.pause();
        vocabAudioRef.current = null;
      }
      if (vocabPracticeTimerIntervalRef.current) {
        clearInterval(vocabPracticeTimerIntervalRef.current);
      }
      if (vocabPracticeStreamRef.current) {
        vocabPracticeStreamRef.current.getTracks().forEach(track => track.stop());
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
            {!sessionId && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                ⚠️ Please log in to start a conversation. Redirecting...
              </div>
            )}
            {TOPICS.map((topic) => (
              <button 
                key={topic.id}
                onClick={() => handleTopicSelect(topic.id)}
                disabled={!sessionId}
                className={`w-full text-left px-5 py-4 rounded-xl border transition-all duration-300 font-medium text-lg relative overflow-hidden group ${
                  !sessionId
                    ? 'opacity-50 cursor-not-allowed'
                    : currentTopic === topic.id 
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

          {/* Brownie Points Window - Below Topics */}
          <div className="relative mt-6 p-5 rounded-2xl bg-gradient-to-br from-cyan/10 via-cyan/5 to-transparent backdrop-blur-xl border border-cyan/30 shadow-[0_0_25px_rgba(0,229,255,0.2)] hover:shadow-[0_0_35px_rgba(0,229,255,0.3)] transition-all duration-300 overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-cyan font-mono text-sm tracking-widest uppercase flex items-center gap-2">
                <Star className={`w-5 h-5 text-cyan fill-cyan/30 ${pointsAnimation ? 'animate-spin scale-125' : ''} transition-all duration-300`} />
                Earn Brownie Points
              </h3>
            </div>
            
            <div className="flex items-baseline gap-2">
              <span className={`text-4xl font-bold text-cyan transition-all duration-300 ${pointsAnimation ? 'scale-125 text-yellow-400' : ''}`}>
                {browniePoints}
              </span>
              <span className="text-sm text-cyan/70 font-mono uppercase tracking-widest">points</span>
            </div>
            
            <div className="mt-3 pt-3 border-t border-cyan/20">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-cyan/60 font-mono">100% clarity</span>
                  <span className="text-cyan font-bold">+10 points</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-cyan/60 font-mono">Vocabulary bonus challenge</span>
                  <span className="text-cyan font-bold">+20 points</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-cyan/60 font-mono">Continue chat</span>
                  <span className="text-cyan font-bold">+5 points</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-cyan/60 font-mono">Hear the vocabulary</span>
                  <span className="text-cyan font-bold">+10 points</span>
                </div>
              </div>
            </div>
            
            {/* Points Animation Overlay */}
            {pointsAnimation && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
                <div className="text-6xl font-bold text-yellow-400 animate-bounce drop-shadow-[0_0_20px_rgba(250,204,21,0.8)]">
                  +{lastPointsAwarded}
                </div>
              </div>
            )}
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
                    {question && (
                      <button 
                        onClick={handleListenClick}
                        disabled={isPlayingAudio}
                        className={`p-1.5 rounded-full transition-colors ${
                          isPlayingAudio 
                            ? 'bg-cyan/20 text-cyan animate-pulse' 
                            : 'hover:bg-white/10 text-cyan hover:text-white'
                        }`}
                        title="Listen to question"
                      >
                        <Volume2 className="w-4 h-4" />
                      </button>
                    )}
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
                      <div className="flex flex-col gap-4">
                        <div className="flex items-center gap-3">
                           <span className="tracking-wide">{welcomeMessage.line1}</span>
                           <Activity className="w-5 h-5 text-cyan animate-pulse" />
                        </div>
                        <span className="text-gray-300 text-base tracking-wide">{welcomeMessage.line2}</span>
                      </div>
                    ) : (
                      <div className="whitespace-pre-line leading-relaxed">
                        {question}
                      </div>
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
                  <div className="relative p-3 rounded-lg bg-white/5 border border-white/10">
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
                    {/* Points Animation - appears near clarity score when 100% */}
                    {clarityPointsAnimation && speechAnalysis.clarity_score === 1.0 && (
                      <div className="absolute -top-2 -right-2 flex items-center justify-center pointer-events-none z-20">
                        <div className="text-3xl font-bold text-yellow-400 animate-bounce drop-shadow-[0_0_15px_rgba(250,204,21,0.8)]">
                          +10
                        </div>
                      </div>
                    )}
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
              <div className="flex flex-col gap-3">
                {/* Feedback Message */}
                <div>
                  <h4 className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-3">Feedback</h4>
                  <div className="bg-cyan/10 p-6 rounded-lg border border-cyan/30">
                    <p className="text-white text-lg leading-relaxed flex items-center gap-2">
                      <span>{speechAnalysis.feedback}</span>
                      <Trophy className="w-6 h-6 text-yellow-400 flex-shrink-0" />
                    </p>
                  </div>
                </div>

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
            <div className="relative w-full max-w-md mx-auto">
              <button
                onClick={handleContinueChat}
                className="w-full px-8 py-4 rounded-xl bg-copper/20 border-2 border-copper text-white font-bold text-lg hover:bg-copper/30 hover:border-copper hover:shadow-[0_0_30px_rgba(255,107,53,0.6)] transition-all duration-300 flex items-center justify-center gap-3 group"
              >
                <span>Continue Chat</span>
                <Star className="w-5 h-5 text-cyan fill-cyan/30 group-hover:animate-pulse" />
              </button>
              {/* Points Animation - appears near Continue Chat button */}
              {continueChatPointsAnimation && (
                <div className="absolute -top-4 -right-4 flex items-center justify-center pointer-events-none z-50">
                  <div className="text-4xl font-bold text-yellow-400 animate-bounce drop-shadow-[0_0_20px_rgba(250,204,21,0.9)]">
                    +5
                  </div>
                </div>
              )}
            </div>
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
               responses.map((res, i) => {
                 const isChooseYourOwn = res === "Choose your own response";
                 
                 return (
                   <div 
                     key={i} 
                     onClick={() => {
                       if (isChooseYourOwn) {
                         // Don't set as selected - user needs to speak their own response
                         setSelectedResponse(null);
                       } else {
                         setSelectedResponse(res);
                       }
                     }}
                     className={`group relative p-4 rounded-xl border transition-all duration-300 flex items-center cursor-pointer animate-in fade-in slide-in-from-bottom-4 ${
                       selectedResponse === res
                         ? 'bg-copper/20 border-copper text-white shadow-[0_0_15px_rgba(255,107,53,0.4)]'
                         : isChooseYourOwn
                         ? 'bg-cyan/10 border-cyan/30 text-cyan hover:border-cyan hover:bg-cyan/20 hover:shadow-[0_0_20px_rgba(0,229,255,0.3)]'
                         : 'bg-white/5 border-white/10 text-gray-300 hover:border-copper hover:bg-copper/5 hover:text-white'
                     }`}
                     style={{ animationDelay: `${i * 100}ms` }}
                   >
                     <span className="text-base">
                       {res}
                     </span>
                     {selectedResponse === res && (
                       <span className="ml-auto text-cyan">✓</span>
                     )}
                   </div>
                 );
               })
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

                <div className="relative mt-4">
                    <button 
                        onClick={handleVocabListenClick}
                        disabled={isPlayingVocabAudio}
                        className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-all duration-300 group ${
                            isPlayingVocabAudio
                                ? 'bg-copper/20 border-copper text-white shadow-[0_0_15px_rgba(255,107,53,0.4)] animate-pulse'
                                : speechAnalysis && !vocabHeard
                                ? 'bg-copper/20 border-copper text-white shadow-[0_0_20px_rgba(255,107,53,0.6)] animate-pulse'
                                : 'bg-copper/10 border-copper/30 text-copper hover:bg-copper/20 hover:border-copper hover:text-white hover:shadow-[0_0_15px_rgba(255,107,53,0.2)]'
                        }`}
                        title="Hear word and definition"
                    >
                        <Volume2 className={`w-4 h-4 ${(isPlayingVocabAudio || (speechAnalysis && !vocabHeard)) ? 'animate-pulse' : 'group-hover:scale-110'} transition-transform`} />
                        <span className="text-xs font-bold tracking-widest uppercase">Hear me say</span>
                        <Star className={`w-4 h-4 text-cyan fill-cyan/30 ${(isPlayingVocabAudio || (speechAnalysis && !vocabHeard)) ? 'animate-pulse' : ''}`} />
                    </button>
              {/* Points Animation - appears near Hear me say button */}
              {hearMeSayPointsAnimation && (
                <div className="absolute -top-2 -right-2 flex items-center justify-center pointer-events-none z-20">
                  <div className="text-3xl font-bold text-yellow-400 animate-bounce drop-shadow-[0_0_15px_rgba(250,204,21,0.8)]">
                    +10
                  </div>
                </div>
              )}
                </div>
            </div>
        </div>

      </div>
    </div>
  );
}
