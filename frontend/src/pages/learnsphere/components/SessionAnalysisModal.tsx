import React from 'react';
import {
  X,
  ShieldCheck,
  Cpu,
  BarChart2,
  ExternalLink,
  CheckCircle2,
  Bot,
  User,
  AlertTriangle,
  HelpCircle,
} from 'lucide-react';
import { RiskResponse, ExplanationResponse } from '../../../types';

interface SessionAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  scenarioType: 'manual' | 'synthetic_automation';
  sessionId: string;
  totalEvents: number;
  riskData: RiskResponse | null;
  explanationData: ExplanationResponse | null;
  onNavigateToMatrix?: () => void;
}

export const SessionAnalysisModal: React.FC<SessionAnalysisModalProps> = ({
  isOpen,
  onClose,
  scenarioType,
  sessionId,
  totalEvents,
  riskData,
  explanationData,
  onNavigateToMatrix,
}) => {
  if (!isOpen) return null;

  const ml = riskData?.ml_inference;
  const isAutomatedPredicted = ml?.predicted_class === 'AUTOMATED';
  const probAuto = ml?.probability_automated !== undefined ? ml.probability_automated : null;
  const probHuman = ml?.probability_human !== undefined ? ml.probability_human : null;
  const isExpB = ml?.active_model === 'experiment_b';

  // Genuine non-zero SHAP contributors only (Task 3)
  const nonzeroContributions =
    explanationData?.shap_contributions?.filter(
      (feat) => Math.abs(feat.shap_value) >= 0.0001
    ) || [];

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-150">
      <div className="bg-white rounded-[28px] max-w-3xl w-full border border-slate-100 shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="p-6 bg-gradient-to-r from-purple-50 via-slate-50 to-indigo-50 border-b border-slate-100 flex items-start justify-between">
          <div className="flex items-center space-x-3.5">
            <div className="w-12 h-12 rounded-2xl bg-purple-600 text-white flex items-center justify-center shadow-md shadow-purple-600/20 shrink-0">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2 mb-1">
                <span className="px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 text-xs font-bold font-mono">
                  Stage 6 Demo Integrity
                </span>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-xs text-slate-600 font-mono font-medium truncate max-w-[200px] sm:max-w-xs">
                  {sessionId}
                </span>
              </div>
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 leading-tight">
                Session Telemetry &amp; ML Inference Verification
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white hover:bg-slate-100 text-slate-400 hover:text-slate-600 flex items-center justify-center border border-slate-200 transition-colors shrink-0 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-5">
          {/* STAGE 6 TASK 2: Clear Model Limitation Notice */}
          {isExpB ? (
            <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-950 space-y-2">
              <div className="flex items-center space-x-2 text-indigo-800 font-bold text-xs uppercase tracking-wider">
                <AlertTriangle className="w-4 h-4 text-indigo-600 shrink-0" />
                <span>Experiment B (Kinematic Classifier) Demonstration Notice</span>
              </div>
              <p className="text-xs leading-relaxed text-indigo-950">
                This candidate model evaluates <strong className="font-mono font-bold">12 scale-free kinematic features</strong> (trajectory straightness, velocity dispersion, angular deviation, acceleration moments) and completely excludes event counts and session duration shortcuts.
              </p>
              <p className="text-[11px] leading-relaxed text-indigo-800/90">
                <strong>Model Limitation:</strong> Reported scores are uncalibrated decision risk scores, not verified statistical probabilities. Candidate Experiment B has only been validated against the current synthetic bot profiles and requires broader human baseline studies before operational deployment.
              </p>
            </div>
          ) : (
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-900 space-y-2">
              <div className="flex items-center space-x-2 text-amber-800 font-bold text-xs uppercase tracking-wider">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>Model Limitation &amp; Demonstration Notice</span>
              </div>
              <p className="text-xs leading-relaxed text-amber-900">
                This frozen Experiment A demonstration model relies overwhelmingly on{' '}
                <strong className="font-mono font-bold">mouse_event_count</strong> (all 35 decision tree splits trigger at &lt; 72 samples). Short demonstration sessions are classified as automated regardless of other behavioral differences (such as natural velocity variance or typing cadence).
              </p>
              <p className="text-[11px] leading-relaxed text-amber-800/90">
                The reported score is an uncalibrated raw model output, not a verified probability that a person is a bot. The model is a pilot artifact and is not production-ready for operational security enforcement without broader, independently validated data.
              </p>
            </div>
          )}

          {/* STAGE 6 TASK 4: Separate Intended Scenario from Model Prediction */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {/* Operator Scenario Context Card */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col justify-between space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                  1. Demo Execution Scenario
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-200/70 text-slate-700 font-semibold">
                  Test Parameter
                </span>
              </div>
              <div className="flex items-center space-x-2">
                {scenarioType === 'manual' ? (
                  <>
                    <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
                      <User className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900">Manual Operator</div>
                      <div className="text-[11px] text-slate-500">Interactive LearnSphere browsing &amp; quizzes</div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="w-8 h-8 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900">Synthetic Bot Automation</div>
                      <div className="text-[11px] text-slate-500">Deterministic linear trajectory script</div>
                    </div>
                  </>
                )}
              </div>
              <p className="text-[10px] text-slate-500 pt-1 border-t border-slate-200/60 leading-tight">
                <strong>Scenario Context:</strong> Describes how the operator ran this local test session. It is not the model&apos;s conclusion and is not passed to the inference engine.
              </p>
            </div>

            {/* Model Prediction Output Card */}
            <div className="p-4 rounded-2xl bg-slate-900 text-white flex flex-col justify-between space-y-2 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                  {isExpB ? '2. Candidate Exp B (Kinematic) Output' : '2. Frozen Exp A (Count Baseline) Output'}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-slate-300 font-mono">
                  Threshold: {ml?.decision_threshold?.toFixed(2) || '0.50'}
                </span>
              </div>
              <div className="flex items-center space-x-2.5">
                <span
                  className={`px-3 py-1 rounded-xl text-sm font-extrabold font-mono shadow-sm ${
                    isAutomatedPredicted
                      ? 'bg-rose-500/30 text-rose-300 border border-rose-500/50'
                      : 'bg-emerald-500/30 text-emerald-300 border border-emerald-500/50'
                  }`}
                >
                  {ml?.predicted_class || 'UNKNOWN'}
                </span>
                <div className="text-xs font-mono text-slate-300">
                  <span>{isExpB ? 'Kinematic Risk (Auto): ' : 'Uncalibrated Score (Auto): '}</span>
                  <span className="font-bold text-rose-400">
                    {probAuto !== null ? `${(probAuto * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                  <span className="mx-1.5 text-slate-500">|</span>
                  <span>{isExpB ? 'Kinematic Risk (Human): ' : 'Uncalibrated Score (Human): '}</span>
                  <span className="font-bold text-emerald-400">
                    {probHuman !== null ? `${(probHuman * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
              </div>
              <p className="text-[10px] text-slate-400 pt-1 border-t border-white/10 leading-tight">
                <strong>Independent Output:</strong> Computed strictly on the {isExpB ? '12 kinematic features' : '64-feature vector'}. It is not inferred from or linked to test scenario metadata.
              </p>
            </div>
          </div>

          {/* Telemetry & Pipeline Readiness Metrics */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col">
              <span className="text-[10px] text-slate-400 font-semibold uppercase">Events Accepted</span>
              <span className="text-xs font-bold text-slate-800 mt-1 font-mono">
                {totalEvents} Telemetry Events
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col">
              <span className="text-[10px] text-slate-400 font-semibold uppercase">Feature Extraction</span>
              {ml?.status === 'available' ? (
                <span className="text-xs font-bold text-emerald-700 mt-1 flex items-center space-x-1 font-mono">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>{isExpB ? '12 Kinematic Features Ready' : '64 Features Ready'}</span>
                </span>
              ) : ml?.status === 'prediction_not_ready' ? (
                <span className="text-xs font-bold text-amber-700 mt-1 flex items-center space-x-1 font-mono">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  <span>Finalization Pending</span>
                </span>
              ) : ml?.status === 'insufficient_telemetry' ? (
                <span className="text-xs font-bold text-rose-700 mt-1 flex items-center space-x-1 font-mono">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                  <span>Insufficient Events</span>
                </span>
              ) : (
                <span className="text-xs font-bold text-slate-500 mt-1 flex items-center space-x-1 font-mono">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
                  <span>Features Unavailable</span>
                </span>
              )}
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col">
              <span className="text-[10px] text-slate-400 font-semibold uppercase">Model Version</span>
              <span className="text-xs font-bold text-slate-800 mt-1 font-mono truncate">
                {ml?.model_version || (isExpB ? '1.0.0-candidate (Exp B)' : '3.4.1 (Exp A)')}
              </span>
            </div>
          </div>

          {/* STAGE 6 TASK 5: Multi-Signal Risk Score Explanation */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-xs font-bold text-slate-800 flex items-center space-x-1.5">
                <span>Behavioral Integrity Score: </span>
                <span className="font-mono text-purple-700">
                  {riskData?.behavioral_integrity_score.toFixed(3) || '0.000'}
                </span>
              </span>
              <p className="text-[11px] text-slate-500">
                Consolidated heuristic multi-signal risk index [0.0 - 1.0]. Distinct from ML posterior probabilities.
              </p>
            </div>
            <div className="flex items-center space-x-2 shrink-0">
              <span className="text-xs font-semibold text-slate-600">Policy Action:</span>
              <span
                className={`px-2.5 py-1 rounded-lg text-xs font-bold font-mono ${
                  riskData?.decision.action === 'BLOCK'
                    ? 'bg-rose-500 text-white'
                    : riskData?.decision.action === 'CHALLENGE'
                    ? 'bg-amber-500 text-slate-950'
                    : 'bg-emerald-500 text-white'
                }`}
              >
                {riskData?.decision.action || 'ALLOW'}
              </span>
            </div>
          </div>

          {/* STAGE 6.1 TASK 2: Semantically Accurate Explanations */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-1.5">
                  <BarChart2 className="w-4 h-4 text-purple-600" />
                  <span>{isExpB ? 'Contributing Behavioral Features (Experiment B Attribution)' : 'Contributing Behavioral Features (SHAP Model Attributions)'}</span>
                </h4>
                <p className="text-[10px] text-slate-500">
                  {isExpB
                    ? 'Experiment B feature evaluations are based on scale-free kinematic trajectories. Tree SHAP is suppressed to avoid attribution leakage.'
                    : 'SHAP values represent tree-split contributions to the model\'s log-odds score, not causal proof of user identity or intent.'}
                </p>
              </div>
              {explanationData && explanationData.ml_inference?.status === 'available' && !isExpB && (
                <span className="text-[10px] text-slate-400 font-mono shrink-0">
                  Non-Zero Contributors: {nonzeroContributions.length}
                </span>
              )}
            </div>

            {isExpB ? (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 text-slate-600 text-xs flex items-center space-x-2">
                <HelpCircle className="w-4 h-4 text-purple-500 shrink-0" />
                <span>
                  Feature attribution explanations are not currently supported for Experiment B (Kinematic Classifier). Experiment A tree SHAP values are intentionally suppressed to prevent cross-model attribution leakage.
                </span>
              </div>
            ) : !explanationData || explanationData.ml_inference?.status !== 'available' ? (
              /* State 2: Explanation unavailable or failed */
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 text-slate-500 text-xs flex items-center space-x-2">
                <HelpCircle className="w-4 h-4 text-slate-400 shrink-0" />
                <span>
                  Explanation data is unavailable for this session.
                </span>
              </div>
            ) : nonzeroContributions.length > 0 ? (
              /* State 1: Non-zero attribution available */
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                {nonzeroContributions.map((feat, idx) => {
                  const isPositive = feat.shap_value >= 0;
                  return (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex flex-col justify-between space-y-1.5"
                    >
                      <div className="flex items-start justify-between gap-1">
                        <span className="text-xs font-bold font-mono text-slate-800 truncate" title={feat.feature_name}>
                          {feat.feature_name}
                        </span>
                        <span
                          className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                            isPositive
                              ? 'bg-rose-100 text-rose-700'
                              : 'bg-emerald-100 text-emerald-700'
                          }`}
                        >
                          {isPositive ? '+' : ''}{feat.shap_value.toFixed(3)}
                        </span>
                      </div>

                      <div className="text-[11px] text-slate-600 font-mono">
                        <span>Value: </span>
                        <span className="text-slate-900 font-bold">{feat.feature_value.toFixed(2)}</span>
                      </div>

                      <p className="text-[10px] text-slate-500 leading-tight">
                        {feat.description}
                      </p>
                    </div>
                  );
                })}
              </div>
            ) : (
              /* State 3: Valid explanation with all-zero feature contributions */
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 text-slate-500 text-xs flex items-center space-x-2">
                <HelpCircle className="w-4 h-4 text-slate-400 shrink-0" />
                <span>
                  No individual feature has a non-zero attribution for this prediction.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-2 text-xs text-slate-500">
            <ShieldCheck className="w-4 h-4 text-purple-600" />
            <span>Behavioral telemetry verified without transmitting student PII or quiz answers.</span>
          </div>

          <div className="flex items-center space-x-2.5">
            {onNavigateToMatrix && (
              <button
                onClick={() => {
                  onClose();
                  onNavigateToMatrix();
                }}
                className="px-4 py-2 rounded-full text-xs font-bold bg-white hover:bg-slate-100 text-purple-700 border border-purple-200 shadow-sm transition-all cursor-pointer flex items-center space-x-1.5"
              >
                <span>View in System Matrix</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            )}

            <button
              onClick={onClose}
              className="px-5 py-2 rounded-full text-xs font-bold bg-[#6941C6] hover:bg-[#53389E] text-white shadow-md shadow-purple-600/20 transition-all cursor-pointer"
            >
              Close Verification
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
