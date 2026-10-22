import React, { useState, useEffect, useMemo } from 'react';
import {
  ArrowLeft,
  CheckCircle2,
  Circle,
  Clock,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  ShieldCheck,
  Award,
  Layers,
  GraduationCap,
  Loader2,
} from 'lucide-react';
import { CourseItem, CourseDetailResponse, LessonItem, QuizAttempt, CourseProgressRecord } from '../../../types';
import { AppApiClient } from '../../../services/api';
import { QuizView } from './QuizView';

interface LessonPlayerViewProps {
  course: CourseItem;
  initialLessonId?: string;
  appClient: AppApiClient;
  progressRecord?: CourseProgressRecord;
  onToggleCompleteLesson: (courseId: string, lessonId: string) => void;
  onRecordQuizAttempt: (courseId: string, attempt: QuizAttempt) => void;
  onBackToCatalog: () => void;
  onOpenCourseDetails?: () => void;
}

export const LessonPlayerView: React.FC<LessonPlayerViewProps> = ({
  course,
  initialLessonId,
  appClient,
  progressRecord,
  onToggleCompleteLesson,
  onRecordQuizAttempt,
  onBackToCatalog,
  onOpenCourseDetails,
}) => {
  const [courseDetails, setCourseDetails] = useState<CourseDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLessonId, setSelectedLessonId] = useState<string>(initialLessonId || '');

  // Fetch full course details if needed
  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    appClient
      .getCourseDetails(course.id)
      .then((res) => {
        if (!isMounted) return;
        if (res.data) {
          setCourseDetails(res.data);
          // Default to initialLessonId or first lesson
          if (!selectedLessonId && res.data.lessons.length > 0) {
            setSelectedLessonId(res.data.lessons[0].id);
          } else if (selectedLessonId) {
            // Verify initialLessonId exists in lessons
            const exists = res.data.lessons.some((l) => l.id === selectedLessonId);
            if (!exists && res.data.lessons.length > 0) {
              setSelectedLessonId(res.data.lessons[0].id);
            }
          }
        } else {
          setError(res.error?.message || 'Failed to load course curriculum.');
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Error fetching course details.');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [course.id, appClient]);

  // Sync selectedLessonId when initialLessonId changes
  useEffect(() => {
    if (initialLessonId) {
      setSelectedLessonId(initialLessonId);
    }
  }, [initialLessonId]);

  const lessons = useMemo(() => courseDetails?.lessons || [], [courseDetails]);

  const currentLessonIndex = useMemo(() => {
    return lessons.findIndex((l) => l.id === selectedLessonId);
  }, [lessons, selectedLessonId]);

  const currentLesson: LessonItem | undefined = useMemo(() => {
    if (currentLessonIndex >= 0) return lessons[currentLessonIndex];
    return lessons[0];
  }, [lessons, currentLessonIndex]);

  // Derived progress values
  const completedLessonIds = useMemo(() => progressRecord?.completedLessonIds || [], [progressRecord]);
  const quizAttempts = useMemo(() => progressRecord?.quizAttempts || {}, [progressRecord]);

  const totalLessonsCount = lessons.length;
  const completedLessonsCount = useMemo(() => {
    return completedLessonIds.filter((id) => lessons.some((l) => l.id === id)).length;
  }, [completedLessonIds, lessons]);

  const progressPercentage = useMemo(() => {
    if (totalLessonsCount === 0) return 0;
    return Math.round((completedLessonsCount / totalLessonsCount) * 100);
  }, [completedLessonsCount, totalLessonsCount]);

  const isCurrentLessonCompleted = useMemo(() => {
    if (!currentLesson) return false;
    return completedLessonIds.includes(currentLesson.id);
  }, [completedLessonIds, currentLesson]);

  const currentLessonQuizAttempt = useMemo(() => {
    if (!currentLesson) return undefined;
    return quizAttempts[currentLesson.id];
  }, [quizAttempts, currentLesson]);

  // Navigation handlers
  const handleSelectLesson = (lessonId: string) => {
    setSelectedLessonId(lessonId);
  };

  const handlePrevLesson = () => {
    if (currentLessonIndex > 0) {
      setSelectedLessonId(lessons[currentLessonIndex - 1].id);
    }
  };

  const handleNextLesson = () => {
    if (currentLessonIndex < lessons.length - 1) {
      setSelectedLessonId(lessons[currentLessonIndex + 1].id);
    }
  };

  const handleToggleCurrentLesson = () => {
    if (!currentLesson) return;
    onToggleCompleteLesson(course.id, currentLesson.id);
  };

  const handleQuizComplete = (attempt: QuizAttempt) => {
    onRecordQuizAttempt(course.id, attempt);
    // Automatically mark lesson completed if passed
    if (attempt.passed && currentLesson && !isCurrentLessonCompleted) {
      onToggleCompleteLesson(course.id, currentLesson.id);
    }
  };

  return (
    <div className="min-h-screen bg-[#ECEAF6] p-2.5 sm:p-5 lg:p-7 relative overflow-x-hidden flex justify-center items-start font-sans">
      {/* Decorative Gradient Blooms */}
      <div className="absolute -top-32 -left-32 w-96 h-96 bg-purple-300/35 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 -right-32 w-[30rem] h-[30rem] bg-indigo-300/30 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 left-1/4 w-80 h-80 bg-purple-200/40 rounded-full blur-3xl pointer-events-none" />

      {/* Main Dashboard Surface */}
      <div className="max-w-[1400px] w-full bg-[#FAFAFE] rounded-[36px] shadow-[0_20px_60px_-15px_rgba(79,70,229,0.07)] border border-white/80 p-4 sm:p-6 lg:p-8 flex flex-col space-y-6 relative z-10">
        {/* Navigation & Header Bar */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-200/70">
          <div className="flex items-center space-x-3">
            <button
              onClick={onBackToCatalog}
              className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-full bg-white hover:bg-slate-100 text-slate-700 hover:text-purple-700 text-xs font-bold border border-slate-200/90 shadow-sm transition-all cursor-pointer group"
              title="Return to Course Catalog"
            >
              <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
              <span>Catalog</span>
            </button>

            {/* Breadcrumb Navigation */}
            <nav className="flex items-center space-x-2 text-xs" aria-label="Breadcrumb">
              <span className="text-slate-400 font-medium hidden sm:inline">Courses</span>
              <span className="text-slate-300 hidden sm:inline">/</span>
              <button
                onClick={onOpenCourseDetails}
                className="font-bold text-slate-800 hover:text-purple-600 transition-colors truncate max-w-[220px] sm:max-w-xs text-left"
                title="View Course Syllabus"
              >
                {course.title}
              </button>
              {currentLesson && (
                <>
                  <span className="text-slate-300">/</span>
                  <span className="text-purple-700 font-semibold truncate max-w-[180px] sm:max-w-xs bg-purple-50 px-2 py-0.5 rounded-md border border-purple-100 font-mono">
                    Module {currentLesson.order}: {currentLesson.title}
                  </span>
                </>
              )}
            </nav>
          </div>

          {/* Course Progress Summary Bar */}
          <div className="flex items-center space-x-3 self-end md:self-auto bg-white px-4 py-2 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="flex flex-col text-right">
              <div className="flex items-center space-x-1.5 justify-end">
                <span className="text-[11px] font-bold text-slate-700">Course Progress:</span>
                <span className="text-xs font-mono font-extrabold text-purple-700">
                  {completedLessonsCount}/{totalLessonsCount}
                </span>
                <span className="text-[11px] text-slate-500 font-mono font-semibold">
                  ({progressPercentage}%)
                </span>
              </div>
              <div className="w-36 h-2 bg-slate-100 rounded-full overflow-hidden mt-1">
                <div
                  className="h-full bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full transition-all duration-300"
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
            </div>

            <div className="pl-2 border-l border-slate-200">
              <span
                className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block"
                title="Progress is tracked locally in current browser session"
              >
                Local Demo
              </span>
            </div>
          </div>
        </header>

        {/* Loading / Error States */}
        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
            <p className="text-xs text-slate-500 font-medium">Loading lesson curriculum and content...</p>
          </div>
        ) : error ? (
          <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 text-sm">
            <div className="font-bold mb-1">Failed to Load Lesson Curriculum</div>
            <p className="text-xs">{error}</p>
            <button
              onClick={onBackToCatalog}
              className="mt-4 px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-semibold hover:bg-rose-700 transition-colors"
            >
              Return to Catalog
            </button>
          </div>
        ) : !currentLesson ? (
          <div className="p-8 bg-white rounded-2xl border border-slate-200 text-center">
            <BookOpen className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <h3 className="text-sm font-bold text-slate-800">No Lessons Found</h3>
            <p className="text-xs text-slate-500 mt-1">This course does not currently contain active lesson modules.</p>
          </div>
        ) : (
          /* Main 2-Column Responsive Workspace */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Lesson Player, Content Panel & Quiz (8 Cols) */}
            <div className="lg:col-span-8 flex flex-col space-y-6 min-w-0">
              {/* Lesson Card Container */}
              <div className="bg-white rounded-[28px] border border-slate-200/80 shadow-sm overflow-hidden flex flex-col">
                {/* Lesson Header */}
                <div className="p-6 bg-gradient-to-r from-purple-50/70 via-white to-indigo-50/60 border-b border-slate-100 flex flex-col space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className="px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 text-[11px] font-bold font-mono border border-purple-200">
                        Module {currentLesson.order} of {totalLessonsCount}
                      </span>
                      <span className="flex items-center space-x-1 text-slate-500 text-xs font-medium bg-white px-2.5 py-0.5 rounded-full border border-slate-200 font-mono">
                        <Clock className="w-3 h-3 text-purple-600" />
                        <span>{currentLesson.duration_minutes} Minutes</span>
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      {isCurrentLessonCompleted ? (
                        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Completed</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-semibold">
                          <Circle className="w-3 h-3 text-slate-400" />
                          <span>In Progress</span>
                        </span>
                      )}
                    </div>
                  </div>

                  <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 leading-tight">
                    {currentLesson.title}
                  </h1>

                  <p className="text-sm text-slate-600 leading-relaxed max-w-3xl">
                    {currentLesson.description}
                  </p>
                </div>

                {/* Lesson Content / Visual Panel */}
                <div className="p-6 space-y-6">
                  {/* Interactive Conceptual Lecture Area (No broken video elements) */}
                  <div className="rounded-2xl border border-purple-100 bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 text-white p-6 sm:p-8 relative overflow-hidden shadow-inner">
                    {/* Background Visual Grid Pattern */}
                    <div className="absolute inset-0 bg-[radial-gradient(#4f46e5_1px,transparent_1px)] [background-size:16px_16px] opacity-20 pointer-events-none" />

                    <div className="relative z-10 flex flex-col space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="inline-flex items-center space-x-2 bg-purple-500/20 backdrop-blur-md px-3 py-1 rounded-full border border-purple-400/30 text-purple-200 text-[11px] font-semibold">
                          <Sparkles className="w-3.5 h-3.5 text-purple-300" />
                          <span>Interactive Demo Lesson • Telemetry Verified</span>
                        </div>

                        <span className="text-[10px] uppercase font-mono tracking-widest text-purple-300/80">
                          CrossTrace Verified Session
                        </span>
                      </div>

                      <div className="py-2">
                        <span className="text-xs uppercase tracking-wider font-semibold text-purple-300">
                          Focus Concept • {course.category}
                        </span>
                        <h3 className="text-lg sm:text-xl font-bold text-white mt-1">
                          {currentLesson.title}
                        </h3>
                        <p className="text-xs sm:text-sm text-slate-300 mt-2 max-w-2xl leading-relaxed">
                          This module introduces core architectural principles and verified behavioral paradigms.
                          Review the curriculum objectives below and complete the knowledge check to cement your understanding.
                        </p>
                      </div>

                      {/* Lesson Highlights Grid */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                        <div className="bg-white/5 border border-white/10 rounded-xl p-3 backdrop-blur-sm">
                          <div className="flex items-center space-x-2 text-purple-300 text-xs font-semibold mb-1">
                            <Layers className="w-3.5 h-3.5" />
                            <span>Structured Concept</span>
                          </div>
                          <p className="text-[11px] text-slate-300 line-clamp-2">
                            {currentLesson.description}
                          </p>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-xl p-3 backdrop-blur-sm">
                          <div className="flex items-center space-x-2 text-indigo-300 text-xs font-semibold mb-1">
                            <Clock className="w-3.5 h-3.5" />
                            <span>Pacing & Review</span>
                          </div>
                          <p className="text-[11px] text-slate-300">
                            {currentLesson.duration_minutes} minutes recommended study time.
                          </p>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-xl p-3 backdrop-blur-sm">
                          <div className="flex items-center space-x-2 text-emerald-300 text-xs font-semibold mb-1">
                            <Award className="w-3.5 h-3.5" />
                            <span>Assessment</span>
                          </div>
                          <p className="text-[11px] text-slate-300">
                            {currentLesson.quiz && currentLesson.quiz.length > 0
                              ? `${currentLesson.quiz.length} Knowledge Check questions`
                              : 'Conceptual mastery checkpoint'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Course Objectives Context for this Lesson */}
                  {courseDetails?.learning_objectives && courseDetails.learning_objectives.length > 0 && (
                    <div className="bg-slate-50/80 rounded-2xl p-5 border border-slate-100">
                      <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2.5 flex items-center space-x-2">
                        <GraduationCap className="w-4 h-4 text-purple-600" />
                        <span>Key Course Competencies Addressed</span>
                      </h4>
                      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-600">
                        {courseDetails.learning_objectives.slice(0, 4).map((obj, i) => (
                          <li key={i} className="flex items-start space-x-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-purple-500 mt-1.5 shrink-0" />
                            <span>{obj}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Interactive Knowledge-Check Quiz Section */}
                  <div className="pt-2">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-base font-bold text-slate-900 tracking-tight">
                          Knowledge-Check Quiz
                        </h3>
                        {currentLesson.quiz && currentLesson.quiz.length > 0 && (
                          <span className="text-[11px] font-semibold text-purple-700 bg-purple-50 px-2.5 py-0.5 rounded-full border border-purple-100 font-mono">
                            {currentLesson.quiz.length} Questions
                          </span>
                        )}
                      </div>

                      {currentLessonQuizAttempt && (
                        <div className="flex items-center space-x-1.5 text-xs font-bold">
                          <span className="text-slate-500 font-medium">Best Score:</span>
                          <span
                            className={`px-2 py-0.5 rounded-full font-mono ${
                              currentLessonQuizAttempt.passed
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : 'bg-amber-50 text-amber-700 border border-amber-200'
                            }`}
                          >
                            {currentLessonQuizAttempt.score}%
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Quiz Component */}
                    <QuizView
                      key={currentLesson.id}
                      questions={currentLesson.quiz}
                      lessonId={currentLesson.id}
                      onQuizComplete={handleQuizComplete}
                      previousAttempt={currentLessonQuizAttempt}
                    />
                  </div>
                </div>

                {/* Lesson Footer Navigation Controls */}
                <div className="p-4 sm:p-6 bg-slate-50 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                  {/* Mark as Complete Button */}
                  <button
                    onClick={handleToggleCurrentLesson}
                    className={`inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all shadow-sm cursor-pointer ${
                      isCurrentLessonCompleted
                        ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200 border border-emerald-300'
                        : 'bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 hover:border-purple-300'
                    }`}
                  >
                    <CheckCircle2
                      className={`w-4 h-4 ${
                        isCurrentLessonCompleted ? 'text-emerald-700' : 'text-slate-400'
                      }`}
                    />
                    <span>
                      {isCurrentLessonCompleted ? 'Completed ✓ (Click to Undo)' : 'Mark Lesson as Complete'}
                    </span>
                  </button>

                  {/* Previous / Next Lesson Controls */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handlePrevLesson}
                      disabled={currentLessonIndex <= 0}
                      className="inline-flex items-center space-x-1.5 px-3.5 py-2.5 rounded-xl text-xs font-bold bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:pointer-events-none transition-all shadow-sm cursor-pointer"
                      title={currentLessonIndex > 0 ? 'Go to previous lesson' : 'At first lesson'}
                    >
                      <ChevronLeft className="w-4 h-4" />
                      <span>Previous</span>
                    </button>

                    <button
                      onClick={handleNextLesson}
                      disabled={currentLessonIndex >= lessons.length - 1}
                      className="inline-flex items-center space-x-1.5 px-4 py-2.5 rounded-xl text-xs font-bold bg-[#6941C6] hover:bg-[#53389E] text-white disabled:opacity-40 disabled:pointer-events-none shadow-md shadow-purple-600/20 hover:shadow-lg transition-all cursor-pointer"
                      title={
                        currentLessonIndex < lessons.length - 1
                          ? 'Go to next lesson'
                          : 'At last lesson'
                      }
                    >
                      <span>Next Lesson</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Curriculum Sidebar & Session Progress (4 Cols) */}
            <div className="lg:col-span-4 flex flex-col space-y-5 min-w-0">
              {/* Curriculum List Card */}
              <div className="bg-white rounded-[28px] border border-slate-200/80 shadow-sm p-5 flex flex-col space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div>
                    <h2 className="text-sm font-extrabold text-slate-900 tracking-tight">
                      Course Curriculum
                    </h2>
                    <span className="text-[11px] text-slate-400 font-medium">
                      {lessons.length} Modules • {course.duration_hours}h Total
                    </span>
                  </div>
                  <span className="text-xs font-mono font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded-full border border-purple-100">
                    {completedLessonsCount}/{lessons.length} Done
                  </span>
                </div>

                {/* Lesson Navigation List */}
                <div className="flex flex-col space-y-2 max-h-[520px] overflow-y-auto pr-1">
                  {lessons.map((lesson) => {
                    const isSelected = lesson.id === currentLesson.id;
                    const isCompleted = completedLessonIds.includes(lesson.id);
                    const attempt = quizAttempts[lesson.id];

                    return (
                      <button
                        key={lesson.id}
                        onClick={() => handleSelectLesson(lesson.id)}
                        className={`w-full text-left p-3.5 rounded-2xl border transition-all flex items-start space-x-3 cursor-pointer ${
                          isSelected
                            ? 'bg-purple-50/80 border-purple-300 ring-2 ring-purple-500/20 shadow-sm'
                            : 'bg-white hover:bg-slate-50/80 border-slate-100 hover:border-slate-200'
                        }`}
                      >
                        {/* Status Icon / Order Badge */}
                        <div className="shrink-0 mt-0.5">
                          {isCompleted ? (
                            <div className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs">
                              <CheckCircle2 className="w-4 h-4" />
                            </div>
                          ) : isSelected ? (
                            <div className="w-7 h-7 rounded-lg bg-[#6941C6] text-white flex items-center justify-center font-bold text-xs shadow-sm shadow-purple-600/30">
                              {lesson.order}
                            </div>
                          ) : (
                            <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center font-semibold text-xs">
                              {lesson.order}
                            </div>
                          )}
                        </div>

                        {/* Title & Metadata */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-1">
                            <span
                              className={`text-xs font-bold leading-snug line-clamp-1 ${
                                isSelected ? 'text-purple-900' : 'text-slate-800'
                              }`}
                            >
                              {lesson.title}
                            </span>
                          </div>

                          <div className="flex items-center space-x-2 mt-1">
                            <span className="text-[11px] text-slate-400 font-mono">
                              {lesson.duration_minutes}m
                            </span>
                            {lesson.quiz && lesson.quiz.length > 0 && (
                              <span className="text-[10px] text-purple-600 bg-purple-50 px-1.5 py-0.2 rounded font-semibold font-mono border border-purple-100">
                                Quiz
                              </span>
                            )}
                            {attempt && (
                              <span
                                className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                                  attempt.passed
                                    ? 'bg-emerald-50 text-emerald-700'
                                    : 'bg-amber-50 text-amber-700'
                                }`}
                              >
                                {attempt.score}%
                              </span>
                            )}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Demo Session Verification Card */}
              <div className="bg-white rounded-[28px] border border-slate-200/80 shadow-sm p-5 space-y-3">
                <div className="flex items-center space-x-2 text-purple-700">
                  <ShieldCheck className="w-4 h-4 text-purple-600 shrink-0" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    Session Behavioral Verification
                  </h3>
                </div>

                <p className="text-xs text-slate-500 leading-relaxed">
                  LearnSphere runs with CrossTrace behavioral telemetry enabled. Interaction dynamics
                  (mouse timing, key intervals) verify human presence without capturing quiz answers or student PII.
                </p>

                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                  <span className="text-slate-500 font-medium">Session Status:</span>
                  <span className="font-mono font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                    Telemetry Active
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
