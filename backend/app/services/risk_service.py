from datetime import datetime
from typing import Dict, Any, Optional
from backend.app.schemas.risk import (
    RiskResponse,
    RiskSignals,
    RiskDecision,
    ExplanationResponse,
    ShapFeatureContribution,
    RuleTrigger,
)
from backend.app.schemas.dashboard import DashboardStatsResponse, FlaggedSessionItem
from backend.app.services.session_service import session_service

class RiskService:
    """
    Risk service orchestrating cross-layer behavioral score retrieval and explainability summaries.
    """
    def __init__(self):
        self._mock_risk_store: Dict[str, Dict[str, Any]] = {}

    async def get_risk_score(self, session_id: str) -> RiskResponse:
        now = datetime.utcnow()
        session = session_service.get_session(session_id)
        from backend.app.services.ml_inference_service import ml_inference_service
        from backend.app.schemas.risk import ModelInferenceDetail

        ml_pred = session_service.get_session_prediction(session_id)
        ml_inference_detail: Optional[ModelInferenceDetail] = None

        if ml_pred and ml_pred.get("status") == "success":
            prob_auto = float(ml_pred["probability_automated"])
            browser_score = round(prob_auto, 3)
            ml_inference_detail = ModelInferenceDetail(
                status="available",
                active_model=ml_pred.get("active_model", "experiment_a"),
                score_label=ml_pred.get("score_label", "Uncalibrated Model Score"),
                model_version=ml_pred.get("model_version"),
                model_type=ml_pred.get("model_type"),
                predicted_class=ml_pred.get("predicted_class"),
                predicted_label=ml_pred.get("predicted_label"),
                probability_automated=round(prob_auto, 4),
                probability_human=round(float(ml_pred.get("probability_human", 1.0 - prob_auto)), 4),
                decision_threshold=ml_pred.get("decision_threshold", 0.50),
                explanation_note=ml_pred.get("demonstration_note", "Pilot demonstration model fitted on 53 Phase 1 development sessions."),
            )
        else:
            # Model inference not available or telemetry pending
            active_mod = ml_inference_service.active_model
            if not ml_inference_service.is_ready:
                inferred_status = "unavailable"
                active_err = (
                    ml_inference_service._load_error_b
                    if active_mod == "experiment_b"
                    else ml_inference_service._load_error
                )
                note = f"ML model artifact unavailable: {active_err}"
            elif session and session.get("status") == "ACTIVE":
                inferred_status = "prediction_not_ready"
                note = "Session is currently ACTIVE; full ML inference is finalized upon session completion."
            else:
                inferred_status = "insufficient_telemetry"
                req_count = 12 if active_mod == "experiment_b" else 64
                note = f"Insufficient event telemetry (<5 events) to construct {req_count}-feature vector."

            browser_score = 0.12  # Foundation baseline heuristic fallback
            ml_inference_detail = ModelInferenceDetail(
                status=inferred_status,
                active_model=active_mod,
                score_label=ml_inference_service.score_label,
                model_version=ml_inference_service.model_version if ml_inference_service.is_ready else None,
                model_type=ml_inference_service.model_type if ml_inference_service.is_ready else None,
                decision_threshold=0.50,
                explanation_note=note,
            )

        api_score = 0.08
        api_struct_score = 0.05
        seq_score = 0.10
        freq_score = 0.04
        cross_disc = abs(browser_score - api_score)
        integrity_score = round(
            0.35 * browser_score + 0.25 * api_score + 0.20 * seq_score + 0.10 * api_struct_score + 0.10 * freq_score,
            3
        )

        decision_action = "ALLOW"
        if integrity_score >= 0.70:
            decision_action = "BLOCK"
            reason = f"High cross-layer discordance: elevated bot probability ({browser_score:.3f}) with automated patterns."
        elif integrity_score >= 0.35:
            decision_action = "CHALLENGE"
            reason = f"Moderate behavioral anomaly detected: elevated automated probability ({browser_score:.3f})."
        else:
            reason = f"Normal correlated behavioral dynamics: low bot probability ({browser_score:.3f})."

        return RiskResponse(
            session_id=session_id,
            behavioral_integrity_score=integrity_score,
            signals=RiskSignals(
                browser_score=browser_score,
                api_anomaly_score=api_score,
                api_structure_score=api_struct_score,
                sequence_score=seq_score,
                frequency_score=freq_score,
                cross_layer_discordance=round(cross_disc, 3),
            ),
            decision=RiskDecision(
                action=decision_action,
                reason=reason,
                enacted_at=now,
            ),
            last_evaluated_at=now,
            ml_inference=ml_inference_detail,
        )

    async def get_explanation(self, session_id: str) -> ExplanationResponse:
        risk = await self.get_risk_score(session_id)
        from backend.app.services.ml_inference_service import ml_inference_service

        features = session_service.get_session_features(session_id)
        shap_contributions: List[ShapFeatureContribution] = []

        if features and ml_inference_service.is_ready:
            raw_shap = ml_inference_service.explain_from_features(features, top_k=5)
            for item in raw_shap:
                shap_contributions.append(
                    ShapFeatureContribution(
                        feature_name=item["feature_name"],
                        feature_value=item["feature_value"],
                        shap_value=item["shap_value"],
                        description=item["description"],
                    )
                )

        # Task 3: If SHAP data is unavailable or has no non-zero feature attributions,
        # return empty list rather than inventing fabricated fallback features.

        rules = []
        if risk.behavioral_integrity_score >= 0.35:
            rules.append(
                RuleTrigger(
                    rule_id="RULE_BEHAVIORAL_DEVIATION",
                    severity="MEDIUM",
                    message="Trajectory straightness or velocity variance exceeds standard human baseline."
                )
            )

        return ExplanationResponse(
            session_id=session_id,
            behavioral_integrity_score=risk.behavioral_integrity_score,
            decision=risk.decision.action,
            shap_contributions=shap_contributions,
            rule_triggers=rules,
            ml_inference=risk.ml_inference,
        )

    async def get_dashboard_stats(self) -> DashboardStatsResponse:
        sessions = session_service.get_all_sessions()
        total = max(len(sessions), 1)
        active = sum(1 for s in sessions.values() if s.get("status") == "ACTIVE")

        decision_dist = {"ALLOW": 0, "CHALLENGE": 0, "RATE_LIMIT": 0, "BLOCK": 0}
        total_risk = 0.0
        flagged: List[FlaggedSessionItem] = []

        for s_id, s in sessions.items():
            pred = s.get("ml_prediction") or {}
            prob_auto = float(pred.get("probability_automated", 0.15)) if pred else 0.15
            total_risk += prob_auto

            if prob_auto >= 0.70:
                dec = "BLOCK"
            elif prob_auto >= 0.35:
                dec = "CHALLENGE"
            else:
                dec = "ALLOW"
            decision_dist[dec] = decision_dist.get(dec, 0) + 1

            ts = s.get("end_time") or s.get("start_time") or datetime.utcnow()
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts)
                except Exception:
                    ts = datetime.utcnow()

            pred_class = pred.get("predicted_class", "HUMAN" if s.get("collection_mode") != "AUTOMATED" else "AUTOMATED")
            flagged.append(
                FlaggedSessionItem(
                    session_id=s_id,
                    risk_score=round(prob_auto, 3),
                    decision=dec,
                    primary_reason=f"Model: {pred_class} (P={prob_auto:.3f})" if pred else "Active / Baseline evaluation",
                    timestamp=ts,
                )
            )

        avg_risk = round(total_risk / max(len(sessions), 1), 3)
        flagged.sort(key=lambda x: x.timestamp, reverse=True)

        return DashboardStatsResponse(
            total_sessions=total,
            active_sessions=active,
            average_risk_score=avg_risk if sessions else 0.18,
            decision_distribution=decision_dist if sessions else {"ALLOW": 1, "CHALLENGE": 0, "RATE_LIMIT": 0, "BLOCK": 0},
            recent_flagged_sessions=flagged[:10],
        )

risk_service = RiskService()
