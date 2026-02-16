import { Bot, Volume2, Mic, BookOpen } from 'lucide-react';

const TOPICS = [
  { id: 'gaming', label: 'Gaming' },
  { id: 'weekend', label: 'Weekend plans' },
  { id: 'hobbies', label: 'Hobbies' },
  { id: 'food', label: 'Food' },
  { id: 'youtube', label: 'YouTube' },
];

export function ChatInterface() {
  return (
    <div className="w-full h-full max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-6 p-4 pt-24">
      
      {/* Left Panel: Topics */}
      <div className="md:col-span-3 flex flex-col gap-4">
        <div className="p-6 rounded-2xl bg-black/40 backdrop-blur-xl border border-copper/30 shadow-[0_0_30px_rgba(0,0,0,0.5)]">
          <h3 className="text-copper font-mono text-sm tracking-widest uppercase mb-4 border-b border-white/10 pb-2">Select Topic</h3>
          <div className="flex flex-col gap-3">
            {TOPICS.map((topic) => (
              <button 
                key={topic.id}
                className="w-full text-left px-4 py-3 rounded-lg border border-white/5 bg-white/5 text-gray-300 hover:bg-copper/10 hover:border-copper/50 hover:text-white transition-all duration-300 font-medium"
              >
                {topic.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="md:col-span-9 flex flex-col gap-6">
        
        {/* Top Section: Robot + Question */}
        <div className="flex flex-col md:flex-row gap-6">
          
          {/* Robot Avatar */}
          <div className="w-full md:w-1/3 aspect-square md:aspect-auto md:h-64 rounded-2xl bg-black/40 backdrop-blur-xl border border-copper/40 flex items-center justify-center shadow-[0_0_40px_rgba(255,107,53,0.1)] relative group">
             <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,11,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-0 bg-[length:100%_4px,6px_100%] pointer-events-none rounded-2xl"></div>
             <Bot className="w-24 h-24 text-copper group-hover:text-cyan transition-colors duration-500 animate-float drop-shadow-[0_0_20px_rgba(255,107,53,0.6)]" />
          </div>

          {/* Question Panel */}
          <div className="w-full md:w-2/3 p-6 md:p-8 rounded-2xl bg-black/60 backdrop-blur-xl border border-cyan/30 shadow-[0_0_30px_rgba(0,229,255,0.1)] flex flex-col justify-between relative overflow-hidden">
             <div className="absolute top-0 left-0 w-1 h-full bg-cyan shadow-[0_0_15px_rgba(0,229,255,0.8)]"></div>
             
             <div className="flex justify-between items-start mb-4">
                <span className="text-cyan font-mono text-xs tracking-widest uppercase">Agent Query</span>
                <button className="p-2 rounded-full hover:bg-white/10 text-cyan transition-colors">
                  <Volume2 className="w-5 h-5" />
                </button>
             </div>
             
             <p className="text-xl md:text-2xl text-white font-light leading-relaxed">
               "What kind of video games do you enjoy playing the most?"
             </p>
          </div>
        </div>

        {/* Bottom Section: Responses + Vocabulary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Response Options (Span 2 columns) */}
            <div className="md:col-span-2 flex flex-col gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="group relative p-4 rounded-xl bg-white/5 border border-white/10 hover:border-copper hover:bg-copper/5 transition-all duration-300 flex items-center justify-between">
                   <span className="text-gray-300 group-hover:text-white">I really like playing adventure games because I can explore new worlds.</span>
                   <button className="flex-shrink-0 w-10 h-10 rounded-full bg-black/50 border border-white/20 flex items-center justify-center text-gray-400 group-hover:border-cyan group-hover:text-cyan group-hover:shadow-[0_0_10px_rgba(0,229,255,0.4)] transition-all">
                     <Mic className="w-5 h-5" />
                   </button>
                </div>
              ))}
            </div>

            {/* Vocabulary Window (Span 1 column) */}
            <div className="md:col-span-1 p-6 rounded-2xl bg-black/40 backdrop-blur-xl border border-copper/30 shadow-[0_0_30px_rgba(0,0,0,0.5)] flex flex-col gap-4">
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
    </div>
  );
}
