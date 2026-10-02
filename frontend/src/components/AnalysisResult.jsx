import React, { useState } from 'react'
import { 
  Award, 
  CheckCircle2, 
  ArrowUpRight, 
  Sparkles, 
  Copy, 
  Check, 
  ChevronDown, 
  ChevronUp, 
  HelpCircle,
  FileText,
  PieChart
} from 'lucide-react'

export function AnalysisResult({ result }) {
  const [copied, setCopied] = useState(false)
  const [showWeights, setShowWeights] = useState(false)

  if (!result) return null

  const {
    question,
    user_answer,
    category,
    calculated_score,
    score_10,
    criteria_scores,
    strengths = [],
    improvements = [],
    improved_answer,
    weights_config,
    score_breakdown,
    status
  } = result

  // Calculate score rating badge
  const finalScore10 = score_10 || (calculated_score / 10.0)
  let scoreBadgeClass = 'badge-good'
  let scoreLabel = 'Solid Answer'

  if (finalScore10 >= 8.5) {
    scoreBadgeClass = 'badge-excellent'
    scoreLabel = 'Strong Answer'
  } else if (finalScore10 < 7.0) {
    scoreBadgeClass = 'badge-needs-work'
    scoreLabel = 'Needs Improvement'
  }

  const handleCopy = () => {
    if (improved_answer) {
      navigator.clipboard.writeText(improved_answer)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const getCriterionBarColor = (score) => {
    const val = score > 10 ? score : score * 10
    if (val >= 85) return '#10b981'
    if (val >= 70) return '#6366f1'
    return '#f59e0b'
  }

  return (
    <div className="analysis-result-container">
      {/* Overview Score Card */}
      <div className="card score-hero-card">
        <div className="score-hero-content">
          <div className="score-header">
            <span className="category-pill">{category.toUpperCase()}</span>
            <span className={`score-badge ${scoreBadgeClass}`}>{scoreLabel}</span>
          </div>

          <div className="score-display">
            <div className="score-circle">
              <span className="score-value">{finalScore10.toFixed(1)}</span>
              <span className="score-max">/ 10</span>
            </div>
            <div className="score-meta">
              <div className="percentage-tag">{calculated_score.toFixed(1)}% Score</div>
              <p className="score-desc">
                Calculated deterministically via weighted criteria engine.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Criteria Breakdown Grid */}
      <div className="card">
        <h3 className="section-title">
          <PieChart size={20} className="icon-accent" />
          <span>Evaluation Criteria Breakdown</span>
        </h3>

        <div className="criteria-grid">
          {criteria_scores && Object.entries(criteria_scores).map(([key, criterion]) => {
            const rawScore = criterion.score > 10 ? (criterion.score / 10).toFixed(1) : criterion.score.toFixed(1)
            const percent = criterion.score > 10 ? criterion.score : criterion.score * 10
            const barColor = getCriterionBarColor(percent)
            const formattedName = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())

            return (
              <div key={key} className="criterion-card">
                <div className="criterion-header">
                  <span className="criterion-name">{formattedName}</span>
                  <span className="criterion-score">{rawScore} / 10</span>
                </div>

                <div className="progress-bar-bg">
                  <div 
                    className="progress-bar-fill"
                    style={{ width: `${percent}%`, backgroundColor: barColor }}
                  />
                </div>

                <p className="criterion-feedback">{criterion.feedback}</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Strengths & Areas for Improvement */}
      <div className="insights-grid">
        {/* Strengths */}
        <div className="card insight-card strengths-card">
          <h3 className="insight-title text-success">
            <CheckCircle2 size={20} />
            <span>Key Strengths</span>
          </h3>
          <ul className="insight-list">
            {strengths.map((item, index) => (
              <li key={index} className="insight-item">
                <span className="bullet-icon success-bullet">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Improvements */}
        <div className="card insight-card improvements-card">
          <h3 className="insight-title text-warning">
            <ArrowUpRight size={20} />
            <span>Areas for Improvement</span>
          </h3>
          <ul className="insight-list">
            {improvements.map((item, index) => (
              <li key={index} className="insight-item">
                <span className="bullet-icon warning-bullet">→</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Improved Answer Card */}
      {improved_answer && (
        <div className="card improved-answer-card">
          <div className="improved-answer-header">
            <h3 className="section-title">
              <Sparkles size={20} className="icon-accent" />
              <span>Suggested Improved Answer</span>
            </h3>
            <button 
              type="button" 
              onClick={handleCopy} 
              className="btn btn-secondary btn-sm"
              title="Copy improved answer to clipboard"
            >
              {copied ? <Check size={16} color="#10b981" /> : <Copy size={16} />}
              <span>{copied ? 'Copied!' : 'Copy'}</span>
            </button>
          </div>

          <div className="improved-answer-box">
            <p>{improved_answer}</p>
          </div>

          <div className="grounding-note">
            <HelpCircle size={14} />
            <span>
              Grounded strictly in your original submission. Suggested additions are presented as bracketed placeholders.
            </span>
          </div>
        </div>
      )}

      {/* Scoring Weighting Configuration Accordion */}
      {weights_config && (
        <div className="card accordion-card">
          <button 
            type="button" 
            className="accordion-toggle"
            onClick={() => setShowWeights(!showWeights)}
          >
            <div className="accordion-title">
              <Award size={18} className="icon-accent" />
              <span>Deterministic Scoring Model Transparency</span>
            </div>
            {showWeights ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>

          {showWeights && (
            <div className="accordion-body">
              <p className="weights-intro">
                Our backend computes the final score deterministically in Python rather than relying on unvalidated LLM output.
              </p>
              <div className="weights-table-wrapper">
                <table className="weights-table">
                  <thead>
                    <tr>
                      <th>Criterion</th>
                      <th>Configured Weight</th>
                      <th>Weighted Contribution</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(weights_config).map(([comp, w]) => {
                      const contrib = score_breakdown ? score_breakdown[comp] : null
                      const formattedComp = comp.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                      return (
                        <tr key={comp}>
                          <td>{formattedComp}</td>
                          <td>{(w * 100).toFixed(0)}%</td>
                          <td>{contrib !== null ? `${contrib.toFixed(2)} pts` : '-'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
