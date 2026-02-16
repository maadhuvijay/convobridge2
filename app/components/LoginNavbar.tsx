import { Bot, Home } from 'lucide-react';
import Link from 'next/link';

export function LoginNavbar() {
  return (
    <nav className="fixed top-0 left-0 w-full z-50 px-6 py-4 flex items-center justify-between backdrop-blur-md bg-black/60 border-b border-copper/30 shadow-[0_4px_30px_rgba(255,107,53,0.1)]">
      
      {/* Logo Section */}
      <Link href="/" className="flex items-center gap-3 group">
        <div className="w-12 h-12 rounded-xl bg-black/80 border border-copper flex items-center justify-center shadow-[0_0_15px_rgba(255,107,53,0.4)] group-hover:shadow-[0_0_25px_rgba(255,107,53,0.6)] transition-all duration-300">
          <Bot className="w-7 h-7 text-copper group-hover:text-white transition-colors duration-300" />
        </div>
        <span className="text-2xl font-bold tracking-widest text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)] uppercase font-mono">
          Convo<span className="text-copper">Bridge</span>
        </span>
      </Link>
      
      {/* Home Button */}
      <Link 
        href="/"
        className="relative overflow-hidden px-8 py-2 rounded-lg border border-copper/80 text-white font-medium transition-all duration-300 bg-black/50 hover:bg-copper/20 hover:border-cyan hover:shadow-[0_0_20px_rgba(0,229,255,0.4)] flex items-center gap-2 group"
      >
        <span className="relative z-10 tracking-wide uppercase text-sm font-semibold group-hover:text-cyan transition-colors">Home</span>
        <Home className="w-4 h-4 relative z-10 text-copper group-hover:text-cyan transition-colors" />
        
        {/* Hover Glitch/Scanline Effect (Subtle) */}
        <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-in-out"></div>
      </Link>
    </nav>
  );
}
