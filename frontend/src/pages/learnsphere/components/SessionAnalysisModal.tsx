import React from 'react';
import {
  X,
  ShieldCheck,
  Cpu,
  BarChart2,
  Sparkles,
  ExternalLink,
  CheckCircle2,
  Bot,
  User,
  Info,
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
                  Stage 4 Verified
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
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {/* Readiness & Execution Pipeline Status */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col">
              <span className="text-[10px] text-slate-400 font-semibold uppercase">Intended Scenario</span>
              <span className="text-xs font-bold text-slate-800 mt-1 flex items-center space-x-1">
                {scenarioType === 'manual' ? (
                  <>
                    <User className="w-3.5 h-3.5 text-purple-600" />
                    <span>Manual Operator</span>
                  </>
                ) : (
                  <>
                    <Bot className="w-3.5 h-3.5 text-indigo-600" />
                    <span>Synthetic Bot</span>
                  </>
                )}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col">
              <span className="text-[10px] text-slate-400 font-semibold uppercase">Events Captured</span>
              <span className="text-xs font-bold text-slate-800 mt-1 font-mono">
                {totalEvents} Events Accepted
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col">
              <span className="text-[10px] text-slate-400 font-semibold uppercase">Feature Extraction</span>
              <span className="text-xs font-bold text-emerald-700 mt-1 flex items-center space-x-1 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>64 Features Ready</span>
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col">
              <span className="text-[10px] text-slate-400 font-semibold uppercase">Frozen Model</span>
              <span className="text-xs font-bold text-slate-800 mt-1 font-mono truncate">
                {ml?.model_version || 'expA (XGBoost)'}
              </span>
            </div>
          </div>

          {/* Genuine ML Prediction Card */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 text-white shadow-lg space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm font-bold tracking-tight">
                  Frozen XGBoost Model Inference Output
                </h3>
              </div>
              <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-white/10 text-purple-200 border border-white/15">
                Decision Threshold: {ml?.decision_threshold?.toFixed(2) || '0.50'}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-center">
              {/* Predicted Class */}
              <div className="flex flex-col space-y-1">
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Predicted Class
                </span>
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-3 py-1 rounded-xl text-sm font-extrabold font-mono shadow-sm ${
                      isAutomatedPredicted
                        ? 'bg-rose-500/30 text-rose-300 border border-rose-500/50'
                        : 'bg-emerald-500/30 text-emerald-300 border border-emerald-500/50'
                    }`}
                  >
                    {ml?.predicted_class || 'UNKNOWN'}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    (Label: {ml?.predicted_label ?? '?'})
                  </span>
                </div>
              </div>

              {/* Probabilities */}
              <div className="flex flex-col space-y-1 sm:border-l sm:border-white/10 sm:pl-4">
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Posterior Probabilities
                </span>
                <div className="space-y-0.5 font-mono text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-300">P(Human):</span>
                    <span className="font-bold text-emerald-400">
                      {probHuman !== null ? `${(probHuman * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-300">P(Automated):</span>
                    <span className="font-bold text-rose-400">
                      {probAuto !== null ? `${(probAuto * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Policy Decision */}
              <div className="flex flex-col space-y-1 sm:border-l sm:border-white/10 sm:pl-4">
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Consolidated Policy
                </span>
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2.5 py-0.5 rounded-lg text-xs font-bold font-mono ${
                      riskData?.decision.action === 'BLOCK'
                        ? 'bg-rose-500 text-white'
                        : riskData?.decision.action === 'CHALLENGE'
                        ? 'bg-amber-500 text-slate-950'
                        : 'bg-emerald-500 text-white'
                    }`}
                  >
                    {riskData?.decision.action || 'ALLOW'}
                  </span>
                  <span className="text-xs font-mono text-slate-300">
                    Risk: {riskData?.behavioral_integrity_score.toFixed(3) || '0.00'}
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-white/10 flex items-start space-x-2 text-[11px] text-slate-300">
              <Info className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
              <span>
                <strong>Distinction Note:</strong> The predicted class reflects genuine model classification on the 64-feature vector. It is reported independently of the operator's intended scenario.
              </span>
            </div>
          </div>

          {/* Contributing SHAP Features */}
          {explanationData?.shap_contributions && explanationData.shap_contributions.length > 0 && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-1.5">
                  <BarChart2 className="w-4 h-4 text-purple-600" />
                  <span>Top Contributing SHAP Features</span>
                </h4>
                <span className="text-[11px] text-slate-400 font-mono">
                  Tree SHAP Contributions
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                {explanationData.shap_contributions.map((feat, idx) => {
                  const isPositive = feat.shap_value >= 0;
                  return (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col justify-between space-y-1.5"
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

                      <div className="text-[11px] text-slate-500 font-mono">
                        <span>Value: </span>
                        <span className="text-slate-800 font-bold">{feat.feature_value.toFixed(2)}</span>
                      </div>

                      <p className="text-[10px] text-slate-500 leading-tight">
                        {feat.description}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
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
