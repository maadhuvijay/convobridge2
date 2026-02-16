import { ChatNavbar } from './components/ChatNavbar';
import { ChatInterface } from './components/ChatInterface';

export default function ChatPage() {
  return (
    <main className="relative min-h-screen overflow-x-hidden text-white font-sans selection:bg-copper selection:text-black bg-black">
      {/* Background Layers */}
      <div className="bg-cyberpunk absolute inset-0 z-0 fixed"></div>
      <div className="bg-dust absolute inset-0 z-0 pointer-events-none fixed"></div>
      
      <ChatNavbar />
      
      <div className="relative z-10 w-full min-h-screen">
        <ChatInterface />
      </div>
    </main>
  );
}
