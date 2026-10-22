import React from 'react';

interface StatItem {
  id: string;
  label: string;
  value: string;
  progressPercent: number;
}

const STATS: StatItem[] = [
  { id: 'completed', label: 'Courses completed', value: '04', progressPercent: 80 },
  { id: 'progress', label: 'Courses in progress', value: '02', progressPercent: 40 },
  { id: 'time', label: 'Total learning time', value: '18h', progressPercent: 75 },
  { id: 'streak', label: 'Daily learning streak', value: '5d', progressPercent: 85 },
];

export const StatsGrid: React.FC = () => {
  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2.5">
        <span className="text-xs font-bold text-slate-800 tracking-tight">Overview Progress</span>
        <span className="text-[10px] font-mono text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full border border-purple-100 font-semibold">
          Demo Profile
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {STATS.map((stat) => {
          // Circumference for r=20 circle is ~125.6
          const radius = 20;
          const circumference = 2 * Math.PI * radius;
          const strokeDashoffset = circumference - (stat.progressPercent / 100) * circumference;

          return (
            <div
              key={stat.id}
              className="bg-white rounded-2xl p-3 border border-slate-100 shadow-[0_2px_12px_rgba(0,0,0,0.02)] flex items-center justify-between gap-2"
            >
              {/* Text label */}
              <div className="flex flex-col pr-1">
                <span className="text-xs font-semibold text-slate-600 leading-tight">
                  {stat.label}
                </span>
              </div>

              {/* Purple Circular Progress Visual */}
              <div className="relative w-12 h-12 shrink-0 flex items-center justify-center">
                <svg className="w-12 h-12 -rotate-90" viewBox="0 0 48 48">
                  {/* Track circle */}
                  <circle
                    cx="24"
                    cy="24"
                    r={radius}
                    fill="transparent"
                    stroke="#F4EBFF"
                    strokeWidth="4"
                  />
                  {/* Progress arc */}
                  <circle
                    cx="24"
                    cy="24"
                    r={radius}
                    fill="transparent"
                    stroke="#7F56D9"
                    strokeWidth="4"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                  />
                </svg>
                {/* Center Value */}
                <span className="absolute text-[11px] font-extrabold text-[#6941C6] font-mono">
                  {stat.value}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
