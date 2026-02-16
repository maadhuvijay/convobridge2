import { Bot, Sparkles } from 'lucide-react';
import Link from 'next/link';

export function Hero() {
  return (
    <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 text-center">
      
      {/* Decorative Holographic Elements */}
      <div className="absolute top-1/4 left-10 w-24 h-24 border border-cyan/20 rounded-full animate-pulse hidden md:block"></div>
      <div className="absolute bottom-1/3 right-12 w-16 h-16 border border-copper/20 rotate-45 hidden md:block"></div>

      {/* Main Heading */}
      <div className="relative mb-6">
        <h1 className="text-5xl md:text-8xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white via-gray-200 to-gray-500 drop-shadow-[0_4px_10px_rgba(255,107,53,0.3)] tracking-tighter uppercase font-mono">
          Convo<span className="text-copper drop-shadow-[0_0_15px_rgba(255,107,53,0.8)]">Bridge</span>
        </h1>
        <div className="absolute -bottom-2 left-0 w-full h-1 bg-gradient-to-r from-transparent via-copper to-transparent opacity-70 blur-[2px]"></div>
      </div>
      
      {/* Subtext */}
      <p className="text-lg md:text-2xl text-gray-300 mb-12 max-w-3xl font-light tracking-wide leading-relaxed drop-shadow-md">
        <span className="text-copper font-medium">Practice real conversations.</span>
        <span className="text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.6)]">Build confidence.</span>
        <span className="text-cyan font-bold drop-shadow-[0_0_10px_rgba(0,229,255,0.8)] animate-pulse">Find your voice.</span>
      </p>
      
      {/* Robot Image Container (Holographic Card) - Centered */}
      <div className="relative w-64 h-64 md:w-80 md:h-80 rounded-2xl bg-black/40 backdrop-blur-xl border border-copper/40 flex items-center justify-center shadow-[0_0_40px_rgba(255,107,53,0.2)] group hover:border-cyan hover:shadow-[0_0_50px_rgba(0,229,255,0.3)] transition-all duration-500 mt-4">
          
          {/* Inner Grid/Tech Pattern */}
          <div className="absolute inset-2 border border-white/5 rounded-xl bg-[radial-gradient(circle_at_center,_rgba(255,107,53,0.1)_0%,_transparent_70%)]"></div>
          
          {/* Scanline Overlay */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,11,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-0 bg-[length:100%_4px,6px_100%] pointer-events-none rounded-2xl"></div>

          <Bot className="relative z-10 w-32 h-32 md:w-48 md:h-48 text-copper group-hover:text-cyan drop-shadow-[0_0_20px_rgba(255,107,53,0.6)] group-hover:drop-shadow-[0_0_30px_rgba(0,229,255,0.6)] transition-all duration-500 animate-float" />
          
          {/* Floating Particle/Sparkle */}
          <Sparkles className="absolute top-4 right-4 w-6 h-6 text-cyan/70 animate-pulse" />
      </div>
        
    </div>
  );
}
