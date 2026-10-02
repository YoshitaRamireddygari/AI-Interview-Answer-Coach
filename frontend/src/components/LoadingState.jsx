import React from 'react'
import { RefreshCw, Sparkles, ShieldCheck, Calculator } from 'lucide-react'

export function LoadingState() {
  return (
    <div className="card loading-card" role="status" aria-live="polite">
      <div className="loading-spinner-wrapper">
        <div className="pulse-ring"></div>
        <RefreshCw size={36} className="spin-slow spinner-icon" />
      </div>

      <h2 className="loading-title">Evaluating Your Interview Response</h2>
      <p className="loading-subtitle">
        Our Gemini AI pipeline is performing qualitative analysis and computing weighted evaluation criteria.
      </p>

      <div className="loading-steps">
        <div className="step-item active">
          <Sparkles size={16} />
          <span>Qualitative Criteria Assessment (Gemini AI)</span>
        </div>
        <div className="step-item active">
          <ShieldCheck size={16} />
          <span>Anti-hallucination Grounding & STAR Alignment</span>
        </div>
        <div className="step-item active">
          <Calculator size={16} />
          <span>Deterministic Weighted Scoring Engine</span>
        </div>
      </div>
    </div>
  )
}
