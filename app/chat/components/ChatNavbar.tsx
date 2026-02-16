'use client';

import { useState, useRef, useEffect } from 'react';
import { Bot, User, LogOut } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export function ChatNavbar() {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  
  // Static user name for now
  const userName = 'USER';

  const handleLogout = () => {
    router.push('/');
  };

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <nav className="fixed top-0 left-0 w-full z-50 px-6 py-4 flex items-center justify-between backdrop-blur-md bg-black/60 border-b border-copper/30 shadow-[0_4px_30px_rgba(255,107,53,0.1)]">
      
      {/* Logo Section (Left) */}
      <Link href="/" className="flex items-center gap-3 group">
        <div className="w-10 h-10 rounded-lg bg-black/80 border border-copper flex items-center justify-center shadow-[0_0_15px_rgba(255,107,53,0.4)] group-hover:shadow-[0_0_25px_rgba(255,107,53,0.6)] transition-all duration-300">
          <Bot className="w-6 h-6 text-copper group-hover:text-white transition-colors duration-300" />
        </div>
      </Link>
      
      {/* ConvoBridge Text (Middle) */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none">
        <span className="text-xl md:text-2xl font-bold tracking-widest text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)] uppercase font-mono">
          Convo<span className="text-copper">Bridge</span>
        </span>
      </div>
      
      {/* Right Section: User Name + Profile */}
      <div className="flex items-center gap-4" ref={dropdownRef}>
        
        {/* User Name Display */}
        <span className="text-cyan font-mono text-xs md:text-sm tracking-widest uppercase hidden md:block">
          {userName}
        </span>

        {/* Profile Icon with Dropdown */}
        <div className="relative">
          <button 
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="w-10 h-10 rounded-full bg-copper/10 border border-copper/50 flex items-center justify-center hover:bg-copper/20 hover:border-cyan hover:shadow-[0_0_15px_rgba(0,229,255,0.4)] transition-all duration-300 cursor-pointer focus:outline-none"
          >
            <User className="w-5 h-5 text-white" />
          </button>

          {/* Dropdown Menu */}
          {isDropdownOpen && (
            <div className="absolute right-0 top-12 w-48 rounded-xl bg-black/90 backdrop-blur-xl border border-copper/30 shadow-[0_0_30px_rgba(255,107,53,0.2)] overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200 z-50">
              <div className="p-2">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-colors group"
                >
                  <LogOut className="w-4 h-4 text-copper group-hover:text-cyan transition-colors" />
                  <span className="font-medium tracking-wide">Logout</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
