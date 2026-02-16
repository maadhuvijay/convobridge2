import { Bot, Volume2, Mic, BookOpen, Activity, Signal, Wifi } from 'lucide-react';

const TOPICS = [
  { id: 'gaming', label: 'Gaming' },
  { id: 'weekend', label: 'Weekend plans' },
  { id: 'hobbies', label: 'Hobbies' },
  { id: 'food', label: 'Food' },
  { id: 'youtube', label: 'YouTube' },
];

export function ChatInterface() {
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
                className="w-full text-left px-5 py-4 rounded-xl border border-white/10 bg-white/5 text-gray-300 hover:bg-copper/10 hover:border-copper hover:text-white hover:shadow-[0_0_15px_rgba(255,107,53,0.2)] transition-all duration-300 font-medium text-lg"
              >
                {topic.label}
              </button>
            ))}
          </div>

          {/* System Status / Decor Area (Fills empty space) */}
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
                <span>ID: AGENT-007-V2 // ENCRYPTED</span>
             </div>
          </div>

        </div>
      </div>

      {/* Main Content Area */}
      <div className="md:col-span-9 flex flex-col h-full gap-8 relative">
        
        {/* Top Section: Robot + Question (Speech Bubble) */}
        <div className="flex flex-col md:flex-row items-start gap-8 mt-4">
          
          {/* Robot Avatar */}
          <div className="flex-shrink-0 w-48 h-48 rounded-2xl bg-black/40 backdrop-blur-xl border border-copper/40 flex items-center justify-center shadow-[0_0_40px_rgba(255,107,53,0.1)] relative group">
             <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,11,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-0 bg-[length:100%_4px,6px_100%] pointer-events-none rounded-2xl"></div>
             <Bot className="w-24 h-24 text-copper group-hover:text-cyan transition-colors duration-500 animate-float drop-shadow-[0_0_20px_rgba(255,107,53,0.6)]" />
          </div>

          {/* Question Panel - Speech Bubble Style */}
          <div className="relative mt-6 max-w-2xl">
             {/* Speech Bubble Tail */}
             <div className="absolute top-6 -left-3 w-6 h-6 bg-black/60 border-l border-b border-cyan/30 transform rotate-45 z-0 hidden md:block"></div>
             
             <div className="relative z-10 p-6 rounded-2xl rounded-tl-none bg-black/60 backdrop-blur-xl border border-cyan/30 shadow-[0_0_30px_rgba(0,229,255,0.15)] flex flex-col gap-3">
                <div className="flex justify-between items-start">
                    <span className="text-cyan font-mono text-xs tracking-widest uppercase mb-2">Agent Query</span>
                    <button className="p-1.5 rounded-full hover:bg-white/10 text-cyan transition-colors">
                      <Volume2 className="w-4 h-4" />
                    </button>
                </div>
                
                <p className="text-lg md:text-xl text-white font-light leading-relaxed">
                  "What kind of video games do you enjoy playing the most?"
                </p>
             </div>
          </div>
        </div>

        {/* Response Options */}
        <div className="w-full max-w-3xl flex flex-col gap-4 mt-8">
            {[1, 2, 3].map((i) => (
            <div key={i} className="group relative p-4 rounded-xl bg-white/5 border border-white/10 hover:border-copper hover:bg-copper/5 transition-all duration-300 flex items-center justify-between cursor-pointer">
                <span className="text-gray-300 group-hover:text-white text-base">I really like playing adventure games because I can explore new worlds.</span>
                <button className="flex-shrink-0 w-10 h-10 rounded-full bg-black/50 border border-white/20 flex items-center justify-center text-gray-400 group-hover:border-cyan group-hover:text-cyan group-hover:shadow-[0_0_10px_rgba(0,229,255,0.4)] transition-all">
                    <Mic className="w-5 h-5" />
                </button>
            </div>
            ))}
        </div>

        {/* Vocabulary Window - Fixed to Bottom Right (Footer Position) */}
        <div className="md:fixed md:bottom-4 md:right-8 w-full md:w-80 p-6 rounded-2xl bg-black/80 backdrop-blur-xl border border-copper/30 shadow-[0_0_40px_rgba(0,0,0,0.8)] flex flex-col gap-4 z-50 mt-8 md:mt-0 transition-all duration-300 hover:border-copper/60">
            <div className="flex items-center gap-2 text-copper border-b border-white/10 pb-2">
                <BookOpen className="w-5 h-5" />
                <h3 className="font-mono text-sm tracking-widest uppercase">Vocabulary</h3>
            </div>
            
            <div>
                <h4 className="text-2xl font-bold text-white mb-1">Hobby</h4>
                <p className="text-sm text-gray-400 italic mb-3">noun • /ˈhɒbi/</p>
                <p className="text-gray-300 text-sm mb-4">An activity done regularly in one's leisure time for pleasure.</p>
                
                <div className="p-3 rounded-lg bg-white/5 border border-white/5 text-sm text-gray-300 italic border-l-2 border-l-cyan">
                "My favorite hobby is painting landscapes."
                </div>
            </div>
        </div>

      </div>
    </div>
  );
}
