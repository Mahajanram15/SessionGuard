import React, { useState } from 'react';
import { Search, SlidersHorizontal, Bell, ChevronDown, Check } from 'lucide-react';

interface TopHeaderProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onSearchSubmit: () => void;
  selectedCategory: string;
  onSelectCategory: (cat: string) => void;
  selectedDifficulty: string;
  onSelectDifficulty: (diff: string) => void;
}

const CATEGORIES = [
  'All',
  'Computer Science',
  'Machine Learning',
  'Cybersecurity',
  'Web Development',
  'Data Structures',
  'Cloud Computing',
];

const DIFFICULTIES = ['All', 'Beginner', 'Intermediate', 'Advanced'];

export const TopHeader: React.FC<TopHeaderProps> = ({
  searchQuery,
  onSearchChange,
  onSearchSubmit,
  selectedCategory,
  onSelectCategory,
  selectedDifficulty,
  onSelectDifficulty,
}) => {
  const [showFilters, setShowFilters] = useState(false);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onSearchSubmit();
    }
  };

  const hasActiveFilters = selectedCategory !== 'All' || selectedDifficulty !== 'All';

  return (
    <div className="w-full flex flex-col space-y-3">
      <div className="flex items-center justify-between gap-3 sm:gap-6">
        {/* Search Bar & Filter Toggle Button */}
        <div className="flex-1 flex items-center space-x-2.5 max-w-2xl">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search your course..."
              className="w-full bg-white text-slate-800 text-sm font-medium rounded-full pl-11 pr-4 py-2.5 sm:py-3 border border-slate-200/80 shadow-[0_2px_10px_rgba(0,0,0,0.02)] placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition-all"
            />
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            title="Toggle Category & Difficulty Filters"
            className={`w-10 h-10 sm:w-11 sm:h-11 rounded-full flex items-center justify-center border transition-all shrink-0 ${
              showFilters || hasActiveFilters
                ? 'bg-purple-600 text-white border-purple-600 shadow-md shadow-purple-500/20'
                : 'bg-white text-slate-600 border-slate-200/80 hover:bg-slate-50 shadow-[0_2px_10px_rgba(0,0,0,0.02)]'
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
          </button>
        </div>

        {/* Right Area: Notification Bell & Profile Pill */}
        <div className="flex items-center space-x-3 sm:space-x-4 shrink-0">
          {/* Notifications */}
          <button
            title="Notifications (2 New)"
            className="w-10 h-10 sm:w-11 sm:h-11 rounded-full bg-white border border-slate-200/80 shadow-[0_2px_10px_rgba(0,0,0,0.02)] flex items-center justify-center text-slate-600 hover:text-purple-600 hover:bg-slate-50 transition-colors relative"
          >
            <Bell className="w-4 h-4" />
            <span className="w-2 h-2 rounded-full bg-purple-600 absolute top-2.5 right-2.5 ring-2 ring-white" />
          </button>

          {/* Profile Pill */}
          <div className="flex items-center space-x-2.5 bg-white border border-slate-200/80 shadow-[0_2px_10px_rgba(0,0,0,0.02)] pl-1.5 pr-3 py-1 rounded-full cursor-pointer hover:border-slate-300 transition-colors">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold tracking-tight shadow-sm">
              AL
            </div>
            <div className="hidden md:flex flex-col text-left">
              <span className="text-xs font-bold text-slate-800 leading-tight">Alex Morgan</span>
              <span className="text-[10px] text-purple-600 font-semibold font-mono">Pro Learner</span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-0.5" />
          </div>
        </div>
      </div>

      {/* Expanded Filter Panel */}
      {showFilters && (
        <div className="bg-white rounded-2xl p-4 border border-purple-100 shadow-md shadow-purple-900/5 flex flex-col space-y-3 animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">Discipline Filter</span>
            {hasActiveFilters && (
              <button
                onClick={() => {
                  onSelectCategory('All');
                  onSelectDifficulty('All');
                }}
                className="text-[11px] text-purple-600 hover:text-purple-800 font-semibold"
              >
                Reset Filters
              </button>
            )}
          </div>

          {/* Categories */}
          <div className="flex flex-wrap gap-1.5">
            {CATEGORIES.map((cat) => {
              const active = selectedCategory === cat;
              return (
                <button
                  key={cat}
                  onClick={() => onSelectCategory(cat)}
                  className={`text-xs px-3 py-1.5 rounded-full font-medium transition-all ${
                    active
                      ? 'bg-purple-600 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {cat}
                </button>
              );
            })}
          </div>

          {/* Difficulty */}
          <div className="flex items-center space-x-2 pt-2 border-t border-slate-100">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Level:</span>
            {DIFFICULTIES.map((diff) => {
              const active = selectedDifficulty === diff;
              return (
                <button
                  key={diff}
                  onClick={() => onSelectDifficulty(diff)}
                  className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-all flex items-center space-x-1 ${
                    active
                      ? 'bg-purple-100 text-purple-700 font-bold'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {active && <Check className="w-3 h-3" />}
                  <span>{diff}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
