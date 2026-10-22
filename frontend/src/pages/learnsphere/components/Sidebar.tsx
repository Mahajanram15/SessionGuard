import React from 'react';
import {
  Home,
  BookOpen,
  Calendar,
  Award,
  Users,
  MessageSquare,
  Settings,
  LogOut,
  GraduationCap,
} from 'lucide-react';

interface SidebarProps {
  activeTab?: string;
  onNavigate?: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab = 'home', onNavigate }) => {
  const navItems = [
    { id: 'home', icon: Home, label: 'Home' },
    { id: 'courses', icon: BookOpen, label: 'Courses' },
    { id: 'calendar', icon: Calendar, label: 'Schedule' },
    { id: 'assessments', icon: Award, label: 'Achievements' },
    { id: 'community', icon: Users, label: 'Community' },
    { id: 'messages', icon: MessageSquare, label: 'Messages' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <aside className="w-16 sm:w-20 bg-white rounded-[28px] py-6 px-2 flex flex-col items-center justify-between border border-slate-100 shadow-[0_10px_30px_rgba(0,0,0,0.03)] shrink-0 self-stretch min-h-[780px]">
      {/* Brand Icon */}
      <div className="flex flex-col items-center space-y-8">
        <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-[#6941C6] to-[#9E77ED] flex items-center justify-center shadow-md shadow-purple-500/20 text-white cursor-pointer hover:scale-105 transition-transform" title="LearnSphere Platform">
          <GraduationCap className="w-6 h-6 stroke-[2.2]" />
        </div>

        {/* Navigation Items */}
        <nav className="flex flex-col items-center space-y-3.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate?.(item.id)}
                title={item.label}
                className={`w-11 h-11 rounded-2xl flex items-center justify-center transition-all ${
                  isActive
                    ? 'bg-purple-100/90 text-purple-700 shadow-sm shadow-purple-200/50'
                    : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'stroke-[2.5]' : 'stroke-[1.8]'}`} />
              </button>
            );
          })}
        </nav>
      </div>

      {/* Logout Action */}
      <div className="pt-6 border-t border-slate-100 w-full flex justify-center">
        <button
          onClick={() => alert('Demo Session Active: LearnSphere is currently running in CrossTrace telemetry verification mode.')}
          title="Sign Out (Demo)"
          className="w-11 h-11 rounded-2xl flex items-center justify-center text-slate-400 hover:text-rose-500 hover:bg-rose-50 transition-colors"
        >
          <LogOut className="w-5 h-5 stroke-[1.8]" />
        </button>
      </div>
    </aside>
  );
};
