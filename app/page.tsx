import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden text-white font-sans selection:bg-copper selection:text-black">
      {/* Background Layers */}
      <div className="bg-futuristic absolute inset-0 z-0"></div>
      <div className="bg-particles absolute inset-0 z-0 pointer-events-none"></div>
      
      {/* Navbar */}
      <Navbar />
      
      {/* Hero Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen w-full">
        <Hero />
      </div>
    </main>
  );
}
