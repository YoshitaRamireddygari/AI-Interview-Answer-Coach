import React, { useState } from 'react'
import { 
  Award, 
  CheckCircle2, 
  AlertTriangle, 
  HelpCircle, 
  Sparkles, 
  Copy, 
  Check, 
  RefreshCw, 
  PlusCircle, 
  Cpu, 
  PieChart,
  ArrowUpRight,
  ShieldAlert,
  Info
} from 'lucide-react'

export function Dashboard({ result, onRetry, onAnalyzeAnother, hideActionButtons = false }) {
  const [copied, setCopied] = useState(false)

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
    technical_warnings = [],
    missing_information = [],
    star_analysis,
    improved_answer,
    weights_config,
    score_breakdown
  } = result

  // Final score on 0-10 scale
  const finalScore10 = score_10 || (calculated_score / 10.0)

  // Status rating classification
  let scoreBadgeClass = 'badge-good'
  let scoreLabel = 'Solid Answer'

  if (finalScore10 >= 8.5) {
    scoreBadgeClass = 'badge-excellent'
    scoreLabel = 'Strong Answer'
  } else if (finalScore10 < 7.0) {
    scoreBadgeClass = 'badge-needs-work'
    scoreLabel = 'Needs Improvement'
  }

  const handleCopy = async () => {
    if (!improved_answer) return

    try {
      if (navigator && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
        await navigator.clipboard.writeText(improved_answer)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
        return
      }
    } catch (err) {
      console.warn('Clipboard API write failed, attempting fallback:', err)
    }

    try {
      const textarea = document.createElement('textarea')
      textarea.value = improved_answer
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      textarea.style.top = '-9999px'
      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()
      const successful = document.execCommand('copy')
      document.body.removeChild(textarea)
      if (successful) {
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }
    } catch (fallbackErr) {
      console.error('Clipboard copy fallback failed:', fallbackErr)
    }
  }

  const getBarColor = (scoreVal) => {
    const val = scoreVal > 10 ? scoreVal : scoreVal * 10
    if (val >= 85) return '#10b981' // Green
    if (val >= 70) return '#6366f1' // Indigo
    return '#f59e0b' // Amber
  }

  return (
    <div className="dashboard-container">
      {/* Top Action Toolbar */}
      {!hideActionButtons && (
        <div className="dashboard-toolbar">
          <button 
            type="button" 
            onClick={onAnalyzeAnother} 
            className="btn btn-secondary btn-sm"
          >
            <PlusCircle size={16} />
            <span>Analyze Another Answer</span>
          </button>

          <button 
            type="button" 
            onClick={onRetry} 
            className="btn btn-primary btn-sm"
          >
            <RefreshCw size={16} />
            <span>Retry Analysis</span>
          </button>
        </div>
      )}


      {/* OVERALL SCORE HERO CARD */}
      <div className="card score-hero-card">
        <div className="score-hero-header">
          <span className="category-pill">{category.toUpperCase()} INTERVIEW</span>
          <span className={`score-badge ${scoreBadgeClass}`}>{scoreLabel}</span>
        </div>

        <div className="score-hero-body">
          <div className="score-main-display">
            <span className="score-title">OVERALL SCORE</span>
            <div className="score-values">
              <span className="score-num-10">{finalScore10.toFixed(1)}</span>
              <span className="score-denom-10">/ 10</span>
              <span className="score-percentage-chip">{calculated_score.toFixed(1)}%</span>
            </div>
          </div>

          <div className="backend-engine-badge">
            <Cpu size={16} className="engine-icon" />
            <span>Calculated by Backend Scoring Engine</span>
          </div>
        </div>
      </div>

      {/* SPECIALIZED STAR FRAMEWORK ANALYSIS (DISPLAYED ONLY FOR BEHAVIORAL QUESTIONS) */}
      {category === 'behavioral' && star_analysis && (
        <div className="card star-framework-card">
          <h3 className="section-header text-indigo">
            <Sparkles size={20} />
            <span>STAR Framework Breakdown (Behavioral)</span>
          </h3>

          <p className="star-intro">
            Content analysis evaluating your narrative structure across Situation, Task, Action, and Result:
          </p>

          <div className="star-grid">
            {/* Situation */}
            <div className={`star-item-card ${star_analysis.situation?.present ? 'star-present' : 'star-missing'}`}>
              <div className="star-item-header">
                <div className="star-letter-badge">S</div>
                <div className="star-title-wrap">
                  <span className="star-item-title">Situation</span>
                  <span className="star-status-pill">
                    {star_analysis.situation?.present ? '✓ Present' : '✗ Missing'}
                  </span>
                </div>
              </div>
              <p className="star-feedback">{star_analysis.situation?.feedback}</p>
            </div>

            {/* Task */}
            <div className={`star-item-card ${star_analysis.task?.present ? 'star-present' : 'star-missing'}`}>
              <div className="star-item-header">
                <div className="star-letter-badge">T</div>
                <div className="star-title-wrap">
                  <span className="star-item-title">Task</span>
                  <span className="star-status-pill">
                    {star_analysis.task?.present ? '✓ Present' : '✗ Missing'}
                  </span>
                </div>
              </div>
              <p className="star-feedback">{star_analysis.task?.feedback}</p>
            </div>

            {/* Action */}
            <div className={`star-item-card ${star_analysis.action?.present ? 'star-present' : 'star-missing'}`}>
              <div className="star-item-header">
                <div className="star-letter-badge">A</div>
                <div className="star-title-wrap">
                  <span className="star-item-title">Action</span>
                  <span className="star-status-pill">
                    {star_analysis.action?.present ? '✓ Present' : '✗ Missing'}
                  </span>
                </div>
              </div>
              <p className="star-feedback">{star_analysis.action?.feedback}</p>
            </div>

            {/* Result */}
            <div className={`star-item-card ${star_analysis.result?.present ? 'star-present' : 'star-missing'}`}>
              <div className="star-item-header">
                <div className="star-letter-badge">R</div>
                <div className="star-title-wrap">
                  <span className="star-item-title">Result</span>
                  <span className="star-status-pill">
                    {star_analysis.result?.present ? '✓ Present' : '✗ Missing'}
                  </span>
                </div>
              </div>
              <p className="star-feedback">{star_analysis.result?.feedback}</p>
            </div>
          </div>

          {/* Summary Feedback */}
          {star_analysis.summary_feedback && (
            <div className="star-summary-box">
              <Info size={18} className="icon-accent" />
              <div className="star-summary-text">
                <strong>STAR Assessment Summary:</strong> {star_analysis.summary_feedback}
              </div>
            </div>
          )}
        </div>
      )}

      {/* INDIVIDUAL SCORES CATEGORY BREAKDOWN */}
      <div className="card">
        <h3 className="dashboard-section-title">
          <PieChart size={20} className="icon-accent" />
          <span>Evaluation Criteria Scores</span>
        </h3>

        <div className="criteria-scores-list">
          {criteria_scores && Object.entries(criteria_scores).map(([key, criterion]) => {
            const rawScore10 = criterion.score > 10 ? (criterion.score / 10).toFixed(1) : criterion.score.toFixed(1)
            const percentVal = criterion.score > 10 ? criterion.score : criterion.score * 10
            const barColor = getBarColor(percentVal)
            const displayName = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())

            return (
              <div key={key} className="criteria-item-card">
                <div className="criteria-item-header">
                  <span className="criteria-item-name">{displayName}</span>
                  <span className="criteria-item-score">{rawScore10} / 10</span>
                </div>

                {/* Visual Progress Indicator */}
                <div className="progress-track">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${percentVal}%`, backgroundColor: barColor }} 
                    role="progressbar"
                    aria-valuenow={percentVal}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`${displayName} score ${rawScore10} out of 10`}
                  />
                </div>

                {/* Short Explanation */}
                <p className="criteria-explanation">{criterion.feedback}</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* SECTION 1: WHAT YOU DID WELL */}
      <div className="card section-card section-well">
        <h3 className="section-header text-success">
          <CheckCircle2 size={20} />
          <span>1. What You Did Well</span>
        </h3>
        {strengths.length > 0 ? (
          <ul className="dashboard-list">
            {strengths.map((item, idx) => (
              <li key={idx} className="dashboard-list-item">
                <span className="bullet success-bullet">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty-text">No specific strengths highlighted.</p>
        )}
      </div>

      {/* SECTION 2: WHAT CAN BE IMPROVED */}
      <div className="card section-card section-improved">
        <h3 className="section-header text-warning">
          <ArrowUpRight size={20} />
          <span>2. What Can Be Improved</span>
        </h3>
        {improvements.length > 0 ? (
          <ul className="dashboard-list">
            {improvements.map((item, idx) => (
              <li key={idx} className="dashboard-list-item">
                <span className="bullet warning-bullet">→</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty-text">No specific improvement areas identified.</p>
        )}
      </div>

      {/* SECTION 3: TECHNICAL WARNINGS & ACCURACY VERIFICATION */}
      <div className="card section-card section-warnings">
        <h3 className="section-header text-danger">
          <ShieldAlert size={20} />
          <span>3. Technical Warnings & Claim Verification</span>
        </h3>
        
        {/* Verification Report Claims List */}
        {result.technical_verification && result.technical_verification.claims && result.technical_verification.claims.length > 0 && (
          <div className="claims-verification-list">
            <span className="claims-list-title">Extracted Technical Claims Verification:</span>
            <div className="claims-grid">
              {result.technical_verification.claims.map((claim, cIdx) => {
                let badgeClass = 'status-likely-correct'
                if (claim.status === 'Potential issue') badgeClass = 'status-potential-issue'
                if (claim.status === 'Needs verification') badgeClass = 'status-needs-verification'

                return (
                  <div key={cIdx} className={`claim-card ${badgeClass}`}>
                    <div className="claim-card-header">
                      <span className="claim-text-quote">"{claim.claim_text}"</span>
                      <span className={`claim-status-pill ${badgeClass}`}>{claim.status}</span>
                    </div>
                    <p className="claim-explanation">{claim.explanation}</p>
                    {claim.source_reference && (
                      <span className="claim-ref-tag">Rule: {claim.source_reference}</span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {technical_warnings && technical_warnings.length > 0 ? (
          <ul className="dashboard-list">
            {technical_warnings.map((item, idx) => (
              <li key={idx} className="dashboard-list-item warning-alert-item">
                <AlertTriangle size={16} className="danger-icon" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="clean-status-text">✓ No critical technical inaccuracies detected in your response.</p>
        )}

        {/* Fact Checking Disclaimer */}
        {result.technical_verification && (
          <div className="disclaimer-box">
            <Info size={16} />
            <span>{result.technical_verification.limitations_disclaimer}</span>
          </div>
        )}
      </div>


      {/* SECTION 4: MISSING INFORMATION */}
      <div className="card section-card section-missing">
        <h3 className="section-header text-info">
          <Info size={20} />
          <span>4. Missing Information</span>
        </h3>
        {missing_information && missing_information.length > 0 ? (
          <ul className="dashboard-list">
            {missing_information.map((item, idx) => (
              <li key={idx} className="dashboard-list-item">
                <span className="bullet info-bullet">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty-text">Answer contains all necessary key context and details.</p>
        )}
      </div>

      {/* SECTION 5: IMPROVED ANSWER */}
      {improved_answer && (
        <div className="card section-card section-answer">
          <div className="improved-answer-top">
            <h3 className="section-header text-indigo">
              <Sparkles size={20} />
              <span>5. Improved Answer</span>
            </h3>
            <button 
              type="button" 
              onClick={handleCopy} 
              className="btn btn-secondary btn-sm"
            >
              {copied ? <Check size={16} color="#10b981" /> : <Copy size={16} />}
              <span>{copied ? 'Copied!' : 'Copy Improved Answer'}</span>
            </button>
          </div>

          <div className="improved-text-container">
            <p>{improved_answer}</p>
          </div>

          <div className="grounding-disclaimer">
            <HelpCircle size={14} />
            <span>
              Grounded strictly in your stated experience. Suggested additions appear as optional placeholders (e.g. [Insert metric]).
            </span>
          </div>
        </div>
      )}

      {/* SCORING METHOD (BACKEND ENGINE TRANSPARENCY) */}
      <div className="card scoring-method-card">
        <h3 className="dashboard-section-title">
          <Award size={20} className="icon-accent" />
          <span>Scoring Method (Backend Engine)</span>
        </h3>

        <p className="scoring-method-desc">
          To eliminate LLM arithmetic inaccuracies, component scores are evaluated by AI but the <strong>final overall score is calculated deterministically by our Python backend scoring engine</strong> using weighted criteria:
        </p>

        <div className="weights-grid">
          <div className="weight-badge-item">
            <span className="weight-name">Relevance</span>
            <span className="weight-val">25%</span>
          </div>
          <div className="weight-badge-item">
            <span className="weight-name">Completeness</span>
            <span className="weight-val">20%</span>
          </div>
          <div className="weight-badge-item">
            <span className="weight-name">Clarity</span>
            <span className="weight-val">20%</span>
          </div>
          <div className="weight-badge-item">
            <span className="weight-name">Structure</span>
            <span className="weight-val">15%</span>
          </div>
          <div className="weight-badge-item">
            <span className="weight-name">Technical Accuracy</span>
            <span className="weight-val">20%</span>
          </div>
        </div>

        <div className="formula-box">
          <code>
            Weighted Score = (Relevance × 0.25) + (Completeness × 0.20) + (Clarity × 0.20) + (Structure × 0.15) + (Technical Accuracy × 0.20)
          </code>
        </div>
      </div>

      {/* Bottom Actions */}
      {!hideActionButtons && (
        <div className="bottom-actions">
          <button 
            type="button" 
            onClick={onRetry} 
            className="btn btn-secondary btn-large"
          >
            <RefreshCw size={18} />
            <span>Retry Current Analysis</span>
          </button>

          <button 
            type="button" 
            onClick={onAnalyzeAnother} 
            className="btn btn-primary btn-large"
          >
            <PlusCircle size={18} />
            <span>Analyze Another Answer</span>
          </button>
        </div>
      )}
    </div>

  )
}
