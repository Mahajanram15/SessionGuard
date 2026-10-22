import React from 'react';
import { ArrowRight } from 'lucide-react';

export const PromoCard: React.FC = () => {
  return (
    <div className="w-full bg-gradient-to-br from-[#F9F5FF] via-[#F4EBFF] to-[#E9D7FE] rounded-2xl p-5 border border-purple-100 shadow-[0_4px_16px_rgba(105,65,198,0.06)] relative overflow-hidden flex items-center justify-between">
      {/* Decorative background glow */}
      <div className="absolute -right-8 -bottom-8 w-28 h-28 bg-purple-300/30 rounded-full blur-xl pointer-events-none" />

      {/* Text Copy */}
      <div className="relative z-10 max-w-[210px] flex flex-col items-start">
        <h4 className="text-base font-extrabold text-slate-900 leading-tight">
          Learn even more!
        </h4>
        <p className="text-xs text-slate-600 mt-1 leading-relaxed">
          Unlock unlimited access to verified professional certificates and career mentorship.
        </p>

        <button
          onClick={() => alert('LearnSphere Pro Demo: Career tracks & verified certificates simulation.')}
          className="mt-3.5 bg-[#6941C6] hover:bg-[#53389E] text-white text-xs font-bold px-4 py-2 rounded-xl shadow-sm shadow-purple-600/20 hover:shadow-md transition-all inline-flex items-center space-x-1.5 cursor-pointer"
        >
          <span>Go Premium</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Right Megaphone / Graduation Graphic */}
      <div className="relative z-10 w-24 h-24 shrink-0 flex items-center justify-center select-none pointer-events-none">
        <svg className="w-20 h-20 drop-shadow-md" viewBox="0 0 100 100" fill="none">
          {/* Circular backdrop */}
          <circle cx="50" cy="50" r="38" fill="#7F56D9" fillOpacity="0.12" />

          {/* Megaphone body */}
          <path
            d="M30 42H40L56 30V70L40 58H30C27.7909 58 26 56.2091 26 54V46C26 43.7909 27.7909 42 30 42Z"
            fill="#7F56D9"
          />
          {/* Megaphone front rim */}
          <ellipse cx="56" cy="50" rx="4" ry="20" fill="#9E77ED" />
          {/* Handle */}
          <path d="M35 58V68C35 70.2 36.8 72 39 72H41C43.2 72 45 70.2 45 68V58" fill="#53389E" />

          {/* Sound waves & sparkles */}
          <path d="M66 40C69 43 71 46 71 50C71 54 69 57 66 60" stroke="#7F56D9" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M74 35C79 39 82 44 82 50C82 56 79 61 74 65" stroke="#9E77ED" strokeWidth="2.5" strokeLinecap="round" />

          {/* Sparkles */}
          <polygon points="76,24 78,28 82,30 78,32 76,36 74,32 70,30 74,28" fill="#FDB022" />
          <polygon points="24,28 25,31 28,32 25,33 24,36 23,33 20,32 23,31" fill="#FDB022" />
        </svg>
      </div>
    </div>
  );
};
