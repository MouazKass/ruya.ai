import type { ReactNode } from 'react';

interface LayoutProps {
  sidebar: ReactNode;
  content: ReactNode;
}

export const Layout = ({ sidebar, content }: LayoutProps) => {
  return (
    <div className="flex h-screen w-screen bg-background text-text overflow-hidden font-sans">
      {/* Decorative background grid/elements for 'Stealth' look */}
      <div className="absolute inset-0 pointer-events-none opacity-5" 
           style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #334155 1px, transparent 0)', backgroundSize: '40px 40px' }}>
      </div>

      {/* Left Panel: Sidebar */}
      <aside className="w-[400px] h-full flex flex-col border-r border-secondary/50 bg-surface/50 backdrop-blur-sm z-10 relative shadow-2xl overflow-hidden">
        <div className="p-4 border-b border-secondary/50 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-widest text-accent font-display uppercase">Outbreak<span className="text-white">OS</span></h1>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-accent animate-pulse"></span>
            <span className="text-xs font-mono text-accent">LIVE</span>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {sidebar}
        </div>
        <div className="p-2 border-t border-secondary/50 text-[10px] text-text-dim text-center font-mono uppercase">
          Secure Connection // <span className="text-success">Encrypted</span>
        </div>
      </aside>

      {/* Right Panel: Content (Map) */}
      <main className="flex-1 h-full relative z-0">
        {content}
        
        {/* Overlay Gradients */}
        <div className="absolute inset-0 pointer-events-none bg-radial-gradient from-transparent to-background/50"></div>
      </main>
    </div>
  );
};
