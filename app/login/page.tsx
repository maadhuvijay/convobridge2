'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { MessageSquare, User } from 'lucide-react';
import { LoginNavbar } from '../components/LoginNavbar';

export default function LoginPage() {
  const [name, setName] = useState('');
  const router = useRouter();

  const handleStartChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      // In a real app, we'd save the name to state/context/storage here
      console.log('Starting chat for:', name);
      router.push('/chat');
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden text-white font-sans selection:bg-copper selection:text-black flex flex-col">
      {/* Background Layers */}
      <div className="bg-cyberpunk absolute inset-0 z-0"></div>
      <div className="bg-dust absolute inset-0 z-0 pointer-events-none"></div>
      
      {/* Navbar */}
      <LoginNavbar />
      
      {/* Login Content */}
      <div className="relative z-10 flex-grow flex flex-col items-center justify-center w-full px-4">
        
        {/* Holographic Card Container */}
        <div className="w-full max-w-md p-1 relative group">
            {/* Animated Border Gradient */}
            <div className="absolute inset-0 bg-gradient-to-r from-copper via-cyan to-copper opacity-50 blur-lg group-hover:opacity-70 transition-opacity duration-500 rounded-2xl animate-pulse"></div>
            
            <div className="relative bg-black/80 backdrop-blur-xl border border-copper/50 rounded-2xl p-8 md:p-12 shadow-[0_0_50px_rgba(0,0,0,0.8)] overflow-hidden">
                
                {/* Scanline Overlay */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,11,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-0 bg-[length:100%_4px,6px_100%] pointer-events-none"></div>
                
                {/* Form Content */}
                <div className="relative z-10 flex flex-col items-center gap-8">
                    
                    <h2 className="text-3xl font-bold uppercase tracking-widest text-transparent bg-clip-text bg-gradient-to-b from-white to-gray-400 drop-shadow-sm font-mono text-center">
                        Access Terminal
                    </h2>
                    
                    <form onSubmit={handleStartChat} className="w-full flex flex-col gap-8">
                        
                        {/* Name Input Group */}
                        <div className="flex flex-col gap-3">
                            <label htmlFor="name" className="text-copper font-medium tracking-wide uppercase text-sm flex items-center gap-2">
                                <User className="w-4 h-4" />
                                User Name
                            </label>
                            
                            <div className="relative group/input">
                                <input
                                    type="text"
                                    id="name"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="Enter your name to start"
                                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-4 text-white placeholder-gray-500 outline-none focus:border-cyan focus:bg-white/10 focus:shadow-[0_0_15px_rgba(0,229,255,0.2)] transition-all duration-300 font-mono text-lg"
                                    required
                                />
                                {/* Input Glow Effect */}
                                <div className="absolute bottom-0 left-0 h-[2px] w-0 bg-cyan transition-all duration-300 group-focus-within/input:w-full shadow-[0_0_10px_rgba(0,229,255,0.8)]"></div>
                            </div>
                        </div>

                        {/* Let's Chat Button */}
                        <button 
                            type="submit"
                            className="group relative w-full px-8 py-4 bg-copper/10 border border-copper text-white text-xl font-bold rounded-xl overflow-hidden transition-all duration-300 hover:bg-copper/20 hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(255,107,53,0.4)] hover:border-cyan mt-4"
                        >
                            <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-in-out"></div>
                            
                            <span className="flex items-center justify-center gap-3 uppercase tracking-widest">
                                Let's Chat
                                <MessageSquare className="w-5 h-5 group-hover:rotate-12 group-hover:text-cyan transition-transform duration-300" />
                            </span>
                        </button>

                    </form>
                </div>
            </div>
        </div>
        
      </div>
    </main>
  );
}
