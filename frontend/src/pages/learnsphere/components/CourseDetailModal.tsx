import React, { useState, useEffect } from 'react';
import { X, Star, Clock, CheckCircle, Loader2, Play } from 'lucide-react';
import { CourseItem, CourseDetailResponse } from '../../../types';
import { AppApiClient } from '../../../services/api';
import { CourseThumbnail } from './CourseThumbnails';

interface CourseDetailModalProps {
  course: CourseItem | null;
  onClose: () => void;
  appClient: AppApiClient;
  onStartLearning?: (course: CourseItem, lessonId?: string) => void;
}

export const CourseDetailModal: React.FC<CourseDetailModalProps> = ({
  course,
  onClose,
  appClient,
  onStartLearning,
}) => {
  const [details, setDetails] = useState<CourseDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!course) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    appClient.getCourseDetails(course.id)
      .then((res) => {
        if (!isMounted) return;
        if (res.data) {
          setDetails(res.data);
        } else {
          setError(res.error?.message || 'Failed to load course details');
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Error fetching course details');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [course, appClient]);

  if (!course) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-150">
      <div className="bg-white rounded-[28px] max-w-2xl w-full border border-slate-100 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="relative p-6 bg-gradient-to-r from-purple-50 via-slate-50 to-indigo-50 border-b border-slate-100 flex items-start justify-between">
          <div className="flex items-center space-x-4 pr-6">
            <div className="w-16 h-16 rounded-2xl overflow-hidden shrink-0 shadow-md">
              <CourseThumbnail category={course.category} className="w-full h-full" />
            </div>
            <div>
              <div className="flex items-center space-x-2 mb-1">
                <span className="px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-700 text-xs font-bold font-mono">
                  {course.category}
                </span>
                <span className="text-xs text-slate-500 font-semibold">•</span>
                <span className="text-xs text-slate-600 font-medium">{course.difficulty}</span>
              </div>
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 leading-tight">
                {course.title}
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white hover:bg-slate-100 text-slate-400 hover:text-slate-600 flex items-center justify-center border border-slate-200 transition-colors shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center space-y-3">
              <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
              <p className="text-xs text-slate-500 font-medium">Fetching syllabus & lesson roadmap...</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-50 border border-rose-100 rounded-xl text-rose-700 text-xs font-medium">
              {error}
            </div>
          ) : details ? (
            <>
              {/* Course Meta Cards */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Duration</span>
                  <span className="text-sm font-bold text-slate-800 mt-1 flex items-center space-x-1">
                    <Clock className="w-3.5 h-3.5 text-purple-600" />
                    <span>{details.duration_hours} Hours</span>
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Rating</span>
                  <span className="text-sm font-bold text-slate-800 mt-1 flex items-center space-x-1">
                    <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                    <span>{details.rating.toFixed(1)} ({details.review_count} reviews)</span>
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Students</span>
                  <span className="text-sm font-bold text-slate-800 mt-1">
                    {details.enrollment_count.toLocaleString()} enrolled
                  </span>
                </div>
              </div>

              {/* Description */}
              <div>
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Course Overview
                </h4>
                <p className="text-sm text-slate-600 leading-relaxed">
                  {details.description}
                </p>
              </div>

              {/* Learning Objectives */}
              {details.learning_objectives.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2.5">
                    What You'll Learn
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {details.learning_objectives.map((obj, i) => (
                      <div key={i} className="flex items-start space-x-2 text-xs text-slate-700">
                        <CheckCircle className="w-3.5 h-3.5 text-purple-600 shrink-0 mt-0.5" />
                        <span>{obj}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Curriculum Lessons */}
              <div>
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2.5 flex items-center justify-between">
                  <span>Curriculum ({details.lessons.length} Modules)</span>
                  <span className="text-[11px] font-normal text-slate-500 font-mono">Structured Syllabus</span>
                </h4>
                <div className="space-y-2">
                  {details.lessons.map((lesson) => (
                    <div
                      key={lesson.id}
                      onClick={() => onStartLearning && onStartLearning(course, lesson.id)}
                      className={`p-3 rounded-xl border border-slate-100 bg-slate-50/50 hover:bg-white transition-all flex items-center justify-between ${
                        onStartLearning ? 'cursor-pointer hover:border-purple-300 hover:shadow-sm' : ''
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-7 h-7 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold">
                          {lesson.order}
                        </div>
                        <div>
                          <h5 className="text-xs font-bold text-slate-900">{lesson.title}</h5>
                          <p className="text-[11px] text-slate-500 line-clamp-1">{lesson.description}</p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2 shrink-0 text-[11px] text-slate-400 font-mono">
                        <span>{lesson.duration_minutes}m</span>
                        {lesson.quiz && (
                          <span className="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 font-semibold border border-purple-100">
                            Quiz
                          </span>
                        )}
                        {onStartLearning && (
                          <span className="text-purple-600 font-bold text-xs pl-1">
                            Play →
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-500">Instructor:</span>
            <span className="text-xs font-bold text-slate-800">{course.instructor}</span>
            <span className="text-[11px] text-purple-600 font-semibold px-2.5 py-0.5 rounded-full bg-purple-50 border border-purple-100">
              Syllabus Preview Mode
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2.5 rounded-full text-xs font-bold bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 shadow-sm transition-all cursor-pointer"
            >
              Close Preview
            </button>
            {onStartLearning && (
              <button
                onClick={() => onStartLearning(course, details?.lessons[0]?.id)}
                className="px-5 py-2.5 rounded-full text-xs font-bold bg-[#6941C6] hover:bg-[#53389E] text-white shadow-md shadow-purple-600/20 hover:shadow-lg transition-all cursor-pointer flex items-center space-x-1.5"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Start Learning</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

