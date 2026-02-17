import { Suspense } from 'react';
import { ChatNavbar } from './components/ChatNavbar';
import { ChatInterface } from './components/ChatInterface';

// Force dynamic rendering since we use search params
export const dynamic = 'force-dynamic';

function ChatNavbarFallback() {
  return (
    <nav className="fixed top-0 left-0 w-full z-50 px-6 py-4 flex items-center justify-between backdrop-blur-md bg-black/60 border-b border-copper/30">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-black/80 border border-copper flex items-center justify-center"></div>
        <span className="text-2xl font-bold tracking-widest text-white uppercase font-mono">
          Convo<span className="text-copper">Bridge</span>
        </span>
      </div>
    </nav>
  );
}

function ChatInterfaceFallback() {
  return (
    <div className="relative z-10 w-full min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="text-2xl font-bold text-white mb-4">Loading...</div>
        <div className="text-gray-400">Preparing your conversation space</div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <main className="relative min-h-screen overflow-x-hidden text-white font-sans selection:bg-copper selection:text-black bg-black">
      {/* Background Layers */}
      <div className="bg-cyberpunk absolute inset-0 z-0 fixed"></div>
      <div className="bg-dust absolute inset-0 z-0 pointer-events-none fixed"></div>
      
      <Suspense fallback={<ChatNavbarFallback />}>
        <ChatNavbar />
      </Suspense>
      
      <div className="relative z-10 w-full min-h-screen">
        <Suspense fallback={<ChatInterfaceFallback />}>
          <ChatInterface />
        </Suspense>
      </div>
    </main>
  );
}
