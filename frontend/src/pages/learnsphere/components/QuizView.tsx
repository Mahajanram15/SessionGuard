import React, { useState } from 'react';
import { CheckCircle2, XCircle, HelpCircle, RotateCcw, ArrowRight, Award, AlertCircle } from 'lucide-react';
import { QuizQuestion, QuizAttempt } from '../../../types';

interface QuizViewProps {
  questions?: QuizQuestion[] | null;
  lessonId: string;
  onQuizComplete: (attempt: QuizAttempt) => void;
  previousAttempt?: QuizAttempt;
}

export const QuizView: React.FC<QuizViewProps> = ({
  questions,
  lessonId,
  onQuizComplete,
  previousAttempt,
}) => {
  const [currentIdx, setCurrentIdx] = useState<number>(0);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);
  const [answers, setAnswers] = useState<Record<number, { selectedId: string; isCorrect: boolean }>>({});
  const [isFinished, setIsFinished] = useState<boolean>(false);

  // If no quiz questions are associated with this lesson
  if (!questions || questions.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm text-center">
        <div className="w-12 h-12 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center mx-auto mb-3">
          <HelpCircle className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-bold text-slate-800">No Knowledge Check for this Module</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
          This lesson focuses on conceptual architecture and foundational principles. Review the summary and mark the lesson as completed to proceed.
        </p>
      </div>
    );
  }

  const currentQuestion = questions[currentIdx];
  const totalQuestions = questions.length;

  const handleSelectOption = (optionId: string) => {
    if (isSubmitted) return;
    setSelectedOptionId(optionId);
  };

  const handleSubmitAnswer = () => {
    if (!selectedOptionId || isSubmitted) return;

    const isCorrect = selectedOptionId === currentQuestion.correct_option_id;
    setAnswers((prev) => ({
      ...prev,
      [currentIdx]: { selectedId: selectedOptionId, isCorrect },
    }));
    setIsSubmitted(true);
  };

  const handleNextQuestion = () => {
    if (currentIdx + 1 < totalQuestions) {
      setCurrentIdx((prev) => prev + 1);
      setSelectedOptionId(null);
      setIsSubmitted(false);
    } else {
      // Calculate final score
      const correctCount = Object.values(answers).filter((a) => a.isCorrect).length;
      const finalScore = Math.round((correctCount / totalQuestions) * 100);
      const passed = finalScore >= 70;

      const attempt: QuizAttempt = {
        lessonId,
        score: finalScore,
        totalQuestions,
        passed,
        completedAt: new Date().toISOString(),
      };

      setIsFinished(true);
      onQuizComplete(attempt);
    }
  };

  const handleRetry = () => {
    setCurrentIdx(0);
    setSelectedOptionId(null);
    setIsSubmitted(false);
    setAnswers({});
    setIsFinished(false);
  };

  // Render Quiz Summary when finished
  if (isFinished) {
    const correctCount = Object.values(answers).filter((a) => a.isCorrect).length;
    const scorePercent = Math.round((correctCount / totalQuestions) * 100);
    const isPassing = scorePercent >= 70;

    return (
      <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-md shadow-purple-900/5 text-center flex flex-col items-center">
        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-3.5 shadow-sm ${
          isPassing ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
        }`}>
          <Award className="w-7 h-7" />
        </div>

        <h3 className="text-base font-extrabold text-slate-900">
          {isPassing ? 'Knowledge Check Passed!' : 'Review Recommended'}
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          You scored <strong className="text-purple-700 font-mono text-sm">{scorePercent}%</strong> ({correctCount} of {totalQuestions} correct)
        </p>

        <span className={`mt-3 px-3 py-1 rounded-full text-xs font-bold font-mono ${
          isPassing ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
        }`}>
          {isPassing ? 'STATUS: MASTERY CONFIRMED' : 'STATUS: REVIEW CONCEPTS'}
        </span>

        <p className="text-[11px] text-slate-400 mt-3 font-mono">
          Session-local evaluation &bull; Zero external answer transmission
        </p>

        <div className="mt-5 flex items-center space-x-3">
          <button
            onClick={handleRetry}
            className="px-4 py-2 rounded-xl text-xs font-bold border border-slate-200 text-slate-700 hover:bg-slate-50 transition-all inline-flex items-center space-x-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Retake Quiz</span>
          </button>
        </div>
      </div>
    );
  }

  const currentAnswer = answers[currentIdx];

  return (
    <div className="bg-white rounded-2xl p-5 sm:p-6 border border-slate-100 shadow-sm flex flex-col space-y-4">
      {/* Quiz Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-purple-600 animate-pulse" />
          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Knowledge Check
          </h4>
        </div>

        <div className="flex items-center space-x-3">
          {previousAttempt && (
            <span className="text-[11px] font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
              Best Score: {previousAttempt.score}%
            </span>
          )}
          <span className="text-xs font-bold text-purple-700 font-mono bg-purple-50 px-2.5 py-1 rounded-full border border-purple-100">
            Question {currentIdx + 1} of {totalQuestions}
          </span>
        </div>
      </div>

      {/* Question Prompt */}
      <div>
        <h3 className="text-sm sm:text-base font-bold text-slate-900 leading-snug">
          {currentQuestion.question}
        </h3>
      </div>

      {/* Answer Options */}
      <div className="space-y-2.5 pt-1">
        {currentQuestion.options.map((opt) => {
          const isSelected = selectedOptionId === opt.id;
          const isCorrectOption = opt.id === currentQuestion.correct_option_id;

          let optionStyle = 'bg-slate-50 border-slate-200/80 text-slate-700 hover:bg-purple-50/50 hover:border-purple-200';

          if (isSubmitted) {
            if (isCorrectOption) {
              optionStyle = 'bg-emerald-50 border-emerald-400 text-emerald-900 shadow-sm';
            } else if (isSelected && !isCorrectOption) {
              optionStyle = 'bg-rose-50 border-rose-400 text-rose-900 shadow-sm';
            } else {
              optionStyle = 'bg-slate-50/60 border-slate-200 text-slate-400 opacity-60';
            }
          } else if (isSelected) {
            optionStyle = 'bg-purple-50 border-purple-600 text-purple-900 shadow-sm';
          }

          return (
            <button
              key={opt.id}
              onClick={() => handleSelectOption(opt.id)}
              disabled={isSubmitted}
              className={`w-full text-left p-3.5 rounded-xl border text-xs sm:text-sm font-medium transition-all flex items-center justify-between ${optionStyle} ${
                isSubmitted ? 'cursor-default' : 'cursor-pointer'
              }`}
            >
              <div className="flex items-center space-x-3 pr-2">
                <span className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-mono font-bold shrink-0 ${
                  isSelected || (isSubmitted && isCorrectOption)
                    ? 'bg-purple-600 text-white'
                    : 'bg-white text-slate-500 border border-slate-200'
                }`}>
                  {opt.id.replace('opt_', '').toUpperCase()}
                </span>
                <span>{opt.text}</span>
              </div>

              {isSubmitted && (
                <div className="shrink-0">
                  {isCorrectOption ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  ) : isSelected ? (
                    <XCircle className="w-5 h-5 text-rose-600" />
                  ) : null}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Explanation Feedback Card after submission */}
      {isSubmitted && (
        <div className={`p-4 rounded-xl border text-xs leading-relaxed animate-in fade-in duration-200 ${
          currentAnswer?.isCorrect
            ? 'bg-emerald-50/80 border-emerald-200 text-emerald-900'
            : 'bg-amber-50/80 border-amber-200 text-amber-900'
        }`}>
          <div className="flex items-center space-x-1.5 font-bold mb-1">
            {currentAnswer?.isCorrect ? (
              <span className="flex items-center space-x-1 text-emerald-700">
                <CheckCircle2 className="w-4 h-4" />
                <span>Correct!</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1 text-amber-700">
                <AlertCircle className="w-4 h-4" />
                <span>Explanation:</span>
              </span>
            )}
          </div>
          <p>{currentQuestion.explanation}</p>
        </div>
      )}

      {/* Action Footer */}
      <div className="pt-2 flex items-center justify-between border-t border-slate-100">
        <span className="text-[11px] text-slate-400 font-mono">
          {isSubmitted ? 'Feedback evaluated' : 'Select an answer to submit'}
        </span>

        {!isSubmitted ? (
          <button
            onClick={handleSubmitAnswer}
            disabled={!selectedOptionId}
            className={`px-5 py-2.5 rounded-full text-xs font-bold transition-all shadow-sm ${
              selectedOptionId
                ? 'bg-[#6941C6] hover:bg-[#53389E] text-white shadow-purple-600/20 cursor-pointer'
                : 'bg-slate-100 text-slate-400 cursor-not-allowed'
            }`}
          >
            Check Answer
          </button>
        ) : (
          <button
            onClick={handleNextQuestion}
            className="px-5 py-2.5 rounded-full text-xs font-bold bg-[#6941C6] hover:bg-[#53389E] text-white shadow-md shadow-purple-600/20 hover:shadow-lg transition-all inline-flex items-center space-x-1.5 cursor-pointer"
          >
            <span>{currentIdx + 1 < totalQuestions ? 'Next Question' : 'View Summary'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};
