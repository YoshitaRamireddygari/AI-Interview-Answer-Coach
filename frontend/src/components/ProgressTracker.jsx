import React, { useState, useEffect } from 'react'
import {
  TrendingUp,
  Award,
  AlertCircle,
  BarChart3,
  Layers,
  CheckCircle2,
  PieChart,
  RefreshCw,
  HelpCircle,
  ArrowRight,
  Clock,
  Sparkles
} from 'lucide-react'

export function ProgressTracker({ backendUrl }) {
  const [overall, setOverall] = useState(null)
  const [history, setHistory] = useState(null)
  const [weaknesses, setWeaknesses] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchTrackerData = async () => {
    setLoading(true)
    setError(null)

    try {
      const [overallRes, historyRes, weaknessesRes] = await Promise.all([
        fetch(`${backendUrl}/api/progress/overall`),
        fetch(`${backendUrl}/api/progress/history`),
        fetch(`${backendUrl}/api/progress/weaknesses`)
      ])

      if (!overallRes.ok || !historyRes.ok || !weaknessesRes.ok) {
        throw new Error('Failed to load progress tracking statistics.')
      }

      const overallData = await overallRes.json()
      const historyData = await historyRes.json()
      const weaknessesData = await weaknessesRes.json()

      setOverall(overallData)
      setHistory(historyData)
      setWeaknesses(weaknessesData)
    } catch (err) {
      console.error('Fetch progress tracker error:', err)
      setError(err.message || 'Failed to fetch progress tracker statistics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTrackerData()
  }, [])

  if (loading) {
    return (
      <div className="card loading-card">
        <div className="loading-spinner-wrapper">
          <RefreshCw size={32} className="spin-slow spinner-icon" />
          <div className="pulse-ring" />
        </div>
        <h3 className="loading-title">Loading Progress & Weaknesses Dashboard...</h3>
        <p className="loading-subtitle">Aggregating database statistics and analyzing recurring feedback patterns.</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-alert">
        <AlertCircle size={20} />
        <span>{error}</span>
        <button onClick={fetchTrackerData}>Retry</button>
      </div>
    )
  }

  const {
    total_interviews_completed = 0,
    total_answers_analyzed = 0,
    average_overall_score = 0,
    average_overall_score_10 = 0,
    component_averages = {},
    category_averages = {}
  } = overall || {}

  return (
    <div className="tracker-dashboard-container">
      {/* Top Hero Stat Cards */}
      <div className="tracker-hero-grid">
        {/* Stat 1: Total Completed */}
        <div className="card stat-hero-card">
          <div className="stat-icon-badge bg-indigo">
            <Layers size={22} />
          </div>
          <div className="stat-content">
            <span className="stat-label">INTERVIEWS COMPLETED</span>
            <div className="stat-value-group">
              <span className="stat-number">{total_interviews_completed}</span>
              <span className="stat-sublabel">sessions ({total_answers_analyzed} answers analyzed)</span>
            </div>
          </div>
        </div>

        {/* Stat 2: Average Score */}
        <div className="card stat-hero-card">
          <div className="stat-icon-badge bg-green">
            <Award size={22} />
          </div>
          <div className="stat-content">
            <span className="stat-label">AVERAGE OVERALL SCORE</span>
            <div className="stat-value-group">
              <span className="stat-number">{average_overall_score_10}</span>
              <span className="stat-denom">/ 10</span>
              <span className="stat-percentage-chip">{average_overall_score}%</span>
            </div>
          </div>
        </div>

        {/* Stat 3: Top Improvement Need */}
        <div className="card stat-hero-card">
          <div className="stat-icon-badge bg-amber">
            <AlertCircle size={22} />
          </div>
          <div className="stat-content">
            <span className="stat-label">PRIMARY FOCUS AREA</span>
            <div className="stat-value-group">
              <span className="stat-focus-title">
                {weaknesses?.recurring_weaknesses?.[0]?.title || 'Structure & Impact'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Criteria Breakdown Grid */}
      <div className="card">
        <h3 className="dashboard-section-title">
          <BarChart3 size={20} className="icon-accent" />
          <span>Average Performance by Evaluation Criterion</span>
        </h3>

        <div className="criteria-averages-grid">
          {[
            { key: 'relevance', label: 'Relevance', val: component_averages.relevance || 0 },
            { key: 'completeness', label: 'Completeness', val: component_averages.completeness || 0 },
            { key: 'clarity', label: 'Clarity', val: component_averages.clarity || 0 },
            { key: 'structure', label: 'Structure', val: component_averages.structure || 0 },
            { key: 'technical_accuracy', label: 'Technical Accuracy', val: component_averages.technical_accuracy || 0 }
          ].map(comp => (
            <div key={comp.key} className="comp-stat-box">
              <div className="comp-stat-header">
                <span className="comp-name">{comp.label}</span>
                <span className="comp-val">{comp.val} / 10</span>
              </div>
              <div className="progress-track">
                <div 
                  className="progress-fill"
                  style={{ width: `${comp.val * 10}%`, backgroundColor: comp.val >= 8.0 ? '#10b981' : comp.val >= 7.0 ? '#6366f1' : '#f59e0b' }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Category Breakdown & Score History */}
      <div className="dashboard-grid grid-2-col">
        {/* Category Performance */}
        <div className="card">
          <h3 className="dashboard-section-title">
            <PieChart size={20} className="icon-accent" />
            <span>Category Averages</span>
          </h3>

          <div className="category-averages-list">
            {[
              { id: 'behavioral', label: 'Behavioral' },
              { id: 'technical', label: 'Technical' },
              { id: 'hr', label: 'HR' },
              { id: 'project', label: 'Project' }
            ].map(cat => {
              const score = category_averages[cat.id] || 0
              return (
                <div key={cat.id} className="category-avg-row">
                  <span className="cat-name">{cat.label}</span>
                  <div className="cat-bar-wrap">
                    <div className="progress-track">
                      <div 
                        className="progress-fill"
                        style={{ width: `${score}%`, backgroundColor: '#818cf8' }}
                      />
                    </div>
                  </div>
                  <span className="cat-score-text">{score}%</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Recent Score History Timeline */}
        <div className="card">
          <h3 className="dashboard-section-title">
            <Clock size={20} className="icon-accent" />
            <span>Score History Timeline</span>
          </h3>

          {history?.items && history.items.length > 0 ? (
            <div className="history-timeline-list">
              {history.items.slice(-5).reverse().map((item, idx) => (
                <div key={idx} className="timeline-item">
                  <div className="timeline-badge">{item.score_10}</div>
                  <div className="timeline-content">
                    <div className="timeline-question">{item.question}</div>
                    <div className="timeline-meta">
                      <span className="timeline-cat">{item.category.toUpperCase()}</span>
                      <span className="timeline-date">{new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-text">No interview sessions recorded yet. Start an interview to build score history.</p>
          )}
        </div>
      </div>

      {/* Recurring Improvement Categories */}
      <div className="card recurring-weaknesses-card">
        <h3 className="dashboard-section-title text-warning">
          <Sparkles size={20} />
          <span>Recurring Improvement Areas (Data-Driven Analysis)</span>
        </h3>

        <p className="weakness-intro">
          Identified automatically from empirical evaluation feedback recorded across past interview sessions.
        </p>

        <div className="weaknesses-list">
          {weaknesses?.recurring_weaknesses && weaknesses.recurring_weaknesses.length > 0 ? (
            weaknesses.recurring_weaknesses.map((weak, idx) => (
              <div key={idx} className="weakness-card">
                <div className="weakness-header">
                  <div className="weakness-title-wrap">
                    <span className="weakness-rank">#{idx + 1}</span>
                    <h4 className="weakness-title">{weak.title}</h4>
                  </div>
                  <span className="weakness-pct-badge">{weak.count} time(s) ({weak.percentage}%)</span>
                </div>

                <p className="weakness-desc">{weak.description}</p>

                {weak.example_feedback && weak.example_feedback.length > 0 && (
                  <div className="weakness-quotes-box">
                    <span className="quotes-label">Observed Feedback Snippets:</span>
                    <ul className="quotes-list">
                      {weak.example_feedback.map((quote, qIdx) => (
                        <li key={qIdx}>"{quote}"</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="actionable-tip-box">
                  <ArrowRight size={16} className="tip-icon" />
                  <div className="tip-text">
                    <strong>Actionable Tip:</strong> {weak.actionable_tip}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="empty-text">Complete more interview evaluations to reveal recurring improvement patterns.</p>
          )}
        </div>
      </div>
    </div>
  )
}
