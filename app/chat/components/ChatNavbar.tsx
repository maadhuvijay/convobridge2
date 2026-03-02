'use client';

import { useState, useRef, useEffect } from 'react';
import { Bot, User, LogOut, Info } from 'lucide-react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';

export function ChatNavbar() {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isSessionInfoOpen, setIsSessionInfoOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Get username and user_id from query parameters
  const userName = searchParams.get('user') || 'USER';
  const userId = searchParams.get('userId') || '';
  const sessionId = searchParams.get('sessionId') || null;
  
  // Get login timestamp from localStorage
  const [loginTimestamp, setLoginTimestamp] = useState<string | null>(null);
  
  useEffect(() => {
    // Get login timestamp from localStorage
    const storedTimestamp = localStorage.getItem('login_timestamp');
    setLoginTimestamp(storedTimestamp);
  }, []);

  const handleLogout = async () => {
    // Close dropdown menu immediately
    setIsDropdownOpen(false);
    
    try {
      // Call logout API endpoint to end session and save exit timestamp
      if (userId) {
        const response = await fetch('http://localhost:8000/api/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: userId,
            session_id: sessionId || null
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('Logout successful:', data);
        }
      }
    } catch (error) {
      console.error('Error during logout:', error);
      // Continue with logout even if API call fails
    }
    
    // Clear login timestamp from localStorage
    localStorage.removeItem('login_timestamp');
    
    // Redirect to home page
    router.push('/');
  };

  const handleSessionInfo = () => {
    setIsDropdownOpen(false);
    setIsSessionInfoOpen(true);
  };

  const formatTimestamp = (timestamp: string | null): string => {
    if (!timestamp) return 'Not available';
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      });
    } catch (error) {
      return timestamp;
    }
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
      
      {/* Logo Section (Left) - Display only, no link */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-black/80 border border-copper flex items-center justify-center shadow-[0_0_15px_rgba(255,107,53,0.4)] transition-all duration-300">
          <Bot className="w-6 h-6 text-copper transition-colors duration-300" />
        </div>
      </div>
      
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
                  onClick={handleSessionInfo}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-colors group"
                >
                  <Info className="w-4 h-4 text-copper group-hover:text-cyan transition-colors" />
                  <span className="font-medium tracking-wide">Session info</span>
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleLogout();
                  }}
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

      {/* Session Info Modal */}
      {isSessionInfoOpen && (
        <div 
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setIsSessionInfoOpen(false)}
        >
          <div 
            className="relative w-full max-w-md mx-4 bg-black/90 backdrop-blur-xl border border-copper/50 rounded-xl shadow-[0_0_50px_rgba(255,107,53,0.3)] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Scanline Overlay */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,11,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-0 bg-[length:100%_4px,6px_100%] pointer-events-none"></div>
            
            <div className="relative z-10 p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold uppercase tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-white to-copper font-mono">
                  Session Information
                </h3>
                <button
                  onClick={() => setIsSessionInfoOpen(false)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Session Details */}
              <div className="space-y-4">
                <div className="p-4 bg-white/5 border border-copper/20 rounded-lg">
                  <div className="text-xs uppercase tracking-widest text-copper mb-1 font-mono">User Name</div>
                  <div className="text-white font-medium">{userName}</div>
                </div>

                <div className="p-4 bg-white/5 border border-copper/20 rounded-lg">
                  <div className="text-xs uppercase tracking-widest text-copper mb-1 font-mono">Session ID</div>
                  <div className="text-white font-mono text-sm break-all">{sessionId || 'Not available'}</div>
                </div>

                <div className="p-4 bg-white/5 border border-copper/20 rounded-lg">
                  <div className="text-xs uppercase tracking-widest text-copper mb-1 font-mono">Login Time</div>
                  <div className="text-white font-medium">{formatTimestamp(loginTimestamp)}</div>
                </div>
              </div>

              {/* Close Button */}
              <button
                onClick={() => setIsSessionInfoOpen(false)}
                className="w-full mt-6 px-4 py-2 bg-copper/10 border border-copper/50 text-white rounded-lg hover:bg-copper/20 hover:border-cyan transition-all duration-300 font-medium tracking-wide"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
