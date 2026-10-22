import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopHeader } from './components/TopHeader';
import { HeroBanner } from './components/HeroBanner';
import { CourseCard } from './components/CourseCard';
import { StatsGrid } from './components/StatsGrid';
import { LearningChart } from './components/LearningChart';
import { PromoCard } from './components/PromoCard';
import { CourseDetailModal } from './components/CourseDetailModal';
import { CourseItem } from '../../types';
import { AppApiClient } from '../../services/api';
import { ChevronLeft, ChevronRight, Loader2, BookOpen } from 'lucide-react';

interface LearnSphereLandingPageProps {
  appClient: AppApiClient;
  onExploreCatalog?: () => void;
}

export const LearnSphereLandingPage: React.FC<LearnSphereLandingPageProps> = ({
  appClient,
  onExploreCatalog: _onExploreCatalog,
}) => {
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('All');
  const [selectedCourse, setSelectedCourse] = useState<CourseItem | null>(null);

  // Carousel page state for Popular Courses section
  const [popularCarouselIndex, setPopularCarouselIndex] = useState<number>(0);

  const coursesSectionRef = useRef<HTMLDivElement>(null);

  // Fetch courses with current filters
  const loadCourses = async (query = '', category = 'All', difficulty = 'All') => {
    setLoading(true);
    try {
      if (query.trim()) {
        const res = await appClient.searchCourses(query.trim(), 10);
        if (res.data) {
          setCourses(res.data.results);
        }
      } else {
        const params: Record<string, any> = { page: 1, page_size: 20 };
        if (category !== 'All') params.category = category;
        if (difficulty !== 'All') params.difficulty = difficulty;

        const res = await appClient.getCourses(params);
        if (res.data) {
          setCourses(res.data.courses);
        }
      }
    } catch (err) {
      console.error('Failed to load courses:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCourses(searchQuery, selectedCategory, selectedDifficulty);
  }, [selectedCategory, selectedDifficulty]);

  const handleSearchSubmit = () => {
    loadCourses(searchQuery, selectedCategory, selectedDifficulty);
  };

  // Divide courses between "My Courses" (2 items) and "Popular Courses" (remaining items)
  const myCourses = useMemo(() => {
    if (courses.length <= 2) return courses;
    return courses.slice(0, 2);
  }, [courses]);

  const popularCoursesPool = useMemo(() => {
    if (courses.length <= 2) return [];
    return courses.slice(2);
  }, [courses]);

  // Display 3 cards per view for popular courses
  const visiblePopularCourses = useMemo(() => {
    if (popularCoursesPool.length <= 3) return popularCoursesPool;
    const start = (popularCarouselIndex * 3) % popularCoursesPool.length;
    const slice = popularCoursesPool.slice(start, start + 3);
    if (slice.length < 3) {
      return [...slice, ...popularCoursesPool.slice(0, 3 - slice.length)];
    }
    return slice;
  }, [popularCoursesPool, popularCarouselIndex]);

  const handleNextPopular = () => {
    if (popularCoursesPool.length <= 3) return;
    setPopularCarouselIndex((prev) => prev + 1);
  };

  const handlePrevPopular = () => {
    if (popularCoursesPool.length <= 3) return;
    setPopularCarouselIndex((prev) => (prev > 0 ? prev - 1 : Math.ceil(popularCoursesPool.length / 3) - 1));
  };

  const handleJoinNow = () => {
    coursesSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
    if (courses.length > 0) {
      setSelectedCourse(courses[0]);
    }
  };

  return (
    <div className="min-h-screen bg-[#ECEAF6] p-2.5 sm:p-5 lg:p-7 relative overflow-x-hidden flex justify-center items-start font-sans">
      {/* Decorative Organic Curved Gradients in Background */}
      <div className="absolute -top-32 -left-32 w-96 h-96 bg-purple-300/35 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 -right-32 w-[30rem] h-[30rem] bg-indigo-300/30 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 left-1/4 w-80 h-80 bg-purple-200/40 rounded-full blur-3xl pointer-events-none" />

      {/* Main Centered Rounded Dashboard Surface */}
      <div className="max-w-[1400px] w-full bg-[#FAFAFE] rounded-[36px] shadow-[0_20px_60px_-15px_rgba(79,70,229,0.07)] border border-white/80 p-3.5 sm:p-6 lg:p-7 flex flex-col md:flex-row gap-5 lg:gap-6 relative z-10">
        {/* Left Floating Sidebar */}
        <Sidebar activeTab="home" onNavigate={() => {}} />

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col space-y-6 overflow-hidden min-w-0">
          {/* Top Search & Profile Area */}
          <TopHeader
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            onSearchSubmit={handleSearchSubmit}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
            selectedDifficulty={selectedDifficulty}
            onSelectDifficulty={setSelectedDifficulty}
          />

          {/* Two-Column Dashboard Content */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left / Main Column (8 cols ~ 67%) */}
            <div className="lg:col-span-8 flex flex-col space-y-6 min-w-0">
              {/* Purple Hero Banner */}
              <HeroBanner onJoinNowClick={handleJoinNow} />

              {/* My Courses Section */}
              <div ref={coursesSectionRef} className="flex flex-col space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <h2 className="text-base sm:text-lg font-extrabold text-slate-900 tracking-tight">
                      My Courses
                    </h2>
                    <span className="text-[11px] font-semibold text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full font-mono border border-purple-100">
                      Explore Track
                    </span>
                  </div>
                  <span className="text-xs text-slate-400 font-medium">
                    {courses.length} courses available
                  </span>
                </div>

                {loading ? (
                  <div className="py-12 bg-white rounded-2xl border border-slate-100 flex flex-col items-center justify-center space-y-2">
                    <Loader2 className="w-6 h-6 text-purple-600 animate-spin" />
                    <span className="text-xs text-slate-400">Loading courses...</span>
                  </div>
                ) : myCourses.length === 0 ? (
                  <div className="p-8 bg-white rounded-2xl border border-slate-100 text-center">
                    <BookOpen className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <p className="text-xs text-slate-500 font-medium">No courses matched your search or filters.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {myCourses.map((c) => (
                      <CourseCard key={c.id} course={c} onSelect={setSelectedCourse} />
                    ))}
                  </div>
                )}
              </div>

              {/* Popular Courses Section */}
              <div className="flex flex-col space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h2 className="text-base sm:text-lg font-extrabold text-slate-900 tracking-tight">
                    Popular Courses
                  </h2>

                  {/* Carousel Controls */}
                  {popularCoursesPool.length > 3 && (
                    <div className="flex items-center space-x-1.5">
                      <button
                        onClick={handlePrevPopular}
                        title="Previous Popular Courses"
                        className="w-7 h-7 rounded-full bg-white hover:bg-slate-100 border border-slate-200/80 shadow-sm flex items-center justify-center text-slate-600 transition-colors"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </button>
                      <button
                        onClick={handleNextPopular}
                        title="Next Popular Courses"
                        className="w-7 h-7 rounded-full bg-white hover:bg-slate-100 border border-slate-200/80 shadow-sm flex items-center justify-center text-slate-600 transition-colors"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>

                {loading ? (
                  <div className="py-8 bg-white rounded-2xl border border-slate-100 flex justify-center">
                    <Loader2 className="w-6 h-6 text-purple-600 animate-spin" />
                  </div>
                ) : visiblePopularCourses.length === 0 ? (
                  <div className="p-6 bg-white rounded-2xl border border-slate-100 text-center text-xs text-slate-500">
                    All available courses are displayed above in Explore Track.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {visiblePopularCourses.map((c) => (
                      <CourseCard key={c.id} course={c} onSelect={setSelectedCourse} compact />
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Right Column (4 cols ~ 33%) */}
            <div className="lg:col-span-4 flex flex-col space-y-5 min-w-0">
              {/* Learning Statistics (2x2 Grid) */}
              <StatsGrid />

              {/* Learning Hours / Statistics Chart */}
              <LearningChart />

              {/* Promotional Go Premium Card */}
              <PromoCard />
            </div>
          </div>
        </main>
      </div>

      {/* Course Detail Modal */}
      {selectedCourse && (
        <CourseDetailModal
          course={selectedCourse}
          onClose={() => setSelectedCourse(null)}
          appClient={appClient}
        />
      )}
    </div>
  );
};
