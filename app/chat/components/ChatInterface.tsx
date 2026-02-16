'use client';

import { Bot, Volume2, Mic, BookOpen, Activity, Signal, Wifi } from 'lucide-react';
import { useState } from 'react';

const TOPICS = [
  { id: 'gaming', label: 'Gaming' },
  { id: 'weekend', label: 'Weekend plans' },
  { id: 'hobbies', label: 'Hobbies' },
  { id: 'food', label: 'Food' },
  { id: 'youtube', label: 'YouTube' },
];

export function ChatInterface() {
  const userName = 'USER'; // Static for now until context/storage is implemented

  const [currentTopic, setCurrentTopic] = useState<string | null>(null);
  const [question, setQuestion] = useState(""); // Question is managed dynamically
  const [welcomeMessage, setWelcomeMessage] = useState({
    line1: `Hi ${userName}! Welcome to ConvoBridge!`,
    line2: "Select a topic to begin the mission."
  });
  const [responses, setResponses] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Vocabulary State (Mocked for now until Backend is fully connected)
  const [vocab, setVocab] = useState({
    word: 'Mission',
    type: 'noun',
    definition: 'An important assignment given to a person or group.',
    example: 'Your mission is to choose a topic.'
  });

  const handleTopicSelect = async (topicId: string) => {
    setCurrentTopic(topicId);
    setIsLoading(true);
    setResponses([]); // Clear previous responses
    
    try {
      // Call the Python Backend API
      const res = await fetch('http://localhost:8000/api/start_conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: topicId,
          user_id: userName,
          difficulty_level: 1
        })
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data = await res.json();
      
      setQuestion(data.question);
      setResponses(data.response_options || []);
      
      // For now, use a default vocab until vocabulary agent is implemented
      setVocab({ 
        word: "Topic", 
        type: "noun", 
        definition: "A matter dealt with in a text, discourse, or conversation.", 
        example: "That is an interesting topic." 
      });
      
      // Reset welcome message state when a topic is selected so we only show the question
      setWelcomeMessage({ line1: "", line2: "" });

    } catch (error) {
      console.error("Failed to fetch conversation", error);
      const errorMessage = error instanceof Error 
        ? error.message 
        : "Unknown error occurred";
      setQuestion(`Connection error: ${errorMessage}. Please make sure the backend server is running on port 8000.`);
      setResponses([]);
    } finally {
      setIsLoading(false);
    }
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

        {/* Response Options */}
        <div className="w-full max-w-3xl flex flex-col gap-4 mt-8">
            {isLoading ? (
               // Loading Skeletons
               [1, 2, 3].map((i) => (
                 <div key={i} className="h-16 w-full rounded-xl bg-white/5 animate-pulse border border-white/5"></div>
               ))
            ) : responses.length > 0 ? (
               responses.map((res, i) => (
                <div key={i} className="group relative p-4 rounded-xl bg-white/5 border border-white/10 hover:border-copper hover:bg-copper/5 transition-all duration-300 flex items-center justify-between cursor-pointer animate-in fade-in slide-in-from-bottom-4" style={{ animationDelay: `${i * 100}ms` }}>
                    <span className="text-gray-300 group-hover:text-white text-base">{res}</span>
                    <button className="flex-shrink-0 w-10 h-10 rounded-full bg-black/50 border border-white/20 flex items-center justify-center text-gray-400 group-hover:border-cyan group-hover:text-cyan group-hover:shadow-[0_0_10px_rgba(0,229,255,0.4)] transition-all">
                        <Mic className="w-5 h-5" />
                    </button>
                </div>
               ))
            ) : (
              <div className="text-center text-gray-500 font-mono text-sm py-8">Select a topic to generate responses...</div>
            )}
        </div>

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
