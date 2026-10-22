import React from 'react';
import { Star, ArrowRight, Clock } from 'lucide-react';
import { CourseItem } from '../../../types';
import { CourseThumbnail } from './CourseThumbnails';

interface CourseCardProps {
  course: CourseItem;
  onSelect: (course: CourseItem) => void;
  compact?: boolean;
}

export const CourseCard: React.FC<CourseCardProps> = ({ course, onSelect, compact: _compact = false }) => {
  return (
    <div
      onClick={() => onSelect(course)}
      className="bg-white rounded-2xl p-3 border border-slate-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] hover:shadow-[0_8px_25px_rgba(105,65,198,0.08)] hover:border-purple-100 transition-all flex flex-col justify-between cursor-pointer group"
    >
      {/* Top Banner Thumbnail with Category & Rating Badges */}
      <div className="relative w-full rounded-xl overflow-hidden mb-3">
        <CourseThumbnail category={course.category} className="w-full h-32 object-cover transition-transform duration-300 group-hover:scale-105" />

        {/* Floating Category Pill */}
        <div className="absolute top-2 left-2 px-2.5 py-1 rounded-full bg-white/95 backdrop-blur-sm text-[11px] font-bold text-slate-800 shadow-sm">
          {course.category}
        </div>

        {/* Floating Rating Pill */}
        <div className="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-slate-900/80 backdrop-blur-sm text-[10px] font-bold text-amber-300 flex items-center space-x-1 shadow-sm">
          <Star className="w-3 h-3 fill-amber-300 text-amber-300" />
          <span>{course.rating.toFixed(1)}</span>
        </div>
      </div>

      {/* Main Content Info */}
      <div className="flex-1 flex flex-col justify-between">
        <div>
          <div className="flex items-center space-x-2 text-[11px] text-slate-400 mb-1 font-medium">
            <span className="flex items-center space-x-1">
              <Clock className="w-3 h-3 text-purple-600" />
              <span>{course.duration_hours} hrs</span>
            </span>
            <span>•</span>
            <span className="text-purple-600 font-semibold">{course.difficulty}</span>
          </div>

          <h3 className="text-sm font-bold text-slate-900 group-hover:text-purple-700 transition-colors line-clamp-2 leading-snug">
            {course.title}
          </h3>
        </div>

        {/* Instructor & Action Footer */}
        <div className="mt-3.5 pt-2.5 border-t border-slate-50 flex items-center justify-between">
          <div className="flex items-center space-x-2 overflow-hidden pr-2">
            <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
              {course.instructor.charAt(0)}
            </div>
            <span className="text-xs text-slate-600 font-medium truncate">
              {course.instructor.split(',')[0]}
            </span>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <span className={`text-xs font-bold ${course.is_free ? 'text-emerald-600' : 'text-purple-700 font-mono'}`}>
              {course.is_free ? 'Free' : `$${course.price.toFixed(2)}`}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onSelect(course);
              }}
              title="View Course Details"
              className="w-7 h-7 rounded-full bg-purple-600 group-hover:bg-purple-700 text-white flex items-center justify-center shadow-sm shadow-purple-500/20 transition-transform group-hover:scale-105"
            >
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
