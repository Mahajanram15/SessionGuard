import React from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';

interface HeroBannerProps {
  onJoinNowClick?: () => void;
}

export const HeroBanner: React.FC<HeroBannerProps> = ({ onJoinNowClick }) => {
  return (
    <div className="w-full rounded-[28px] bg-gradient-to-r from-[#6941C6] via-[#7F56D9] to-[#9E77ED] text-white p-6 sm:p-8 relative overflow-hidden shadow-lg shadow-purple-600/15 flex items-center justify-between">
      {/* Subtle Decorative Education Background Shapes */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {/* Soft radial glow */}
        <div className="absolute -left-12 -bottom-12 w-48 h-48 bg-white/10 rounded-full blur-2xl" />
        <div className="absolute right-32 -top-10 w-40 h-40 bg-purple-300/20 rounded-full blur-xl" />

        {/* Floating geometric line art */}
        <svg className="absolute inset-0 w-full h-full opacity-10" viewBox="0 0 800 300" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="120" cy="50" r="30" strokeDasharray="4 4" />
          <polygon points="450,40 480,90 420,90" />
          <path d="M600 200c40-30 80 10 120-20" />
          <rect x="280" y="220" width="30" height="30" rx="6" />
        </svg>
      </div>

      {/* Left Content Area */}
      <div className="relative z-10 max-w-sm sm:max-w-md flex flex-col items-start">
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-sm text-purple-100 text-[11px] font-bold tracking-wider uppercase mb-3">
          <Sparkles className="w-3 h-3 text-purple-200" />
          <span>ONLINE COURSE</span>
        </div>

        <h1 className="text-xl sm:text-2xl lg:text-[28px] font-extrabold tracking-tight leading-snug text-white drop-shadow-sm">
          Sharpen Your Skills With Professional Online Courses
        </h1>

        <button
          onClick={onJoinNowClick}
          className="mt-5 sm:mt-6 bg-white text-[#6941C6] hover:bg-purple-50 font-bold px-6 py-2.5 rounded-full text-xs sm:text-sm shadow-md shadow-purple-950/10 hover:shadow-lg transition-all inline-flex items-center space-x-2 group cursor-pointer"
        >
          <span>Join Now</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>

      {/* Right Student Learning Illustration */}
      <div className="hidden sm:flex relative z-10 w-44 lg:w-56 shrink-0 justify-center items-center select-none pointer-events-none">
        <svg className="w-40 h-40 lg:w-48 lg:h-48 drop-shadow-xl" viewBox="0 0 240 240" fill="none">
          {/* Backdrop decorative aura */}
          <circle cx="120" cy="120" r="90" fill="url(#hero-aura)" opacity="0.4" />
          <circle cx="120" cy="120" r="75" fill="white" fillOpacity="0.1" />

          {/* Floating educational icons */}
          {/* Graduation Cap */}
          <g transform="translate(145, 30) scale(0.9)">
            <rect x="0" y="0" width="46" height="46" rx="12" fill="white" fillOpacity="0.25" />
            <path d="M23 12L37 19L23 26L9 19L23 12Z" fill="#F4EBFF" />
            <path d="M14 22V30C14 30 18 34 23 34C28 34 32 30 32 30V22" stroke="#F4EBFF" strokeWidth="2" />
            <path d="M37 19V28" stroke="#F4EBFF" strokeWidth="1.5" />
          </g>

          {/* Book */}
          <g transform="translate(18, 50) scale(0.85)">
            <rect x="0" y="0" width="44" height="44" rx="12" fill="white" fillOpacity="0.25" />
            <path d="M12 16C12 14.8954 12.8954 14 14 14H22V32H14C12.8954 32 12 31.1046 12 30V16Z" fill="#E9D7FE" />
            <path d="M32 16C32 14.8954 31.1046 14 30 14H22V32H30C31.1046 32 32 31.1046 32 30V16Z" fill="#F4EBFF" />
          </g>

          {/* Student Character Avatar / Head & Laptop */}
          <ellipse cx="115" cy="190" rx="55" ry="24" fill="#3E1C96" fillOpacity="0.3" />
          {/* Torso */}
          <path d="M80 190C80 160 95 150 115 150C135 150 150 160 150 190" fill="#F4EBFF" />
          {/* Head & Hair */}
          <circle cx="115" cy="115" r="24" fill="#FEE4E2" />
          <path d="M96 115C96 98 106 92 118 92C130 92 136 100 136 112C130 110 124 114 116 110C108 106 102 110 96 115Z" fill="#344054" />
          {/* Spectacles */}
          <circle cx="109" cy="115" r="5" stroke="#344054" strokeWidth="1.5" />
          <circle cx="123" cy="115" r="5" stroke="#344054" strokeWidth="1.5" />
          <line x1="114" y1="115" x2="118" y2="115" stroke="#344054" strokeWidth="1.5" />

          {/* Laptop */}
          <rect x="85" y="165" width="60" height="32" rx="4" fill="#FFFFFF" />
          <rect x="90" y="170" width="50" height="22" rx="2" fill="#7F56D9" />
          <circle cx="115" cy="181" r="3" fill="#FFFFFF" fillOpacity="0.8" />
          <polygon points="75,198 155,198 145,192 85,192" fill="#D0D5DD" />

          {/* Sparkles */}
          <path d="M60 140L63 147L70 150L63 153L60 160L57 153L50 150L57 147L60 140Z" fill="#FEF08A" />
          <path d="M185 145L187 150L192 152L187 154L185 159L183 154L178 152L183 150L185 145Z" fill="#FEF08A" />

          <defs>
            <radialGradient id="hero-aura" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(120 120) rotate(90) scale(90)">
              <stop stopColor="white" stopOpacity="0.8" />
              <stop offset="1" stopColor="#7F56D9" stopOpacity="0" />
            </radialGradient>
          </defs>
        </svg>
      </div>
    </div>
  );
};
