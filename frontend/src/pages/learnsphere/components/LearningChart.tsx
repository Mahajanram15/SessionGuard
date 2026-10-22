import React, { useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { ChevronDown } from 'lucide-react';

const WEEKLY_DATA = [
  { day: 'Mon', hours: 2.5, courses: 2 },
  { day: 'Tue', hours: 3.8, courses: 3 },
  { day: 'Wed', hours: 1.8, courses: 1 },
  { day: 'Thu', hours: 4.5, courses: 4 },
  { day: 'Fri', hours: 3.2, courses: 2 },
  { day: 'Sat', hours: 5.0, courses: 3 },
  { day: 'Sun', hours: 4.0, courses: 2 },
];

export const LearningChart: React.FC = () => {
  const [activeMetric, setActiveMetric] = useState<'hours' | 'courses'>('hours');
  const [timeframe, setTimeframe] = useState<string>('Weekly');

  return (
    <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] flex flex-col space-y-3">
      {/* Header with Title, Tabs, and Dropdown */}
      <div className="flex items-center justify-between pb-1 border-b border-slate-50">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Your statistics</h3>
          <p className="text-[10px] text-slate-400">Illustrative learning activity</p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Timeframe Dropdown */}
          <div className="relative inline-flex items-center">
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="appearance-none bg-slate-50 hover:bg-slate-100 border border-slate-200/80 rounded-lg pl-2.5 pr-6 py-1 text-[11px] font-semibold text-slate-700 cursor-pointer focus:outline-none focus:ring-1 focus:ring-purple-500"
            >
              <option value="Weekly">Weekly</option>
              <option value="Monthly">Monthly</option>
            </select>
            <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 bg-slate-100/70 p-1 rounded-xl self-start">
        <button
          onClick={() => setActiveMetric('hours')}
          className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
            activeMetric === 'hours'
              ? 'bg-white text-purple-700 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          Learning Hours
        </button>
        <button
          onClick={() => setActiveMetric('courses')}
          className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
            activeMetric === 'courses'
              ? 'bg-white text-purple-700 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          My Courses
        </button>
      </div>

      {/* Chart Canvas */}
      <div className="h-44 w-full pt-1">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={WEEKLY_DATA} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="purpleGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#7F56D9" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#7F56D9" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="day"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: '#94A3B8', fontWeight: 500 }}
              dy={5}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: '#94A3B8' }}
              domain={[0, 'auto']}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const val = payload[0].value;
                  return (
                    <div className="bg-slate-900 text-white text-[11px] font-bold px-2.5 py-1 rounded-lg shadow-lg">
                      {val} {activeMetric === 'hours' ? 'hours' : 'modules'}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey={activeMetric}
              stroke="#7F56D9"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#purpleGradient)"
              dot={{ stroke: '#7F56D9', strokeWidth: 2, fill: '#FFFFFF', r: 3.5 }}
              activeDot={{ r: 5, fill: '#7F56D9', stroke: '#FFFFFF', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
