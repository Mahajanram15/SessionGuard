import React from 'react';

interface ThumbnailProps {
  category: string;
  className?: string;
}

export const CourseThumbnail: React.FC<ThumbnailProps> = ({ category, className = "w-full h-32" }) => {
  const cat = category.toLowerCase();

  if (cat.includes('machine') || cat.includes('ai')) {
    return (
      <div className={`${className} bg-gradient-to-tr from-violet-600 via-purple-600 to-indigo-700 flex items-center justify-center relative overflow-hidden rounded-xl`}>
        <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:12px_12px]" />
        <svg className="w-16 h-16 text-white/90 drop-shadow-md" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="32" cy="18" r="6" fill="rgba(255,255,255,0.2)" />
          <circle cx="16" cy="46" r="6" fill="rgba(255,255,255,0.2)" />
          <circle cx="48" cy="46" r="6" fill="rgba(255,255,255,0.2)" />
          <circle cx="32" cy="36" r="4" fill="rgba(255,255,255,0.4)" />
          <path d="M32 24v8M18 42l12-4M46 42l-12-4M20 44h24" strokeLinecap="round" />
        </svg>
        <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/30 backdrop-blur-sm text-[10px] font-mono text-white/90 font-semibold">ML / AI</span>
      </div>
    );
  }

  if (cat.includes('cyber') || cat.includes('security')) {
    return (
      <div className={`${className} bg-gradient-to-tr from-emerald-600 via-teal-700 to-cyan-800 flex items-center justify-center relative overflow-hidden rounded-xl`}>
        <div className="absolute inset-0 opacity-15 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:12px_12px]" />
        <svg className="w-16 h-16 text-white/90 drop-shadow-md" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M32 10l18 6v14c0 14-18 24-18 24S14 44 14 30V16l18-6z" fill="rgba(255,255,255,0.15)" strokeLinejoin="round" />
          <path d="M26 30l4 4 8-8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/30 backdrop-blur-sm text-[10px] font-mono text-white/90 font-semibold">SECURITY</span>
      </div>
    );
  }

  if (cat.includes('web') || cat.includes('react')) {
    return (
      <div className={`${className} bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-700 flex items-center justify-center relative overflow-hidden rounded-xl`}>
        <div className="absolute inset-0 opacity-15 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:12px_12px]" />
        <svg className="w-16 h-16 text-white/90 drop-shadow-md" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="12" y="14" width="40" height="36" rx="4" fill="rgba(255,255,255,0.15)" />
          <path d="M12 24h40M18 19h2M24 19h2M30 19h2" strokeLinecap="round" />
          <path d="M22 36l4-4-4-4M32 40h10" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/30 backdrop-blur-sm text-[10px] font-mono text-white/90 font-semibold">REACT / WEB</span>
      </div>
    );
  }

  if (cat.includes('data') || cat.includes('algorithm')) {
    return (
      <div className={`${className} bg-gradient-to-tr from-amber-600 via-orange-600 to-rose-700 flex items-center justify-center relative overflow-hidden rounded-xl`}>
        <div className="absolute inset-0 opacity-15 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:12px_12px]" />
        <svg className="w-16 h-16 text-white/90 drop-shadow-md" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="14" y="38" width="10" height="14" rx="2" fill="rgba(255,255,255,0.2)" />
          <rect x="27" y="26" width="10" height="26" rx="2" fill="rgba(255,255,255,0.3)" />
          <rect x="40" y="16" width="10" height="36" rx="2" fill="rgba(255,255,255,0.4)" />
          <path d="M18 34l12-10 14-8" strokeLinecap="round" />
        </svg>
        <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/30 backdrop-blur-sm text-[10px] font-mono text-white/90 font-semibold">DSA</span>
      </div>
    );
  }

  if (cat.includes('cloud')) {
    return (
      <div className={`${className} bg-gradient-to-tr from-sky-600 via-cyan-600 to-blue-700 flex items-center justify-center relative overflow-hidden rounded-xl`}>
        <div className="absolute inset-0 opacity-15 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:12px_12px]" />
        <svg className="w-16 h-16 text-white/90 drop-shadow-md" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M44 42H20a10 10 0 01-2-19.8A14 14 0 0142 18a12 12 0 012 24z" fill="rgba(255,255,255,0.2)" strokeLinejoin="round" />
        </svg>
        <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/30 backdrop-blur-sm text-[10px] font-mono text-white/90 font-semibold">CLOUD</span>
      </div>
    );
  }

  // Default: Computer Science
  return (
    <div className={`${className} bg-gradient-to-tr from-purple-700 via-indigo-700 to-purple-900 flex items-center justify-center relative overflow-hidden rounded-xl`}>
      <div className="absolute inset-0 opacity-15 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:12px_12px]" />
      <svg className="w-16 h-16 text-white/90 drop-shadow-md" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="20" y="20" width="24" height="24" rx="3" fill="rgba(255,255,255,0.2)" />
        <path d="M26 20v-6M38 20v-6M26 44v6M38 44v6M20 26h-6M20 38h-6M44 26h6M44 38h6" strokeLinecap="round" />
      </svg>
      <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/30 backdrop-blur-sm text-[10px] font-mono text-white/90 font-semibold">CS</span>
    </div>
  );
};
