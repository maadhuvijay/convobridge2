import { Bot, User } from 'lucide-react';
import Link from 'next/link';

export function ChatNavbar() {
  return (
    <nav className="fixed top-0 left-0 w-full z-50 px-6 py-4 flex items-center justify-between backdrop-blur-md bg-black/60 border-b border-copper/30 shadow-[0_4px_30px_rgba(255,107,53,0.1)]">
      
      {/* Logo Section (Left) */}
      <Link href="/" className="flex items-center gap-3 group">
        <div className="w-10 h-10 rounded-lg bg-black/80 border border-copper flex items-center justify-center shadow-[0_0_15px_rgba(255,107,53,0.4)] group-hover:shadow-[0_0_25px_rgba(255,107,53,0.6)] transition-all duration-300">
          <Bot className="w-6 h-6 text-copper group-hover:text-white transition-colors duration-300" />
        </div>
      </Link>
      
      {/* ConvoBridge Text (Middle) */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        <span className="text-xl md:text-2xl font-bold tracking-widest text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)] uppercase font-mono">
          Convo<span className="text-copper">Bridge</span>
        </span>
      </div>
      
      {/* Profile Icon (Right) */}
      <div className="w-10 h-10 rounded-full bg-copper/10 border border-copper/50 flex items-center justify-center hover:bg-copper/20 hover:border-cyan hover:shadow-[0_0_15px_rgba(0,229,255,0.4)] transition-all duration-300 cursor-pointer">
        <User className="w-5 h-5 text-white" />
      </div>
    </nav>
  );
}
