import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck,
  Activity,
  Users,
  AlertTriangle,
  CheckCircle2,
  Search,
  Cpu,
  BarChart2,
  Sparkles,
  Info,
  Loader2,
  HelpCircle,
  RefreshCw,
} from 'lucide-react';
import {
  DashboardStats,
  HealthResponse,
  RiskResponse,
  ExplanationResponse,
  ModelStatusResponse,
} from '../types';
import { apiClient } from '../services/api';

interface DashboardShellProps {
  stats: DashboardStats | null;
  health: HealthResponse | null;
  loading: boolean;
  currentSessionId?: string | null;
}

export const DashboardShell: React.FC<DashboardShellProps> = ({
  stats,
  health,
  loading: _loading,
  currentSessionId,
}) => {
  const [inspectSessionId, setInspectSessionId] = useState<string>(currentSessionId || '');
  const [inspectLoading, setInspectLoading] = useState<boolean>(false);
  const [inspectError, setInspectError] = useState<string | null>(null);
  const [riskData, setRiskData] = useState<RiskResponse | null>(null);
  const [explanationData, setExplanationData] = useState<ExplanationResponse | null>(null);

  // Globally active model status armed for upcoming inferences
  const [modelStatus, setModelStatus] = useState<ModelStatusResponse | null>(null);
  const [modelStatusLoading, setModelStatusLoading] = useState<boolean>(false);
  const [modelStatusError, setModelStatusError] = useState<string | null>(null);

  const fetchModelStatus = useCallback(async () => {
    setModelStatusLoading(true);
    setModelStatusError(null);
    try {
      const data = await apiClient.getModelStatus();
      setModelStatus(data);
    } catch (err: any) {
      console.error('Failed to load active model status:', err);
      setModelStatusError(err?.message || 'Failed to retrieve active model status');
    } finally {
      setModelStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModelStatus();
  }, [fetchModelStatus, stats]);

  // If a currentSessionId is provided and none is selected yet, prefill it
  useEffect(() => {
    if (currentSessionId && !inspectSessionId) {
      setInspectSessionId(currentSessionId);
    }
  }, [currentSessionId]);

  const handleInspectSession = async (targetId?: string) => {
    const sId = (targetId || inspectSessionId).trim();
    if (!sId) {
      setInspectError('Please enter or select a valid session ID to inspect.');
      return;
    }

    setInspectLoading(true);
    setInspectError(null);

    try {
      const [riskRes, explRes] = await Promise.all([
        apiClient.getRiskScore(sId),
        apiClient.getExplanation(sId),
      ]);
      setRiskData(riskRes);
      setExplanationData(explRes);
    } catch (err: any) {
      console.error('Session inspection failed:', err);
      setInspectError(err?.message || 'Failed to retrieve session risk and ML explanation.');
      setRiskData(null);
      setExplanationData(null);
    } finally {
      setInspectLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner: Research Foundation Overview */}
      <div className="glass-panel p-6 rounded-xl relative overflow-hidden">
        <div className="absolute -right-10 -top-10 w-48 h-48 bg-primary-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-xs font-mono mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-primary-400 animate-pulse" />
            <span>Research USP: Cross-Layer Behavioral Integrity</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">
            System Matrix &amp; Behavioral Inference Dashboard
          </h1>
          <p className="text-slate-300 text-sm leading-relaxed">
            Evaluates cross-layer consistency between browser motor dynamics and backend API telemetry with multi-signal heuristics and behavioral machine learning inference.
          </p>
        </div>
      </div>

      {/* Active Inference Engine Indicator (Armed for Future Sessions) */}
      <div className="p-4 rounded-xl glass-panel border border-border/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start sm:items-center space-x-3.5">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border ${
            modelStatus?.active_model === 'experiment_b'
              ? 'bg-purple-500/10 text-purple-400 border-purple-500/20'
              : 'bg-primary-500/10 text-primary-400 border-primary-500/20'
          }`}>
            <Cpu className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Armed Inference Engine:
              </span>
              {modelStatusLoading ? (
                <span className="inline-flex items-center space-x-1.5 text-xs text-slate-400 font-mono">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-primary-400" />
                  <span>Checking engine status...</span>
                </span>
              ) : modelStatusError ? (
                <span className="inline-flex items-center space-x-1 text-xs text-rose-400 font-mono">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>{modelStatusError}</span>
                </span>
              ) : (
                <>
                  <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                    modelStatus?.active_model === 'experiment_b'
                      ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                      : 'bg-primary-500/20 text-primary-300 border border-primary-500/40'
                  }`}>
                    {modelStatus?.active_model === 'experiment_b'
                      ? 'Experiment B (Kinematic Candidate)'
                      : 'Experiment A (Frozen XGBoost Baseline)'}
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface border border-border/60 text-slate-300">
                    v{modelStatus?.model_version || 'N/A'}
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface border border-border/60 text-slate-300">
                    {modelStatus?.feature_count ?? (modelStatus?.active_model === 'experiment_b' ? 12 : 64)} Features
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface border border-border/60 text-slate-400">
                    Score Label: <strong className="text-slate-200">{modelStatus?.score_label || 'Uncalibrated Model Score'}</strong>
                  </span>
                </>
              )}
            </div>
            <p className="text-[11px] text-slate-400 leading-tight">
              <strong>Future Sessions Scope:</strong> This model is armed for upcoming evaluations. Inspected historical sessions below remain immutable and display the model that analyzed them.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0 self-end md:self-center">
          <button
            onClick={() => fetchModelStatus()}
            disabled={modelStatusLoading}
            className="px-2.5 py-1.5 rounded-lg bg-surface-elevated/70 hover:bg-surface-elevated border border-border/70 hover:border-border text-slate-300 hover:text-white text-xs font-mono flex items-center space-x-1.5 transition-colors disabled:opacity-50 cursor-pointer"
            title="Refresh active model status from backend"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${modelStatusLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Engine</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Sessions */}
        <div className="glass-panel p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Tracked</span>
            <Users className="w-4 h-4 text-slate-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono text-white">
              {stats?.total_sessions ?? 0}
            </span>
            <span className="text-xs text-cyber-emerald flex items-center font-mono">
              Active: {stats?.active_sessions ?? 0}
            </span>
          </div>
        </div>

        {/* Avg Risk Score */}
        <div className="glass-panel p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Fleet Risk Score</span>
            <Activity className="w-4 h-4 text-cyber-cyan" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono text-cyber-cyan">
              {stats?.average_risk_score !== undefined ? stats.average_risk_score.toFixed(2) : '0.00'}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Range: [0.0 - 1.0]
            </span>
          </div>
        </div>

        {/* Allow Decisions */}
        <div className="glass-panel p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Allow Rate</span>
            <CheckCircle2 className="w-4 h-4 text-cyber-emerald" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono text-cyber-emerald">
              {stats?.decision_distribution?.ALLOW ?? 0}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Risk &lt; 0.35
            </span>
          </div>
        </div>

        {/* Challenge / Rate Limit */}
        <div className="glass-panel p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Flagged / Blocked</span>
            <AlertTriangle className="w-4 h-4 text-cyber-amber" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono text-cyber-amber">
              {(stats?.decision_distribution?.CHALLENGE ?? 0) + (stats?.decision_distribution?.BLOCK ?? 0)}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Risk &ge; 0.35
            </span>
          </div>
        </div>
      </div>

      {/* STAGE 4: Dedicated Session Telemetry & ML Inference Inspector */}
      <div className="glass-panel p-6 rounded-xl border border-primary-500/30 bg-surface/90 shadow-xl space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-border/80">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-primary-500/10 border border-primary-500/30 text-primary-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
                <span>Session Behavioral Telemetry &amp; ML Inspector</span>
                <span className="text-[10px] font-mono uppercase bg-primary-500/20 text-primary-300 border border-primary-500/30 px-2 py-0.5 rounded-full">
                  Stage 4 Verified
                </span>
              </h2>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Inspect real-time behavioral telemetry, machine learning model inference, and feature attributions.
              </p>
            </div>
          </div>

          {/* Session Input & Action */}
          <div className="flex items-center space-x-2 w-full md:w-auto">
            <div className="relative flex-1 md:w-72">
              <input
                type="text"
                placeholder="Enter Session ID (sess_...)"
                value={inspectSessionId}
                onChange={(e) => setInspectSessionId(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleInspectSession()}
                className="w-full bg-surface-elevated/70 border border-border/80 rounded-lg px-3.5 py-1.5 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <button
              onClick={() => handleInspectSession()}
              disabled={inspectLoading || !inspectSessionId.trim()}
              className="px-4 py-1.5 rounded-lg bg-primary-600 hover:bg-primary-500 disabled:opacity-40 text-white text-xs font-semibold shadow-md transition-all flex items-center space-x-1.5 shrink-0 cursor-pointer"
            >
              {inspectLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Inspecting...</span>
                </>
              ) : (
                <>
                  <Search className="w-3.5 h-3.5" />
                  <span>Inspect</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Recent Sessions Quick Selector */}
        {stats?.recent_flagged_sessions && stats.recent_flagged_sessions.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-xs font-mono text-slate-400">Recent Sessions:</span>
            {stats.recent_flagged_sessions.slice(0, 6).map((item) => (
              <button
                key={item.session_id}
                onClick={() => {
                  setInspectSessionId(item.session_id);
                  handleInspectSession(item.session_id);
                }}
                title={item.session_id}
                className={`text-[11px] font-mono px-2.5 py-1 rounded-md border transition-all cursor-pointer flex items-center space-x-1.5 ${
                  inspectSessionId === item.session_id
                    ? 'bg-primary-500/20 border-primary-500/50 text-primary-200'
                    : 'bg-surface-elevated/60 border-border/60 text-slate-300 hover:border-primary-500/40'
                }`}
              >
                <span className="break-all">{item.session_id}</span>
                <span
                  className={`text-[9px] px-1 py-0.2 rounded font-bold shrink-0 ${
                    item.decision === 'BLOCK'
                      ? 'bg-rose-500/20 text-rose-300'
                      : item.decision === 'CHALLENGE'
                      ? 'bg-amber-500/20 text-amber-300'
                      : 'bg-emerald-500/20 text-emerald-300'
                  }`}
                >
                  {item.decision} ({item.risk_score.toFixed(2)})
                </span>
              </button>
            ))}
          </div>
        )}

        {/* Inspection Error */}
        {inspectError && (
          <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-xs flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{inspectError}</span>
          </div>
        )}

        {/* Inspection Results Display */}
        {riskData && (() => {
          const isSessionExpB = riskData.ml_inference?.active_model === 'experiment_b';
          const nonzeroContribs =
            explanationData?.shap_contributions?.filter(
              (feat) => Math.abs(feat.shap_value) >= 0.0001
            ) || [];

          return (
            <div className="space-y-4 pt-2">
              {/* STAGE 6 TASK 2: Model Limitation Notice */}
              {isSessionExpB ? (
                <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-200 text-xs space-y-1.5">
                  <div className="flex items-center space-x-2 text-purple-300 font-bold">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-purple-400" />
                    <span className="uppercase tracking-wider">Experiment B (Kinematic Classifier) Demonstration Notice</span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-purple-100/90">
                    This candidate model evaluates <strong className="font-mono text-white">12 scale-free kinematic features</strong> (trajectory straightness, velocity dispersion, angular deviation, acceleration moments) and completely excludes event counts and session duration shortcuts.
                  </p>
                  <p className="text-[11px] leading-relaxed text-purple-100/80">
                    <strong>Model Limitation:</strong> Reported scores are uncalibrated kinematic risk scores, not verified statistical probabilities. Candidate Experiment B has only been validated against current synthetic bot profiles and requires broader human baseline studies before operational deployment.
                  </p>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs space-y-1.5">
                  <div className="flex items-center space-x-2 text-amber-300 font-bold">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                    <span className="uppercase tracking-wider">Model Limitation &amp; Demonstration Notice</span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-amber-100/90">
                    This frozen Experiment A demonstration model relies overwhelmingly on <strong className="font-mono text-white">mouse_event_count</strong> (all 35 decision tree splits trigger at &lt; 72 samples). Short demonstration sessions are classified as automated regardless of other behavioral differences (such as natural velocity variance or typing cadence).
                  </p>
                  <p className="text-[11px] leading-relaxed text-amber-100/80">
                    The reported score is an uncalibrated raw model output, not a verified probability that a person is a bot. The model is a pilot demonstration artifact and is not production-ready for operational security enforcement.
                  </p>
                </div>
              )}

              {/* Session Metadata vs Actual ML Model Output Comparison */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Left Column: Risk Signals & Decision */}
                <div className="p-4 rounded-xl bg-surface-elevated/50 border border-border/80 space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-border/60">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
                      <BarChart2 className="w-3.5 h-3.5 text-cyber-cyan" />
                      <span>Cross-Layer Risk Signals</span>
                    </span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                        riskData.decision.action === 'BLOCK'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : riskData.decision.action === 'CHALLENGE'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      }`}
                    >
                      Policy: {riskData.decision.action}
                    </span>
                  </div>

                  <div className="space-y-2 text-xs font-mono">
                    <div className="flex justify-between items-center text-slate-300">
                      <span>Behavioral Integrity Score:</span>
                      <span className="text-sm font-bold text-white">
                        {riskData.behavioral_integrity_score.toFixed(3)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-slate-400">
                      <span>Browser Motor Anomaly Score:</span>
                      <span className="text-slate-200">{riskData.signals.browser_score.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between items-center text-slate-400">
                      <span>API Semantic Anomaly Score:</span>
                      <span className="text-slate-200">{riskData.signals.api_anomaly_score.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between items-center text-slate-400">
                      <span>Sequence Transition Anomaly:</span>
                      <span className="text-slate-200">{riskData.signals.sequence_score.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between items-center text-slate-400">
                      <span>Cross-Layer Discordance:</span>
                      <span className="text-cyber-cyan font-bold">{riskData.signals.cross_layer_discordance.toFixed(3)}</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-border/50 text-[11px] text-slate-400">
                    <span className="font-semibold text-slate-300">Score Meaning: </span>
                    <span>Consolidated multi-signal heuristic risk index [0.0 - 1.0]. Distinct from ML posterior probabilities.</span>
                  </div>
                </div>

                {/* Right Column: Model Inference Detail */}
                <div className="p-4 rounded-xl bg-surface-elevated/50 border border-border/80 space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-border/60">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
                      <Cpu className="w-3.5 h-3.5 text-primary-400" />
                      <span>{isSessionExpB ? 'Candidate Kinematic Inference (Exp B)' : 'Frozen XGBoost Inference (Exp A)'}</span>
                    </span>
                    {riskData.ml_inference && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-primary-500/10 text-primary-300 border border-primary-500/20">
                        {riskData.ml_inference.model_version || (isSessionExpB ? '1.0.0-candidate' : '3.4.1')}
                      </span>
                    )}
                  </div>

                  {riskData.ml_inference ? (
                    <div className="space-y-2 text-xs font-mono">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400">Predicted Class:</span>
                        <span
                          className={`px-2.5 py-0.5 rounded font-bold ${
                            riskData.ml_inference.predicted_class === 'AUTOMATED'
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                              : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          }`}
                        >
                          {riskData.ml_inference.predicted_class || 'N/A'} (Label: {riskData.ml_inference.predicted_label ?? '?'})
                        </span>
                      </div>

                      <div className="flex justify-between items-center text-slate-300">
                        <span className="text-slate-400">
                          {isSessionExpB
                            ? 'Kinematic Risk (Human):'
                            : 'Uncalibrated Score (Human):'}
                        </span>
                        <span className="text-emerald-400 font-bold">
                          {riskData.ml_inference.probability_human !== undefined
                            ? `${(riskData.ml_inference.probability_human * 100).toFixed(1)}%`
                            : 'N/A'}
                        </span>
                      </div>

                      <div className="flex justify-between items-center text-slate-300">
                        <span className="text-slate-400">
                          {isSessionExpB
                            ? 'Kinematic Risk (Auto):'
                            : 'Uncalibrated Score (Auto):'}
                        </span>
                        <span className="text-rose-400 font-bold">
                          {riskData.ml_inference.probability_automated !== undefined
                            ? `${(riskData.ml_inference.probability_automated * 100).toFixed(1)}%`
                            : 'N/A'}
                        </span>
                      </div>

                      <div className="flex justify-between items-center text-slate-400">
                        <span>Decision Threshold:</span>
                        <span className="text-slate-200">
                          {riskData.ml_inference.decision_threshold?.toFixed(2) || '0.50'}
                        </span>
                      </div>

                      <div className="flex justify-between items-center text-slate-400">
                        <span>Inference Subsystem:</span>
                        <span className="text-cyber-emerald capitalize">
                          {riskData.ml_inference.status}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-slate-400 py-3 text-center">
                      No ML inference evaluation available for this session.
                    </div>
                  )}

                  <div className="pt-2 border-t border-border/50 text-[11px] text-slate-400 flex items-start space-x-1.5">
                    <Info className="w-3.5 h-3.5 text-primary-400 shrink-0 mt-0.5" />
                    <span>
                      <strong>Distinction:</strong> Predicted class is computed strictly from the {isSessionExpB ? '12-feature kinematic vector' : '64-feature vector'}. It is reported separately from the intended test scenario.
                    </span>
                  </div>
                </div>
              </div>

              {/* STAGE 6.1 TASK 2: Model Explainability Breakdown */}
              <div className="p-4 rounded-xl bg-surface-elevated/40 border border-border/80 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-2 border-b border-border/60 gap-1">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-primary-400" />
                      <span>{isSessionExpB ? 'Feature Attributions & Explainability (Experiment B)' : 'Contributing Behavioral Features (SHAP Model Attributions)'}</span>
                    </span>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      {isSessionExpB
                        ? 'Tree SHAP feature attributions are unavailable for Experiment B to prevent cross-model explanation leakage.'
                        : 'SHAP values represent tree-split contributions to the model\'s log-odds score, not causal proof of user identity or intent.'}
                    </p>
                  </div>
                  {!isSessionExpB && explanationData && explanationData.ml_inference?.status === 'available' && (
                    <span className="text-[10px] font-mono text-slate-400 shrink-0">
                      Non-Zero Contributors: {nonzeroContribs.length}
                    </span>
                  )}
                </div>

                {/* State 1: Explanation not yet loaded */}
                {inspectLoading ? (
                  <div className="p-4 rounded-lg bg-surface/60 border border-border/50 text-slate-400 text-xs flex items-center space-x-2">
                    <Loader2 className="w-4 h-4 text-primary-400 animate-spin shrink-0" />
                    <span>Loading feature explanations...</span>
                  </div>
                ) : isSessionExpB ? (
                  /* Experiment B state: Tree SHAP suppressed */
                  <div className="p-3.5 rounded-lg bg-surface/60 border border-border/50 text-slate-300 text-xs flex items-center space-x-2">
                    <HelpCircle className="w-4 h-4 text-purple-400 shrink-0" />
                    <span>
                      Feature attribution explanations are not currently supported for Experiment B (Kinematic Classifier). Tree SHAP values are intentionally unavailable to prevent cross-model attribution leakage.
                    </span>
                  </div>
                ) : !explanationData || explanationData.ml_inference?.status !== 'available' ? (
                  /* State 2: Explanation unavailable or failed */
                  <div className="p-3.5 rounded-lg bg-surface/60 border border-border/50 text-slate-400 text-xs flex items-center space-x-2">
                    <HelpCircle className="w-4 h-4 text-slate-500 shrink-0" />
                    <span>
                      Explanation data is unavailable for this session.
                    </span>
                  </div>
                ) : nonzeroContribs.length > 0 ? (
                  /* State 3: Non-zero attribution available */
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {nonzeroContribs.map((feat, idx) => {
                      const isPositive = feat.shap_value >= 0;
                      return (
                        <div
                          key={idx}
                          className="p-3 rounded-lg bg-surface/80 border border-border/70 flex flex-col justify-between space-y-2"
                        >
                          <div className="flex items-start justify-between gap-1">
                            <span className="text-xs font-bold font-mono text-slate-200 truncate" title={feat.feature_name}>
                              {feat.feature_name}
                            </span>
                            <span
                              className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                                isPositive
                                  ? 'bg-rose-500/20 text-rose-300'
                                  : 'bg-emerald-500/20 text-emerald-300'
                              }`}
                            >
                              {isPositive ? '+' : ''}{feat.shap_value.toFixed(3)}
                            </span>
                          </div>

                          <div className="text-[11px] text-slate-400 font-mono">
                            <span>Value: </span>
                            <span className="text-slate-200 font-semibold">{feat.feature_value.toFixed(2)}</span>
                          </div>

                          <p className="text-[10px] text-slate-400 leading-tight">
                            {feat.description}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  /* State 4: Valid explanation with all-zero feature contributions */
                  <div className="p-3.5 rounded-lg bg-surface/60 border border-border/50 text-slate-400 text-xs flex items-center space-x-2">
                    <HelpCircle className="w-4 h-4 text-slate-500 shrink-0" />
                    <span>
                      No individual feature has a non-zero attribution for this prediction.
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })()}
      </div>

      {/* Subsystem & Foundation Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Architecture Components Card */}
        <div className="glass-panel p-6 rounded-xl">
          <h2 className="text-base font-semibold text-white mb-4 flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-primary-400" />
            <span>Subsystem Foundation Matrix</span>
          </h2>
          <div className="space-y-3">
            {health?.components ? (
              Object.entries(health.components).map(([key, val]) => (
                <div key={key} className="flex items-center justify-between p-3 rounded-lg bg-surface-elevated/50 border border-border/60">
                  <div className="flex items-center space-x-3">
                    <span className="w-2 h-2 rounded-full bg-cyber-emerald" />
                    <span className="font-mono text-xs text-slate-200 capitalize">
                      {key.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <span className="text-xs font-mono uppercase text-cyber-emerald px-2 py-0.5 rounded bg-cyber-emerald/10 border border-cyber-emerald/20">
                    {val}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-xs font-mono text-slate-400">Loading component health...</div>
            )}
          </div>
        </div>

        {/* Privacy & Research Guardrails */}
        <div className="glass-panel p-6 rounded-xl">
          <h2 className="text-base font-semibold text-white mb-4 flex items-center space-x-2">
            <Activity className="w-4 h-4 text-cyber-cyan" />
            <span>Privacy-Preserving Telemetry Design</span>
          </h2>
          <div className="space-y-3 text-xs text-slate-300">
            <div className="p-3 rounded-lg bg-surface-elevated/50 border border-border/60 flex items-start space-x-3">
              <span className="text-cyber-cyan font-bold font-mono">01</span>
              <div>
                <p className="font-medium text-slate-200">Zero Keystroke Content Capture</p>
                <p className="text-slate-400 mt-0.5">Captures only inter-key flight timing ($\Delta t$) and dwell duration. Character codes are discarded at listener invocation.</p>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-surface-elevated/50 border border-border/60 flex items-start space-x-3">
              <span className="text-cyber-cyan font-bold font-mono">02</span>
              <div>
                <p className="font-medium text-slate-200">Form Isolation</p>
                <p className="text-slate-400 mt-0.5">Form inputs, passwords, and user values are never read or transmitted by the Browser SDK.</p>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-surface-elevated/50 border border-border/60 flex items-start space-x-3">
              <span className="text-cyber-cyan font-bold font-mono">03</span>
              <div>
                <p className="font-medium text-slate-200">Continuous Behavioral Integrity Scoring</p>
                <p className="text-slate-400 mt-0.5">Continuous risk assessment $[0.0 - 1.0]$ with live SHAP explainability rather than binary hard-coded heuristics.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
